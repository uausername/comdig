#!/usr/bin/env python3
"""
Скрипт для сброса ранжирования комментариев

# Сбросить ранжирование для видео ID 1
docker-compose run --rm comments-downloader python reset_ranking.py 1

# Показать статистику
docker-compose run --rm comments-downloader python reset_ranking.py --stats
"""

from models import get_db_session, Video, Comment

def reset_ranking_for_video(video_id: int) -> bool:
    """
    Сбрасывает ранжирование для всех комментариев указанного видео
    
    Args:
        video_id: ID видео в базе данных
        
    Returns:
        bool: True если сброс прошел успешно
    """
    session = get_db_session()
    try:
        # Проверяем существование видео
        video = session.query(Video).filter_by(id=video_id).first()
        if not video:
            print(f"❌ Видео с ID {video_id} не найдено")
            return False
        
        # Получаем все комментарии с рангами
        ranked_comments = session.query(Comment).filter(
            Comment.video_id == video_id,
            Comment.comment_rank.isnot(None)
        ).all()
        
        if not ranked_comments:
            print(f"ℹ️ У видео {video_id} нет проранжированных комментариев")
            return True
        
        print(f"🔄 Сбрасываю ранжирование для {len(ranked_comments)} комментариев видео {video_id}")
        
        # Сбрасываем ранги
        for comment in ranked_comments:
            comment.comment_rank = None
        
        session.commit()
        print(f"✅ Ранжирование сброшено для видео {video_id}")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при сбросе ранжирования: {e}")
        session.rollback()
        return False
    finally:
        session.close()

def show_ranking_stats():
    """Показывает статистику ранжирования"""
    session = get_db_session()
    try:
        videos = session.query(Video).all()
        print("📊 Статистика ранжирования:")
        print("=" * 50)
        
        total_comments = 0
        total_ranked = 0
        
        for video in videos:
            comments_count = session.query(Comment).filter_by(video_id=video.id).count()
            ranked_count = session.query(Comment).filter(
                Comment.video_id == video.id,
                Comment.comment_rank.isnot(None)
            ).count()
            
            total_comments += comments_count
            total_ranked += ranked_count
            
            print(f"\n🎬 Видео ID: {video.id}")
            print(f"   Комментариев: {comments_count}")
            print(f"   Проранжировано: {ranked_count}")
            print(f"   Прогресс: {ranked_count/comments_count*100:.1f}%" if comments_count > 0 else "   Прогресс: 0%")
        
        print(f"\n📈 Общая статистика:")
        print(f"   Всего комментариев: {total_comments}")
        print(f"   Проранжировано: {total_ranked}")
        print(f"   Общий прогресс: {total_ranked/total_comments*100:.1f}%" if total_comments > 0 else "   Общий прогресс: 0%")
        
    finally:
        session.close()

def main():
    """Основная функция"""
    import sys
    
    if len(sys.argv) < 2:
        print("Использование:")
        print("  python reset_ranking.py <video_id>     # Сбросить ранжирование для конкретного видео")
        print("  python reset_ranking.py --stats        # Показать статистику ранжирования")
        return
    
    try:
        if sys.argv[1] == "--stats":
            show_ranking_stats()
        else:
            video_id = int(sys.argv[1])
            print(f"🔄 Сброс ранжирования для видео ID: {video_id}")
            reset_ranking_for_video(video_id)
        
    except ValueError:
        print("❌ Неверный формат video_id. Должно быть число.")
    except KeyboardInterrupt:
        print("\n👋 Операция прервана пользователем")
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    main()

