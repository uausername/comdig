#!/usr/bin/env python3
"""
Тестовый скрипт для демонстрации измерения времени ранжирования
"""

import time
from comment_ranker import CommentRanker
from models import get_db_session, Video, Comment

def test_timing_demo():
    """Демонстрирует измерение времени ранжирования"""
    print("🧪 ТЕСТ ИЗМЕРЕНИЯ ВРЕМЕНИ РАНЖИРОВАНИЯ")
    print("=" * 50)
    
    session = get_db_session()
    try:
        # Ищем видео с комментариями для тестирования
        video = session.query(Video).first()
        if not video:
            print("❌ Нет видео в базе данных для тестирования")
            return
        
        # Проверяем есть ли комментарии
        comments_count = session.query(Comment).filter_by(video_id=video.id).count()
        if comments_count == 0:
            print("❌ Нет комментариев для тестирования")
            return
        
        print(f"📹 Тестовое видео: {video.title[:50]}...")
        print(f"💬 Комментариев: {comments_count}")
        
        # Сбрасываем ранги для демонстрации
        session.query(Comment).filter_by(video_id=video.id).update({Comment.comment_rank: None})
        session.commit()
        print("🔄 Ранги сброшены для демонстрации")
        
        # Тестируем эвристическое ранжирование
        print("\n📊 ТЕСТ ЭВРИСТИЧЕСКОГО РАНЖИРОВАНИЯ:")
        print("-" * 40)
        
        ranker = CommentRanker()
        start_time = time.time()
        success = ranker.rank_comments_for_video(video.id)
        end_time = time.time()
        
        if success:
            duration = end_time - start_time
            print(f"\n✅ Тест завершен успешно!")
            print(f"⏱️ Измеренное время: {duration:.2f} секунд")
            
            # Показываем статистику
            ranked_count = session.query(Comment).filter(
                Comment.video_id == video.id,
                Comment.comment_rank.isnot(None)
            ).count()
            print(f"📊 Проранжировано: {ranked_count}/{comments_count} комментариев")
        else:
            print("❌ Тест не удался")
            
    except Exception as e:
        print(f"❌ Ошибка теста: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    test_timing_demo() 