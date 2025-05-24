import os
import json
import requests
from youtube_comment_downloader import YoutubeCommentDownloader
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, Video, Comment
from datetime import datetime
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
from urllib.parse import urlparse, parse_qs
import time
import re

def get_db_session():
    db_host = os.getenv("DB_HOST", "localhost")
    db_port = os.getenv("DB_PORT", "5432")
    db_name = os.getenv("DB_NAME", "comments")
    db_user = os.getenv("DB_USER", "postgres")
    db_password = os.getenv("DB_PASSWORD", "postgres")
    db_url = f"postgresql+psycopg2://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    engine = create_engine(db_url)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session()

def download_comments(video_url):
    downloader = YoutubeCommentDownloader()
    comments = []
    for i, comment in enumerate(downloader.get_comments_from_url(video_url), 1):
        comments.append(comment)
        if i % 10 == 0:
            print(f"Скачано {i} комментариев...")
    return comments

def save_comments_json(comments, filename, video_url=None, video_db_id=None):
    """Сохраняет комментарии в JSON файл с дополнительными полями"""
    enhanced_comments = []
    
    for comment in comments:
        # Извлекаем video_id из URL для формирования ссылки на комментарий
        video_id = extract_video_id(video_url) if video_url else None
        comment_url = None
        
        if video_id and comment.get('cid'):
            comment_url = f"https://www.youtube.com/watch?v={video_id}&lc={comment.get('cid')}"
        
        enhanced_comment = {
            "database_id": video_db_id,  # ID видео в базе данных
            "comment_id": comment.get('cid'),  # Исправляем на cid
            "video_url": video_url,  # Адрес исходного видео
            "comment_url": comment_url,  # Ссылка на комментарий в YouTube
            "text": comment.get('text'),
            "time": comment.get('time'),
            "author": comment.get('author'),
            "channel": comment.get('channel'),
            "votes": comment.get('votes'),
            "replies": comment.get('replies'),
            "photo": comment.get('photo'),
            "heart": comment.get('heart'),
            "reply": comment.get('reply'),
            "time_parsed": comment.get('time_parsed')
        }
        enhanced_comments.append(enhanced_comment)
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(enhanced_comments, f, indent=4, ensure_ascii=False)

def save_to_db(video_url, comments):
    session = get_db_session()
    # Попробуем получить видео, если его нет — создадим
    video = session.query(Video).filter_by(youtube_url=video_url).first()
    if not video:
        video = Video(
            youtube_url=video_url,
            title=None,
            channel=None,
            upload_date=None,
            summary=None
        )
        session.add(video)
        session.commit()
    # Сохраняем комментарии, избегая дубликатов
    for c in comments:
        # Проверяем, есть ли уже такой comment_id
        exists = session.query(Comment).filter_by(comment_id=c.get('cid')).first()
        if exists:
            continue  # пропускаем дубликат
        published_at = None
        if c.get('time'):
            try:
                # updated_at: преобразуем в datetime, если возможно
                published_at = datetime.strptime(c['time'], '%Y-%m-%dT%H:%M:%SZ')
            except Exception:
                published_at = None
        comment = Comment(
            comment_id=c.get('cid'),
            video_id=video.id,
            author=c.get('author'),
            text=c.get('text'),
            likes=parse_likes_count(c.get('votes')),
            published_at=published_at,
            parent_id=c.get('parent')
        )
        session.add(comment)
    session.commit()
    session.close()

def extract_video_id(video_url):
    parsed = urlparse(video_url)
    if parsed.hostname == 'youtu.be':
        return parsed.path[1:]
    elif parsed.hostname in ('www.youtube.com', 'youtube.com'):
        return parse_qs(parsed.query).get('v', [None])[0]
    return None

def get_transcript(video_id):
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=['ru', 'en'])
        return " ".join([entry['text'] for entry in transcript])
    except (TranscriptsDisabled, NoTranscriptFound):
        print("❌ Субтитры не найдены")
        return None
    except Exception as e:
        print(f"❌ Ошибка при получении транскрипта: {e}")
        return None

# Обновленная функция для генерации summary с помощью HTTP запроса к сервису суммаризации
def generate_summary(text):
    if not text:
        return None
    
    summarizer_service_url = "http://summarizer-llm:8000/summarize"
    print(f"Отправка текста на суммаризацию по адресу: {summarizer_service_url}")
    
    max_retries = 3
    for attempt in range(1, max_retries + 1):
        try:
            response = requests.post(summarizer_service_url, json={"text": text}, timeout=600)  # увеличен таймаут
            response.raise_for_status() # Проверка на ошибки HTTP (4xx, 5xx)
            summary_data = response.json()
            summary = summary_data.get("summary")
            if not summary:
                print("⚠️ Сервис суммаризации вернул пустой результат.")
                return None
            return summary
        except requests.exceptions.RequestException as e:
            print(f"Попытка {attempt}/{max_retries}: Ошибка при обращении к сервису суммаризации: {e}")
            if attempt < max_retries:
                print("Повторная попытка через 10 секунд...")
                time.sleep(10)
            else:
                print("Убедитесь, что сервис 'summarizer-llm' запущен и доступен по адресу http://summarizer-llm:8000")
                return None
        except Exception as e:
            print(f"Неизвестная ошибка при генерации саммари: {e}")
            return None

