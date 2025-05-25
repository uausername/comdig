import requests
import json
import time
import random
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from models import Video, Comment, get_db_session

class CommentRanker:
    """Система ранжирования комментариев по информативности (только эвристический алгоритм)"""
    
    def __init__(self, use_fallback: bool = True):
        self.batch_size = 5  # Размер батча для обработки
        self.use_fallback = use_fallback  # Использовать fallback при ошибках LLM
    
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
            
            # Используем только эвристический алгоритм
            print("📊 Использую эвристический алгоритм ранжирования")
            
            # Обрабатываем комментарии батчами
            successful_ranks = 0
            for i in range(0, len(comments), self.batch_size):
                batch = comments[i:i + self.batch_size]
                batch_success = self._process_batch(batch, video.summary, session)
                successful_ranks += batch_success
                
                # Небольшая пауза между батчами
                time.sleep(1)
                
            session.commit()
            print(f"✅ Ранжирование завершено для видео {video_id}")
            print(f"📊 Успешно проранжировано: {successful_ranks}/{len(comments)} комментариев")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка при ранжировании комментариев: {e}")
            session.rollback()
            return False
        finally:
            session.close()
    
    def _process_batch(self, comments: List[Comment], video_summary: str, session: Session) -> int:
        """Обрабатывает батч комментариев"""
        successful_ranks = 0
        for comment in comments:
            try:
                rank = self._rank_single_comment_fallback(comment.text, video_summary)
                    
                if rank is not None:
                    comment.comment_rank = rank
                    successful_ranks += 1
                    print(f"📊 Комментарий ID {comment.id}: ранг {rank:.3f}")
                else:
                    print(f"⚠️ Не удалось проранжировать комментарий ID {comment.id}")
                    
            except Exception as e:
                print(f"❌ Ошибка при обработке комментария ID {comment.id}: {e}")
        
        return successful_ranks
    
    def _rank_single_comment_fallback(self, comment_text: str, video_summary: str) -> float:
        """
        Ранжирует комментарий с помощью эвристического алгоритма
        """
        # Простые эвристики для демонстрации
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
        
        # Ограничиваем диапазон
        return max(0.0, min(1.0, rank))
    
    def _create_ranking_prompt(self, comment_text: str, video_summary: str) -> str:
        """Создает промпт для ранжирования комментария"""
        return f"""Оцени информативность комментария относительно содержания видео по шкале от 0.0 до 1.0.

Содержание видео: {video_summary}

Комментарий: {comment_text}

Критерии оценки:
- 1.0: Комментарий добавляет значительную ценность, дополняет или уточняет содержание видео
- 0.7-0.9: Комментарий релевантен и содержит полезную информацию
- 0.4-0.6: Комментарий частично связан с темой видео
- 0.1-0.3: Комментарий слабо связан с содержанием
- 0.0: Комментарий не связан с видео (спам, оффтоп, эмоции без содержания)

Ответь только числом от 0.0 до 1.0: """
    
    def _extract_rank_from_response(self, response: str) -> Optional[float]:
        """Извлекает числовую оценку из ответа LLM"""
        try:
            # Ищем число от 0.0 до 1.0 в ответе
            import re
            
            # Паттерн для поиска числа от 0.0 до 1.0
            pattern = r'([0-1]\.?\d*)'
            matches = re.findall(pattern, response)
            
            if matches:
                rank = float(matches[0])
                # Убеждаемся что ранг в допустимых пределах
                return max(0.0, min(1.0, rank))
            
            return None
            
        except (ValueError, IndexError):
            return None
    
    def get_ranked_comments(self, video_id: int, min_rank: float = 0.0) -> List[Dict]:
        """
        Получает проранжированные комментарии для видео
        
        Args:
            video_id: ID видео
            min_rank: Минимальный ранг для фильтрации
            
        Returns:
            List[Dict]: Список комментариев с рангами
        """
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


def main():
    """Основная функция для тестирования ранжирования"""
    import sys
    
    if len(sys.argv) < 2:
        print("Использование: python comment_ranker.py <video_id> [--no-fallback]")
        return
    
    try:
        video_id = int(sys.argv[1])
        use_fallback = "--no-fallback" not in sys.argv
        
        ranker = CommentRanker(use_fallback=use_fallback)
        
        print(f"🚀 Запуск ранжирования комментариев для видео ID: {video_id}")
        if use_fallback:
            print("🔄 Режим: LLM с fallback на эвристику")
        else:
            print("🔄 Режим: только LLM")
            
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