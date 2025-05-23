#!/usr/bin/env python3
"""
Полный пайплайн обработки YouTube видео:
1. Скачивание комментариев
2. Получение транскрипта
3. Генерация summary
4. Ранжирование комментариев
"""

import os
import sys
import time
from comments_downloader import download_comments, save_to_db, extract_video_id, get_transcript, generate_summary
from comment_ranker import CommentRanker
from models import get_db_session, Video, Transcript


def process_video_full_pipeline(video_url: str) -> bool:
    """
    Полный пайплайн обработки видео
    
    Args:
        video_url: URL YouTube видео
        
    Returns:
        bool: True если обработка прошла успешно
    """
    print(f"🚀 Запуск полного пайплайна для видео: {video_url}")
    
    # Шаг 1: Скачивание комментариев
    print("\n📥 Шаг 1: Скачивание комментариев...")
    try:
        session = get_db_session()
        video = session.query(Video).filter_by(youtube_url=video_url).first()
        
        if not video:
            print("Скачиваем комментарии...")
            comments = download_comments(video_url)
            save_to_db(video_url, comments)
            print(f"✅ Скачано и сохранено {len(comments)} комментариев")
            
            # Обновляем объект video
            video = session.query(Video).filter_by(youtube_url=video_url).first()
        else:
            print("✅ Видео уже есть в базе данных")
            
        session.close()
        
    except Exception as e:
        print(f"❌ Ошибка при скачивании комментариев: {e}")
        return False
    
    # Шаг 2: Получение транскрипта
    print("\n📝 Шаг 2: Получение транскрипта...")
    try:
        session = get_db_session()
        video = session.query(Video).filter_by(youtube_url=video_url).first()
        
        # Проверяем, есть ли уже транскрипт
        transcript = session.query(Transcript).filter_by(video_id=video.id).first()
        transcript_text = transcript.content if transcript else None
        
        if not transcript_text:
            video_id = extract_video_id(video_url)
            if video_id:
                transcript_text = get_transcript(video_id)
                if transcript_text:
                    new_transcript = Transcript(video_id=video.id, content=transcript_text)
                    session.add(new_transcript)
                    session.commit()
                    print("✅ Транскрипт получен и сохранен")
                else:
                    print("❌ Не удалось получить транскрипт")
                    session.close()
                    return False
            else:
                print("❌ Не удалось извлечь video_id")
                session.close()
                return False
        else:
            print("✅ Транскрипт уже есть в базе данных")
            
        session.close()
        
    except Exception as e:
        print(f"❌ Ошибка при получении транскрипта: {e}")
        return False
    
    # Шаг 3: Генерация summary
    print("\n🧠 Шаг 3: Генерация summary...")
    try:
        session = get_db_session()
        video = session.query(Video).filter_by(youtube_url=video_url).first()
        
        if not video.summary and transcript_text:
            print("Генерируем summary...")
            summary = generate_summary(transcript_text)
            if summary:
                video.summary = summary
                session.commit()
                print("✅ Summary сгенерировано и сохранено")
            else:
                print("❌ Не удалось сгенерировать summary")
                session.close()
                return False
        else:
            print("✅ Summary уже есть в базе данных")
            
        session.close()
        
    except Exception as e:
        print(f"❌ Ошибка при генерации summary: {e}")
        return False
    
    # Шаг 4: Ранжирование комментариев
    print("\n📊 Шаг 4: Ранжирование комментариев...")
    try:
        session = get_db_session()
        video = session.query(Video).filter_by(youtube_url=video_url).first()
        session.close()
        
        ranker = CommentRanker()
        success = ranker.rank_comments_for_video(video.id)
        
        if success:
            print("✅ Ранжирование комментариев завершено")
            
            # Показываем топ-5 комментариев
            print("\n🏆 Топ-5 самых информативных комментариев:")
            ranked_comments = ranker.get_ranked_comments(video.id, min_rank=0.0)
            
            for i, comment in enumerate(ranked_comments[:5], 1):
                print(f"\n{i}. Ранг: {comment['rank']:.3f} | Лайки: {comment['likes']}")
                print(f"   Автор: {comment['author']}")
                print(f"   Текст: {comment['text'][:150]}...")
                
        else:
            print("❌ Ошибка при ранжировании комментариев")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка при ранжировании комментариев: {e}")
        return False
    
    print(f"\n🎉 Полный пайплайн успешно завершен для видео: {video_url}")
    return True


def main():
    """Основная функция"""
    if len(sys.argv) != 2:
        print("Использование: python process_video.py <youtube_url>")
        print("Пример: python process_video.py 'https://www.youtube.com/watch?v=dQw4w9WgXcQ'")
        return
    
    video_url = sys.argv[1]
    
    # Проверяем, что это YouTube URL
    if "youtube.com" not in video_url and "youtu.be" not in video_url:
        print("❌ Неверный URL. Укажите ссылку на YouTube видео.")
        return
    
    print("=" * 60)
    print("🎬 ПОЛНЫЙ ПАЙПЛАЙН ОБРАБОТКИ YOUTUBE ВИДЕО")
    print("=" * 60)
    
    start_time = time.time()
    success = process_video_full_pipeline(video_url)
    end_time = time.time()
    
    print("\n" + "=" * 60)
    if success:
        print(f"✅ УСПЕХ! Обработка завершена за {end_time - start_time:.1f} секунд")
    else:
        print(f"❌ ОШИБКА! Обработка не завершена")
    print("=" * 60)


if __name__ == "__main__":
    main() 