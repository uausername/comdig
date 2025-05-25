#!/usr/bin/env python3
"""
Скрипт для исправления comment_id в существующих записях базы данных
"""

from youtube_comment_downloader import YoutubeCommentDownloader
from models import Video, Comment, get_db_session
from urllib.parse import urlparse, parse_qs

def extract_video_id(url):
    """Извлекает video_id из YouTube URL"""
    try:
        parsed_url = urlparse(url)
        if parsed_url.hostname in ['www.youtube.com', 'youtube.com']:
            return parse_qs(parsed_url.query)['v'][0]
        elif parsed_url.hostname == 'youtu.be':
            return parsed_url.path[1:]
        return None
    except:
        return None

def fix_comment_ids():
    """Исправляет comment_id для существующих комментариев"""
    print("🔧 Исправляю comment_id для существующих комментариев...")
    
    session = get_db_session()
    
    # Получаем все видео
    videos = session.query(Video).all()
    
    for video in videos:
        print(f"\n📹 Обрабатываю видео ID {video.id}: {video.youtube_url}")
        
        # Извлекаем video_id из URL
        youtube_video_id = extract_video_id(video.youtube_url)
        if not youtube_video_id:
            print(f"❌ Не удалось извлечь video_id из URL: {video.youtube_url}")
            continue
        
        # Получаем комментарии из базы данных без comment_id
        db_comments = session.query(Comment).filter_by(
            video_id=video.id,
            comment_id=None
        ).all()
        
        if not db_comments:
            print(f"✅ Все комментарии уже имеют comment_id")
            continue
        
        print(f"🔍 Найдено {len(db_comments)} комментариев без comment_id")
        
        try:
            # Загружаем свежие комментарии с YouTube
            print(f"📥 Загружаю свежие комментарии с YouTube...")
            downloader = YoutubeCommentDownloader()
            fresh_comments = list(downloader.get_comments(youtube_video_id))
            
            print(f"📊 Получено {len(fresh_comments)} свежих комментариев")
            
            # Создаем словарь для быстрого поиска по тексту и автору
            fresh_comments_map = {}
            for comment in fresh_comments:
                key = (comment.get('author', ''), comment.get('text', ''))
                fresh_comments_map[key] = comment.get('cid')
            
            # Обновляем comment_id в базе данных
            updated_count = 0
            for db_comment in db_comments:
                key = (db_comment.author, db_comment.text)
                if key in fresh_comments_map:
                    new_comment_id = fresh_comments_map[key]
                    
                    # Проверяем, не существует ли уже такой comment_id
                    existing = session.query(Comment).filter_by(comment_id=new_comment_id).first()
                    if existing and existing.id != db_comment.id:
                        print(f"⚠️ Comment ID {new_comment_id} уже существует, пропускаю")
                        continue
                    
                    db_comment.comment_id = new_comment_id
                    updated_count += 1
            
            # Сохраняем изменения
            session.commit()
            print(f"✅ Обновлено {updated_count} комментариев")
            
        except Exception as e:
            print(f"❌ Ошибка при обработке видео {video.id}: {e}")
            session.rollback()
    
    session.close()
    print("\n🎉 Исправление завершено!")

if __name__ == "__main__":
    fix_comment_ids() 