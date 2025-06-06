import google.generativeai as genai
import time
import random
import os
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from models import Video, Comment, get_db_session

class GeminiCommentRanker:
    """Система ранжирования комментариев с использованием Google Gemini API"""
    
    def __init__(self, api_key: str = None, use_fallback: bool = True):
        # Настройка API ключа
        if api_key:
            genai.configure(api_key=api_key)
        elif os.getenv('GEMINI_API_KEY'):
            genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
        else:
            raise ValueError("Необходимо указать GEMINI_API_KEY")
        
        # Инициализация модели
        self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
        self.batch_size = 10  # Gemini быстрее, можем увеличить размер батча
        self.use_fallback = use_fallback
        self.max_retries = 3
        
        # Настройки генерации
        self.generation_config = genai.types.GenerationConfig(
            temperature=0.1,  # Низкая температура для стабильности
            max_output_tokens=50,  # Короткий ответ
            top_p=0.8,
            top_k=40
        )
        
    def rank_comments_for_video(self, video_id: int) -> bool:
        """
        Ранжирует все комментарии для указанного видео
        
        Args:
            video_id: ID видео в базе данных
            
        Returns:
            bool: True если ранжирование прошло успешно
        """
        session = get_db_session()
        try:
            # Получаем видео и его summary
            video = session.query(Video).filter_by(id=video_id).first()
            if not video:
                print(f"❌ Видео с ID {video_id} не найдено")
                return False
                
            if not video.summary:
                print(f"❌ У видео {video_id} нет summary для ранжирования")
                return False
                
            # Получаем комментарии без ранга
            comments = session.query(Comment).filter_by(
                video_id=video_id, 
                comment_rank=None
            ).all()
            
            if not comments:
                print(f"✅ Все комментарии для видео {video_id} уже проранжированы")
                return True
                
            print(f"🔄 Начинаю ранжирование {len(comments)} комментариев для видео {video_id}")
            print(f"🤖 Используется: Google Gemini 2.0 Flash (контекст: ~1M токенов)")
            
            # Проверяем доступность Gemini API
            gemini_available = self._check_gemini_availability()
            if not gemini_available and self.use_fallback:
                print("⚠️ Gemini API недоступен, переключаюсь на эвристический алгоритм")
                return self._fallback_rank_all_comments(comments, video.summary, session)
            elif not gemini_available:
                print("❌ Gemini API недоступен и fallback отключен")
                return False
            
            # Пробуем обработать ВСЕ комментарии одним запросом
            success = self._rank_all_comments_single_request(comments, video.summary, session)
            
            if success:
                session.commit()
                print(f"✅ Ранжирование завершено для видео {video_id}")
                return True
            else:
                print("⚠️ Не удалось обработать все комментарии одним запросом, переключаюсь на батчи")
                # Fallback к батчевой обработке
                return self._rank_comments_in_batches(comments, video.summary, session)
                
        except Exception as e:
            print(f"❌ Ошибка при ранжировании комментариев: {e}")
            session.rollback()
            return False
        finally:
            session.close()
    
    def _check_gemini_availability(self) -> bool:
        """Проверяет доступность Gemini API"""
        try:
            print("🔍 Проверяю доступность Gemini API...")
            # Простой тестовый запрос
            response = self.model.generate_content(
                "Ответь одним словом: тест",
                generation_config=self.generation_config
            )
            
            if response and response.text:
                print(f"✅ Gemini API доступен. Тестовый ответ: {response.text.strip()}")
                return True
            else:
                print("❌ Gemini API не отвечает")
                return False
                
        except Exception as e:
            print(f"❌ Ошибка при проверке Gemini API: {e}")
            return False
    
    def _process_batch(self, comments: List[Comment], video_summary: str, session: Session, gemini_available: bool) -> int:
        """Обрабатывает батч комментариев"""
        successful_ranks = 0
        
        if gemini_available:
            # Пробуем обработать весь батч одним запросом для эффективности
            try:
                ranks = self._rank_batch_gemini(comments, video_summary)
                if ranks and len(ranks) == len(comments):
                    for comment, rank in zip(comments, ranks):
                        if rank is not None:
                            comment.comment_rank = rank
                            successful_ranks += 1
                            print(f"📊 Комментарий ID {comment.id}: ранг {rank:.3f} (Gemini)")
                        else:
                            print(f"⚠️ Не удалось проранжировать комментарий ID {comment.id}")
                    return successful_ranks
            except Exception as e:
                print(f"⚠️ Ошибка батчевой обработки: {e}, переключаюсь на индивидуальную")
        
        # Fallback: обрабатываем комментарии по одному
        for comment in comments:
            try:
                if gemini_available:
                    rank = self._rank_single_comment_gemini(comment.text, video_summary)
                else:
                    rank = self._rank_single_comment_fallback(comment.text, video_summary)
                    
                if rank is not None:
                    comment.comment_rank = rank
                    successful_ranks += 1
                    method = "Gemini" if gemini_available else "эвристика"
                    print(f"📊 Комментарий ID {comment.id}: ранг {rank:.3f} ({method})")
                else:
                    print(f"⚠️ Не удалось проранжировать комментарий ID {comment.id}")
                    
            except Exception as e:
                print(f"❌ Ошибка при обработке комментария ID {comment.id}: {e}")
        
        return successful_ranks
    
    def _rank_batch_gemini(self, comments: List[Comment], video_summary: str) -> Optional[List[float]]:
        """Ранжирует батч комментариев одним запросом к Gemini"""
        try:
            # Создаем промпт для батчевой обработки
            prompt = self._create_batch_ranking_prompt(comments, video_summary)
            
            for attempt in range(self.max_retries):
                try:
                    response = self.model.generate_content(
                        prompt,
                        generation_config=self.generation_config
                    )
                    
                    if response and response.text:
                        ranks = self._extract_batch_ranks_from_response(response.text, len(comments))
                        if ranks:
                            return ranks
                    
                except Exception as e:
                    print(f"⚠️ Попытка {attempt + 1}/{self.max_retries} не удалась: {e}")
                    if attempt < self.max_retries - 1:
                        time.sleep(1)
            
            return None
            
        except Exception as e:
            print(f"❌ Ошибка батчевого ранжирования: {e}")
            return None
    
    def _rank_single_comment_gemini(self, comment_text: str, video_summary: str) -> Optional[float]:
        """Ранжирует один комментарий с помощью Gemini"""
        prompt = self._create_ranking_prompt(comment_text, video_summary)
        
        for attempt in range(self.max_retries):
            try:
                response = self.model.generate_content(
                    prompt,
                    generation_config=self.generation_config
                )
                
                if response and response.text:
                    rank = self._extract_rank_from_response(response.text)
                    if rank is not None:
                        return rank
                        
            except Exception as e:
                print(f"⚠️ Попытка {attempt + 1}/{self.max_retries}: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(1)
        
        # Если Gemini не сработал, используем fallback
        if self.use_fallback:
            return self._rank_single_comment_fallback(comment_text, video_summary)
        
        return None
    
    def _rank_single_comment_fallback(self, comment_text: str, video_summary: str) -> float:
        """Ранжирует комментарий с помощью эвристического алгоритма"""
        rank = 0.5  # базовый ранг
        
        # Длинные комментарии обычно более информативны
        if len(comment_text) > 100:
            rank += 0.2
        elif len(comment_text) < 20:
            rank -= 0.2
            
        # Комментарии с вопросами могут быть более информативными
        if '?' in comment_text:
            rank += 0.1
            
        # Комментарии только с эмодзи менее информативны
        if len(comment_text.strip()) < 10 and any(ord(char) > 127 for char in comment_text):
            rank -= 0.3
            
        # Комментарии с ключевыми словами более релевантны
        keywords = ['рецепт', 'ингредиент', 'приготовление', 'вкус', 'температура', 'время', 'как', 'почему', 'что']
        for keyword in keywords:
            if keyword.lower() in comment_text.lower():
                rank += 0.15
                break
                
        # Добавляем немного случайности
        rank += random.uniform(-0.1, 0.1)
        
        return max(0.0, min(1.0, rank))
    
    def _create_ranking_prompt(self, comment_text: str, video_summary: str) -> str:
        """Создает промпт для ранжирования одного комментария"""
        return f"""Rate the informativeness of this comment relative to the video content on a scale from 0.0 to 1.0.

Video content: {video_summary}

Comment: {comment_text}

Rating criteria:
- 1.0: Comment adds significant value, complements or clarifies video content
- 0.7-0.9: Comment is relevant and contains useful information
- 0.4-0.6: Comment is partially related to video topic
- 0.1-0.3: Comment is weakly related to content
- 0.0: Comment is unrelated to video (spam, off-topic, emotions without content)

Respond with only a number from 0.0 to 1.0:"""
    
    def _create_batch_ranking_prompt(self, comments: List[Comment], video_summary: str) -> str:
        """Создает промпт для батчевого ранжирования"""
        comments_text = ""
        for i, comment in enumerate(comments, 1):
            comments_text += f"{i}. {comment.text}\n"
        
        return f"""Rate the informativeness of these comments relative to the video content on a scale from 0.0 to 1.0.

Video content: {video_summary}

Comments:
{comments_text}

Rating criteria:
- 1.0: Comment adds significant value, complements or clarifies video content
- 0.7-0.9: Comment is relevant and contains useful information
- 0.4-0.6: Comment is partially related to video topic
- 0.1-0.3: Comment is weakly related to content
- 0.0: Comment is unrelated to video (spam, off-topic, emotions without content)

Respond with only the ratings separated by commas (e.g., 0.8, 0.3, 0.9, 0.1):"""
    
    def _extract_rank_from_response(self, response: str) -> Optional[float]:
        """Извлекает числовую оценку из ответа Gemini"""
        try:
            import re
            # Ищем число от 0.0 до 1.0
            pattern = r'([0-1]\.?\d*)'
            matches = re.findall(pattern, response)
            
            if matches:
                rank = float(matches[0])
                return max(0.0, min(1.0, rank))
            
            return None
            
        except (ValueError, IndexError):
            return None
    
    def _extract_batch_ranks_from_response(self, response: str, expected_count: int) -> Optional[List[float]]:
        """Извлекает список оценок из батчевого ответа"""
        try:
            import re
            # Ищем числа, разделенные запятыми
            pattern = r'([0-1]\.?\d*)'
            matches = re.findall(pattern, response)
            
            if len(matches) == expected_count:
                ranks = []
                for match in matches:
                    rank = float(match)
                    ranks.append(max(0.0, min(1.0, rank)))
                return ranks
            
            return None
            
        except (ValueError, IndexError):
            return None
    
    def get_ranked_comments(self, video_id: int, min_rank: float = 0.0) -> List[Dict]:
        """Получает проранжированные комментарии для видео"""
        session = get_db_session()
        try:
            comments = session.query(Comment).filter(
                Comment.video_id == video_id,
                Comment.comment_rank.isnot(None),
                Comment.comment_rank >= min_rank
            ).order_by(Comment.comment_rank.desc()).all()
            
            result = []
            for comment in comments:
                result.append({
                    'id': comment.id,
                    'author': comment.author,
                    'text': comment.text,
                    'likes': comment.likes,
                    'rank': comment.comment_rank,
                    'published_at': comment.published_at.isoformat() if comment.published_at else None
                })
            
            return result
            
        finally:
            session.close()
    
    def _rank_all_comments_single_request(self, comments: List[Comment], video_summary: str, session: Session) -> bool:
        """Ранжирует ВСЕ комментарии одним запросом к Gemini"""
        try:
            print(f"📡 Отправляю все {len(comments)} комментариев одним запросом...")
            
            # Создаем мега-промпт для всех комментариев
            prompt = self._create_mega_ranking_prompt(comments, video_summary)
            
            # Увеличиваем лимиты для большого запроса
            mega_config = genai.types.GenerationConfig(
                temperature=0.1,
                max_output_tokens=2000,  # Больше токенов для ответа
                top_p=0.8,
                top_k=40
            )
            
            start_time = time.time()
            
            for attempt in range(self.max_retries):
                try:
                    print(f"🔄 Попытка {attempt + 1}/{self.max_retries}...")
                    
                    response = self.model.generate_content(
                        prompt,
                        generation_config=mega_config
                    )
                    
                    if response and response.text:
                        elapsed = time.time() - start_time
                        print(f"⚡ Получен ответ за {elapsed:.1f} секунд")
                        
                        ranks = self._extract_mega_ranks_from_response(response.text, len(comments))
                        if ranks and len(ranks) == len(comments):
                            # Применяем ранги к комментариям
                            successful_ranks = 0
                            for comment, rank in zip(comments, ranks):
                                if rank is not None:
                                    comment.comment_rank = rank
                                    successful_ranks += 1
                                    print(f"📊 ID {comment.id}: {rank:.3f}")
                            
                            print(f"✅ Успешно проранжировано: {successful_ranks}/{len(comments)} комментариев")
                            return True
                        else:
                            print(f"⚠️ Получено {len(ranks) if ranks else 0} рангов, ожидалось {len(comments)}")
                    
                except Exception as e:
                    print(f"❌ Попытка {attempt + 1} не удалась: {e}")
                    if attempt < self.max_retries - 1:
                        time.sleep(2)
            
            return False
            
        except Exception as e:
            print(f"❌ Ошибка мега-ранжирования: {e}")
            return False
    
    def _create_mega_ranking_prompt(self, comments: List[Comment], video_summary: str) -> str:
        """Создает мега-промпт для ранжирования всех комментариев"""
        comments_text = ""
        for i, comment in enumerate(comments, 1):
            # Ограничиваем длину каждого комментария для экономии токенов
            comment_preview = comment.text[:500] + "..." if len(comment.text) > 500 else comment.text
            comments_text += f"{i}. {comment_preview}\n"
        
        return f"""Rate the informativeness of ALL these comments relative to the video content on a scale from 0.0 to 1.0.

Video content: {video_summary}

Comments ({len(comments)} total):
{comments_text}

Rating criteria:
- 1.0: Comment adds significant value, complements or clarifies video content
- 0.7-0.9: Comment is relevant and contains useful information  
- 0.4-0.6: Comment is partially related to video topic
- 0.1-0.3: Comment is weakly related to content
- 0.0: Comment is unrelated to video (spam, off-topic, emotions without content)

IMPORTANT: Respond with EXACTLY {len(comments)} ratings separated by commas, one for each comment in order.
Example format: 0.8, 0.3, 0.9, 0.1, 0.7, 0.2, ...

Ratings:"""
    
    def _extract_mega_ranks_from_response(self, response: str, expected_count: int) -> Optional[List[float]]:
        """Извлекает список оценок из мега-ответа"""
        try:
            import re
            
            # Ищем строку с рейтингами (может быть в разных форматах)
            lines = response.strip().split('\n')
            ratings_line = None
            
            for line in lines:
                # Ищем строку с множественными числами через запятую
                if ',' in line and re.search(r'[0-1]\.\d+', line):
                    ratings_line = line
                    break
            
            if not ratings_line:
                # Если не нашли строку с запятыми, ищем все числа в тексте
                ratings_line = response
            
            # Извлекаем все числа от 0.0 до 1.0
            pattern = r'([0-1]\.?\d*)'
            matches = re.findall(pattern, ratings_line)
            
            if len(matches) >= expected_count:
                ranks = []
                for i in range(expected_count):
                    try:
                        rank = float(matches[i])
                        ranks.append(max(0.0, min(1.0, rank)))
                    except (ValueError, IndexError):
                        ranks.append(0.5)  # Дефолтный ранг при ошибке
                return ranks
            else:
                print(f"⚠️ Найдено только {len(matches)} рангов из {expected_count}")
                return None
            
        except Exception as e:
            print(f"❌ Ошибка извлечения мега-рангов: {e}")
            return None
    
    def _rank_comments_in_batches(self, comments: List[Comment], video_summary: str, session: Session) -> bool:
        """Fallback: ранжирование батчами при неудаче мега-запроса"""
        print("🔄 Переключаюсь на батчевую обработку...")
        
        successful_ranks = 0
        for i in range(0, len(comments), self.batch_size):
            batch = comments[i:i + self.batch_size]
            batch_success = self._process_batch(batch, video_summary, session, True)
            successful_ranks += batch_success
            time.sleep(0.5)  # Пауза между батчами
            
        session.commit()
        print(f"✅ Батчевое ранжирование завершено: {successful_ranks}/{len(comments)}")
        return successful_ranks > 0
    
    def _fallback_rank_all_comments(self, comments: List[Comment], video_summary: str, session: Session) -> bool:
        """Fallback: эвристическое ранжирование всех комментариев"""
        print("🔄 Использую эвристический алгоритм для всех комментариев...")
        
        successful_ranks = 0
        for comment in comments:
            try:
                rank = self._rank_single_comment_fallback(comment.text, video_summary)
                comment.comment_rank = rank
                successful_ranks += 1
                print(f"📊 ID {comment.id}: {rank:.3f} (эвристика)")
            except Exception as e:
                print(f"❌ Ошибка при обработке комментария ID {comment.id}: {e}")
        
        session.commit()
        print(f"✅ Эвристическое ранжирование завершено: {successful_ranks}/{len(comments)}")
        return successful_ranks > 0


def main():
    """Основная функция для тестирования ранжирования с Gemini"""
    import sys
    
    if len(sys.argv) < 2:
        print("Использование: python gemini_ranker.py <video_id> [--no-fallback] [--api-key=KEY]")
        return
    
    try:
        video_id = int(sys.argv[1])
        use_fallback = "--no-fallback" not in sys.argv
        
        # Извлекаем API ключ из аргументов
        api_key = None
        for arg in sys.argv:
            if arg.startswith("--api-key="):
                api_key = arg.split("=", 1)[1]
                break
        
        ranker = GeminiCommentRanker(api_key=api_key, use_fallback=use_fallback)
        
        print(f"🚀 Запуск ранжирования комментариев для видео ID: {video_id}")
        print(f"🤖 Модель: Google Gemini 2.0 Flash")
        if use_fallback:
            print("🔄 Режим: Gemini с fallback на эвристику")
        else:
            print("🔄 Режим: только Gemini")
            
        success = ranker.rank_comments_for_video(video_id)
        
        if success:
            print("\n📊 Топ-10 проранжированных комментариев:")
            ranked_comments = ranker.get_ranked_comments(video_id, min_rank=0.5)
            
            for i, comment in enumerate(ranked_comments[:10], 1):
                print(f"\n{i}. Ранг: {comment['rank']:.3f}")
                print(f"   Автор: {comment['author']}")
                print(f"   Лайки: {comment['likes']}")
                print(f"   Текст: {comment['text'][:100]}...")
        
    except ValueError:
        print("❌ Неверный формат video_id. Должно быть число.")
    except Exception as e:
        print(f"❌ Ошибка: {e}")


if __name__ == "__main__":
    main() 