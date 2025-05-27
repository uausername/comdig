#!/usr/bin/env python3
"""
Скрипт для сброса данных видео (транскрипт и summary)

# Сбросить данные для видео ID 1
docker-compose run --rm comments-downloader python reset_video_data.py 11

# Сбросить только транскрипт для видео ID 1
docker-compose run --rm comments-downloader python reset_video_data.py 1 --transcript-only

# Сбросить только summary для видео ID 1
docker-compose run --rm comments-downloader python reset_video_data.py 1 --summary-only

# Показать статистику данных видео
docker-compose run --rm comments-downloader python reset_video_data.py --stats

# Полная очистка всех данных видео (транскрипт + summary)
docker-compose run --rm comments-downloader python reset_video_data.py --all
"""

from models import get_db_session, Video, Comment

def reset_video_data(video_id: int, transcript_only: bool = False, summary_only: bool = False) -> bool:
    """
    Сбрасывает данные видео (транскрипт и/или summary)
    
    Args:
        video_id: ID видео в базе данных
        transcript_only: Сбросить только транскрипт
        summary_only: Сбросить только summary
        
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
        
        print(f"🎬 Видео ID: {video_id}")
        print(f"📹 YouTube ID: {video.video_id}")
        print(f"🔗 URL: {video.youtube_url}")
        
        # Определяем что сбрасывать
        reset_transcript = not summary_only
        reset_summary = not transcript_only
        
        changes_made = False
        
        # Сбрасываем транскрипт
        if reset_transcript and video.transcript:
            print(f"🔄 Сбрасываю транскрипт (длина: {len(video.transcript)} символов)")
            video.transcript = None
            changes_made = True
        elif reset_transcript:
            print("ℹ️ Транскрипт уже отсутствует")
        
        # Сбрасываем summary
        if reset_summary and video.summary:
            print(f"🔄 Сбрасываю summary (длина: {len(video.summary)} символов)")
            video.summary = None
            changes_made = True
        elif reset_summary:
            print("ℹ️ Summary уже отсутствует")
        
        if changes_made:
            session.commit()
            print(f"✅ Данные видео {video_id} сброшены")
        else:
            print(f"ℹ️ Нет данных для сброса у видео {video_id}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при сбросе данных видео: {e}")
        session.rollback()
        return False
    finally:
        session.close()

def reset_all_video_data() -> bool:
    """Сбрасывает данные всех видео"""
    session = get_db_session()
    try:
        # Получаем ВСЕ видео
        all_videos = session.query(Video).all()
        
        if not all_videos:
            print("ℹ️ В базе данных нет видео")
            return True
        
        # Фильтруем видео с данными
        videos_with_data = [v for v in all_videos if v.transcript or v.summary]
        videos_without_data = [v for v in all_videos if not v.transcript and not v.summary]
        
        print(f"📊 Найдено видео:")
        print(f"   - С данными для сброса: {len(videos_with_data)}")
        print(f"   - Уже без данных: {len(videos_without_data)}")
        print(f"   - Всего видео: {len(all_videos)}")
        
        if videos_without_data:
            print(f"\n📝 Видео без данных (пропускаются):")
            for video in videos_without_data:
                print(f"   - ID {video.id}: {video.video_id}")
        
        if not videos_with_data:
            print("ℹ️ Нет видео с данными для сброса")
            return True
        
        print(f"\n🔄 Видео для сброса данных:")
        for video in videos_with_data:
            transcript_info = f"транскрипт ({len(video.transcript)} символов)" if video.transcript else "нет транскрипта"
            summary_info = f"summary ({len(video.summary)} символов)" if video.summary else "нет summary"
            print(f"   - ID {video.id}: {video.video_id} - {transcript_info}, {summary_info}")
        
        confirm = input(f"\n⚠️ Вы уверены, что хотите сбросить данные у {len(videos_with_data)} видео? (yes/no): ")
        if confirm.lower() != 'yes':
            print("❌ Операция отменена")
            return False
        
        reset_count = 0
        for video in videos_with_data:
            print(f"🔄 Сбрасываю данные видео ID: {video.id} ({video.video_id})")
            video.transcript = None
            video.summary = None
            reset_count += 1
        
        session.commit()
        print(f"✅ Данные сброшены для {reset_count} видео")
        
        if videos_without_data:
            print(f"ℹ️ {len(videos_without_data)} видео пропущено (уже без данных)")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при массовом сбросе: {e}")
        session.rollback()
        return False
    finally:
        session.close()

def show_video_data_stats():
    """Показывает статистику данных видео"""
    session = get_db_session()
    try:
        videos = session.query(Video).all()
        print("📊 Статистика данных видео:")
        print("=" * 60)
        
        total_videos = len(videos)
        videos_with_transcript = 0
        videos_with_summary = 0
        videos_with_both = 0
        
        for video in videos:
            has_transcript = video.transcript is not None
            has_summary = video.summary is not None
            
            if has_transcript:
                videos_with_transcript += 1
            if has_summary:
                videos_with_summary += 1
            if has_transcript and has_summary:
                videos_with_both += 1
            
            # Показываем детали каждого видео
            print(f"\n🎬 Видео ID: {video.id}")
            print(f"   YouTube ID: {video.video_id or 'N/A'}")
            print(f"   Транскрипт: {'✅' if has_transcript else '❌'} {f'({len(video.transcript)} символов)' if has_transcript else ''}")
            print(f"   Summary: {'✅' if has_summary else '❌'} {f'({len(video.summary)} символов)' if has_summary else ''}")
            
            # Показываем количество комментариев
            comments_count = session.query(Comment).filter_by(video_id=video.id).count()
            ranked_count = session.query(Comment).filter(
                Comment.video_id == video.id,
                Comment.comment_rank.isnot(None)
            ).count()
            print(f"   Комментарии: {comments_count} (ранжировано: {ranked_count})")
        
        print(f"\n📈 Общая статистика:")
        print(f"   Всего видео: {total_videos}")
        print(f"   С транскриптом: {videos_with_transcript} ({videos_with_transcript/total_videos*100:.1f}%)" if total_videos > 0 else "   С транскриптом: 0")
        print(f"   С summary: {videos_with_summary} ({videos_with_summary/total_videos*100:.1f}%)" if total_videos > 0 else "   С summary: 0")
        print(f"   С полными данными: {videos_with_both} ({videos_with_both/total_videos*100:.1f}%)" if total_videos > 0 else "   С полными данными: 0")
        
    finally:
        session.close()

def main():
    """Основная функция"""
    import sys
    
    if len(sys.argv) < 2:
        print("Использование:")
        print("  python reset_video_data.py <video_id>                    # Сбросить все данные видео")
        print("  python reset_video_data.py <video_id> --transcript-only  # Сбросить только транскрипт")
        print("  python reset_video_data.py <video_id> --summary-only     # Сбросить только summary")
        print("  python reset_video_data.py --stats                       # Показать статистику")
        print("  python reset_video_data.py --all                         # Сбросить данные всех видео")
        print("\nПримеры:")
        print("  docker-compose run --rm comments-downloader python reset_video_data.py 1")
        print("  docker-compose run --rm comments-downloader python reset_video_data.py 1 --transcript-only")
        print("  docker-compose run --rm comments-downloader python reset_video_data.py --stats")
        return
    
    try:
        if sys.argv[1] == "--stats":
            show_video_data_stats()
        elif sys.argv[1] == "--all":
            print("🔄 Массовый сброс данных всех видео")
            reset_all_video_data()
        else:
            video_id = int(sys.argv[1])
            
            # Проверяем флаги
            transcript_only = "--transcript-only" in sys.argv
            summary_only = "--summary-only" in sys.argv
            
            if transcript_only and summary_only:
                print("❌ Нельзя использовать --transcript-only и --summary-only одновременно")
                return
            
            action_desc = "транскрипта" if transcript_only else "summary" if summary_only else "всех данных"
            print(f"🔄 Сброс {action_desc} для видео ID: {video_id}")
            
            reset_video_data(video_id, transcript_only, summary_only)
        
    except ValueError:
        print("❌ Неверный формат video_id. Должно быть число.")
    except KeyboardInterrupt:
        print("\n👋 Операция прервана пользователем")
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    main() 