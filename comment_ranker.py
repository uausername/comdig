import requests
import json
import time
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from models import Video, Comment, get_db_session

class CommentRanker:
    """Система ранжирования комментариев по информативности"""
    
    def __init__(self, llm_service_url: str = "http://summarizer-llm:8080"):
        self.llm_service_url = llm_service_url
        self.batch_size = 5  # Размер батча для обработки
        
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
                rank=None
            ).all()
            
            if not comments:
                print(f"✅ Все комментарии для видео {video_id} уже проранжированы")
                return True
                
            print(f"🔄 Начинаю ранжирование {len(comments)} комментариев для видео {video_id}")
            
            # Обрабатываем комментарии батчами
            for i in range(0, len(comments), self.batch_size):
                batch = comments[i:i + self.batch_size]
                self._process_batch(batch, video.summary, session)
                
                # Небольшая пауза между батчами
                time.sleep(1)
                
            session.commit()
            print(f"✅ Ранжирование завершено для видео {video_id}")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка при ранжировании комментариев: {e}")
            session.rollback()
            return False
        finally:
            session.close()
    
    def _process_batch(self, comments: List[Comment], video_summary: str, session: Session):
        """Обрабатывает батч комментариев"""
        for comment in comments:
            try:
                rank = self._rank_single_comment(comment.text, video_summary)
                if rank is not None:
                    comment.rank = rank
                    print(f"📊 Комментарий ID {comment.id}: ранг {rank:.3f}")
                else:
                    print(f"⚠️ Не удалось проранжировать комментарий ID {comment.id}")
                    
            except Exception as e:
                print(f"❌ Ошибка при обработке комментария ID {comment.id}: {e}")
    
    def _rank_single_comment(self, comment_text: str, video_summary: str) -> Optional[float]:
        """
        Ранжирует один комментарий
        
        Args:
            comment_text: Текст комментария
            video_summary: Краткое содержание видео
            
        Returns:
            float: Ранг от 0.0 до 1.0 или None при ошибке
        """
        prompt = self._create_ranking_prompt(comment_text, video_summary)
        
        try:
            response = requests.post(
                f"{self.llm_service_url}/completion",
                json={
                    "prompt": prompt,
                    "n_predict": 50,
                    "temperature": 0.1,
                    "stop": ["\n", "Объяснение:", "Комментарий:"]
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result.get("content", "").strip()
                
                # Извлекаем числовую оценку из ответа
                rank = self._extract_rank_from_response(content)
                return rank
            else:
                print(f"❌ Ошибка LLM сервиса: {response.status_code}")
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Ошибка соединения с LLM: {e}")
            return None
    
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

Оценка: """
    
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
                Comment.rank.isnot(None),
                Comment.rank >= min_rank
            ).order_by(Comment.rank.desc()).all()
            
            result = []
            for comment in comments:
                result.append({
                    'id': comment.id,
                    'author': comment.author,
                    'text': comment.text,
                    'likes': comment.likes,
                    'rank': comment.rank,
                    'published_at': comment.published_at.isoformat() if comment.published_at else None
                })
            
            return result
            
        finally:
            session.close()


def main():
    """Основная функция для тестирования ранжирования"""
    import sys
    
    if len(sys.argv) != 2:
        print("Использование: python comment_ranker.py <video_id>")
        return
    
    try:
        video_id = int(sys.argv[1])
        ranker = CommentRanker()
        
        print(f"🚀 Запуск ранжирования комментариев для видео ID: {video_id}")
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