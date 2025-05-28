#!/usr/bin/env python3
"""
Скрипт для сброса данных видео (транскрипт, summary и комментарии)

# Сбросить данные для видео ID 1
docker-compose run --rm comments-downloader python reset_video_data.py 11

# Сбросить только транскрипт для видео ID 1
docker-compose run --rm comments-downloader python reset_video_data.py 1 --transcript-only

# Сбросить только summary для видео ID 1
docker-compose run --rm comments-downloader python reset_video_data.py 1 --summary-only

# Сбросить только комментарии для видео ID 1
docker-compose run --rm comments-downloader python reset_video_data.py 1 --comments-only

# Сбросить только ранжирование для видео ID 1
docker-compose run --rm comments-downloader python reset_video_data.py 1 --ranking-only

# Показать статистику данных видео
docker-compose run --rm comments-downloader python reset_video_data.py --stats

# Полная очистка всех данных видео (транскрипт + summary + комментарии)
docker-compose run --rm comments-downloader python reset_video_data.py --all
"""

from models import get_db_session, Video, Comment

def reset_comments_data(video_id: int) -> bool:
    """
    Сбрасывает все комментарии для указанного видео
    
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
        
        # Подсчитываем количество комментариев
        comments_count = session.query(Comment).filter_by(video_id=video_id).count()
        
        if comments_count == 0:
            print(f"ℹ️ У видео {video_id} нет комментариев для удаления")
            return True
        
        print(f"🎬 Видео ID: {video_id}")
        print(f"📹 YouTube ID: {video.video_id}")
        print(f"💬 Найдено комментариев: {comments_count}")
        
        # Удаляем все комментарии для этого видео
        deleted_count = session.query(Comment).filter_by(video_id=video_id).delete()
        session.commit()
        
        print(f"✅ Удалено {deleted_count} комментариев для видео {video_id}")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при удалении комментариев: {e}")
        session.rollback()
        return False
    finally:
        session.close()

def reset_video_data(video_id: int, transcript_only: bool = False, summary_only: bool = False, comments_only: bool = False, ranking_only: bool = False) -> bool:
    """
    Сбрасывает данные видео (транскрипт, summary и/или комментарии)
    
    Args:
        video_id: ID видео в базе данных
        transcript_only: Сбросить только транскрипт
        summary_only: Сбросить только summary
        comments_only: Сбросить только комментарии
        ranking_only: Сбросить только ранжирование комментариев
        
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
        
        # Если указан только сброс комментариев
        if comments_only:
            return reset_comments_data(video_id)
        
        # Если указан только сброс ранжирования
        if ranking_only:
            ranked_comments = session.query(Comment).filter(
                Comment.video_id == video_id,
                Comment.comment_rank.isnot(None)
            ).count()
            
            if ranked_comments == 0:
                print(f"ℹ️ У видео {video_id} нет проранжированных комментариев")
                return True
            
            print(f"🔄 Сбрасываю ранжирование {ranked_comments} комментариев")
            session.query(Comment).filter_by(video_id=video_id).update(
                {Comment.comment_rank: None}
            )
            session.commit()
            print(f"✅ Ранжирование сброшено для {ranked_comments} комментариев видео {video_id}")
            return True
        
        # Определяем что сбрасывать
        reset_transcript = not summary_only and not comments_only and not ranking_only
        reset_summary = not transcript_only and not comments_only and not ranking_only
        reset_comments = not transcript_only and not summary_only and not ranking_only
        
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
        
        # Сбрасываем комментарии
        if reset_comments:
            comments_count = session.query(Comment).filter_by(video_id=video_id).count()
            if comments_count > 0:
                print(f"🔄 Удаляю {comments_count} комментариев")
                session.query(Comment).filter_by(video_id=video_id).delete()
                changes_made = True
            else:
                print("ℹ️ Комментарии уже отсутствуют")
        else:
            # Если комментарии не удаляются, но сбрасываются другие данные, 
            # то также сбрасываем ранжирование комментариев
            if reset_transcript or reset_summary:
                ranked_comments = session.query(Comment).filter(
                    Comment.video_id == video_id,
                    Comment.comment_rank.isnot(None)
                ).count()
                if ranked_comments > 0:
                    print(f"🔄 Сбрасываю ранжирование {ranked_comments} комментариев")
                    session.query(Comment).filter_by(video_id=video_id).update(
                        {Comment.comment_rank: None}
                    )
                    changes_made = True
                else:
                    print("ℹ️ Ранжирование комментариев уже отсутствует")
        
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
    """Сбрасывает данные всех видео (включая комментарии)"""
    session = get_db_session()
    try:
        # Получаем ВСЕ видео
        all_videos = session.query(Video).all()
        
        if not all_videos:
            print("ℹ️ В базе данных нет видео")
            return True
        
        # Фильтруем видео с данными
        videos_with_data = []
        videos_without_data = []
        
        for video in all_videos:
            comments_count = session.query(Comment).filter_by(video_id=video.id).count()
            has_data = video.transcript or video.summary or comments_count > 0
            
            if has_data:
                videos_with_data.append(video)
            else:
                videos_without_data.append(video)
        
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
            comments_count = session.query(Comment).filter_by(video_id=video.id).count()
            comments_info = f"{comments_count} комментариев" if comments_count > 0 else "нет комментариев"
            print(f"   - ID {video.id}: {video.video_id} - {transcript_info}, {summary_info}, {comments_info}")
        
        confirm = input(f"\n⚠️ Вы уверены, что хотите сбросить ВСЕ данные у {len(videos_with_data)} видео? (yes/no): ")
        if confirm.lower() != 'yes':
            print("❌ Операция отменена")
            return False
        
        reset_count = 0
        total_comments_deleted = 0
        
        for video in videos_with_data:
            print(f"🔄 Сбрасываю данные видео ID: {video.id} ({video.video_id})")
            
            # Удаляем комментарии
            comments_count = session.query(Comment).filter_by(video_id=video.id).count()
            if comments_count > 0:
                session.query(Comment).filter_by(video_id=video.id).delete()
                total_comments_deleted += comments_count
                print(f"   💬 Удалено {comments_count} комментариев")
            
            # Сбрасываем транскрипт и summary
            video.transcript = None
            video.summary = None
            reset_count += 1
        
        session.commit()
        print(f"✅ Данные сброшены для {reset_count} видео")
        print(f"💬 Всего удалено комментариев: {total_comments_deleted}")
        
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
        print("  python reset_video_data.py <video_id> --comments-only    # Сбросить только комментарии")
        print("  python reset_video_data.py <video_id> --ranking-only     # Сбросить только ранжирование")
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
            comments_only = "--comments-only" in sys.argv
            ranking_only = "--ranking-only" in sys.argv
            
            # Проверяем конфликтующие флаги
            flags_count = sum([transcript_only, summary_only, comments_only, ranking_only])
            if flags_count > 1:
                print("❌ Нельзя использовать несколько флагов одновременно")
                print("   Доступные флаги: --transcript-only, --summary-only, --comments-only, --ranking-only")
                return
            
            action_desc = "транскрипта" if transcript_only else "summary" if summary_only else "комментариев" if comments_only else "ранжирования" if ranking_only else "всех данных"
            print(f"🔄 Сброс {action_desc} для видео ID: {video_id}")
            
            reset_video_data(video_id, transcript_only, summary_only, comments_only, ranking_only)
        
    except ValueError:
        print("❌ Неверный формат video_id. Должно быть число.")
    except KeyboardInterrupt:
        print("\n👋 Операция прервана пользователем")
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    main() 