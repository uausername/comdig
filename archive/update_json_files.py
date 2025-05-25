#!/usr/bin/env python3
"""
Скрипт для обновления JSON файлов с правильными comment_id
"""

from models import Video, Comment, get_db_session
from process_video import VideoProcessor

def update_json_files():
    """Обновляет JSON файлы для всех видео"""
    print("📄 Обновляю JSON файлы...")
    
    session = get_db_session()
    
    # Получаем видео ID 7 (с меньшим количеством комментариев)
    video = session.query(Video).filter_by(id=7).first()
    
    if not video:
        print("❌ Видео не найдено")
        return
    
    print(f"📹 Обновляю JSON для видео ID {video.id}: {video.youtube_url}")
    
    # Извлекаем video_id из URL
    from urllib.parse import urlparse, parse_qs
    try:
        parsed_url = urlparse(video.youtube_url)
        if parsed_url.hostname in ['www.youtube.com', 'youtube.com']:
            youtube_video_id = parse_qs(parsed_url.query)['v'][0]
        elif parsed_url.hostname == 'youtu.be':
            youtube_video_id = parsed_url.path[1:]
        else:
            youtube_video_id = 'unknown'
    except:
        youtube_video_id = 'unknown'
    
    # Создаем процессор и обновляем JSON файлы
    processor = VideoProcessor()
    processor._save_comments_to_json(video.id, video.youtube_url, youtube_video_id)
    processor._save_summary_to_json(video.id, video.youtube_url, youtube_video_id)
    
    session.close()
    print("✅ JSON файлы обновлены!")

if __name__ == "__main__":
    update_json_files() 