def parse_likes_count(likes_str):
    """Парсит количество лайков из строки YouTube"""
    if not likes_str or likes_str == '':
        return 0
    
    # Если это уже число
    if isinstance(likes_str, int):
        return likes_str
    
    # Преобразуем в строку
    likes_str = str(likes_str).strip()
    
    # Если пустая строка
    if not likes_str:
        return 0
    
    # Убираем пробелы и приводим к нижнему регистру
    likes_str = likes_str.lower().replace(' ', '')
    
    # Обрабатываем сокращения
    if 'тыс' in likes_str or 'k' in likes_str:
        # Извлекаем число перед "тыс" или "k"
        match = re.search(r'(\d+(?:[,\.]\d+)?)', likes_str)
        if match:
            number = match.group(1).replace(',', '.')
            return int(float(number) * 1000)
    
    if 'млн' in likes_str or 'm' in likes_str:
        # Извлекаем число перед "млн" или "m"
        match = re.search(r'(\d+(?:[,\.]\d+)?)', likes_str)
        if match:
            number = match.group(1).replace(',', '.')
            return int(float(number) * 1000000)
    
    # Пробуем извлечь просто число
    match = re.search(r'(\d+)', likes_str)
    if match:
        return int(match.group(1))
    
    # Если ничего не получилось
    return 0

def main():
    video_url = os.environ.get("VIDEO_URL")
    if not video_url:
        video_url = input("Введите ссылку на YouTube-видео: ")

    # Проверяем, есть ли уже видео в базе
    session = get_db_session()
    video = session.query(Video).filter_by(youtube_url=video_url).first()

    if not video:
        # Скачиваем и сохраняем комментарии и видео, если оно новое
        print(f"Скачиваем комментарии для {video_url}...")
        comments = download_comments(video_url)
        save_to_db(video_url, comments) # Сначала сохраняем в БД
        print(f"Комментарии и видео сохранены в базу данных PostgreSQL")

        # Обновляем объект video после создания в save_to_db
        video = session.query(Video).filter_by(youtube_url=video_url).first()
        
        # Теперь сохраняем в JSON с правильным video.id
        filename = "comments.json"
        save_comments_json(comments, filename, video_url, video.id if video else None)
        print(f"Комментарии сохранены в файл {filename}")

    # --- Транскрипт и summary (для существующего или нового видео) ---
    video_id = extract_video_id(video_url)

    if video_id and video:
        # Проверяем, есть ли уже транскрипт для этого видео
        transcript_text = video.transcript

        if not transcript_text:
            print(f"Скачиваем транскрипт для video_id: {video_id}...")
            transcript_text = get_transcript(video_id)
            if transcript_text:
                video.transcript = transcript_text
                session.commit() # Сохраняем транскрипт сразу
                print("✅ Транскрипт сохранен в базу.")
            else:
                print("❌ Не удалось скачать транскрипт. Пропускаем генерацию summary.")
                session.close()
                return  # Завершаем main() без аварии

        # Генерируем summary, если есть транскрипт и summary еще не сгенерировано
        if transcript_text and not video.summary:
            print("Генерируем саммари...")
            summary = generate_summary(transcript_text)
            if summary: # Проверяем, что summary не None или пустая строка после обработки ошибок
                video.summary = summary
                session.commit() # Сохраняем summary
                print("✅ Саммари сгенерировано и добавлено в базу.")
                print("Сгенерированное summary:")
                print(summary)
                # Сохраняем summary в файл
                video_id_youtube = extract_video_id(video_url)
                summary_data = {
                    "database_video_id": video.id,  # ID исходного видео в базе
                    "youtube_video_id": video_id_youtube,
                    "video_title": video.title,  # Название видео
                    "video_url": video_url,  # Адрес исходного видео
                    "summary": summary,
                    "created_at": video.upload_date
                }
                with open("summary.json", "w", encoding="utf-8") as f:
                    json.dump(summary_data, f, ensure_ascii=False, indent=2)
                    print("Summary также сохранено в summary.json")
            else:
                 print("⚠️ Не удалось сгенерировать саммари.")
        elif video.summary:
             print("✅ Саммари уже существует в базе.")
             print("Существующее summary:")
             print(video.summary)
             # Сохраняем существующий summary в файл
             video_id_youtube = extract_video_id(video_url)
             summary_data = {
                 "database_video_id": video.id,  # ID исходного видео в базе
                 "youtube_video_id": video_id_youtube,
                 "video_title": video.title,  # Название видео
                 "video_url": video_url,  # Адрес исходного видео
                 "summary": video.summary,
                 "created_at": video.upload_date
             }
             with open("summary.json", "w", encoding="utf-8") as f:
                 json.dump(summary_data, f, ensure_ascii=False, indent=2)
                 print("Существующий summary также сохранен в summary.json")
        else:
            print("⚠️ Пропускаем генерацию саммари — нет транскрипта.")
    else:
        print("⚠️ Не удалось извлечь video_id или найти видео в базе.")

    session.close()

if __name__ == "__main__":
    main()