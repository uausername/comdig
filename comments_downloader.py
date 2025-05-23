import os
import json
import requests
from youtube_comment_downloader import YoutubeCommentDownloader
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, Video, Comment, Transcript
from datetime import datetime
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
from urllib.parse import urlparse, parse_qs
import time

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

def save_comments_json(comments, filename):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(comments, f, indent=4, ensure_ascii=False)

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
            likes=c.get('likes', 0),
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
        filename = "comments.json"
        save_comments_json(comments, filename)
        print(f"Комментарии сохранены в файл {filename}")
        save_to_db(video_url, comments) # Эта функция теперь создает видео, если его нет
        print(f"Комментарии и видео сохранены в базу данных PostgreSQL")

        # Обновляем объект video после возможного создания в save_to_db
        video = session.query(Video).filter_by(youtube_url=video_url).first()

    # --- Транскрипт и summary (для существующего или нового видео) ---
    video_id = extract_video_id(video_url)

    if video_id and video:
        # Проверяем, есть ли уже транскрипт для этого видео
        transcript = session.query(Transcript).filter_by(video_id=video.id).first()
        transcript_text = transcript.content if transcript else None

        if not transcript_text:
            print(f"Скачиваем транскрипт для video_id: {video_id}...")
            transcript_text = get_transcript(video_id)
            if transcript_text:
                new_transcript = Transcript(video_id=video.id, content=transcript_text)
                session.add(new_transcript)
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
                with open("summary.json", "w", encoding="utf-8") as f:
                    json.dump({"summary": summary}, f, ensure_ascii=False, indent=2)
                    print("Summary также сохранено в summary.json")
            else:
                 print("⚠️ Не удалось сгенерировать саммари.")
        elif video.summary:
             print("✅ Саммари уже существует в базе.")
             print("Существующее summary:")
             print(video.summary)
        else:
            print("⚠️ Пропускаем генерацию саммари — нет транскрипта.")
    else:
        print("⚠️ Не удалось извлечь video_id или найти видео в базе.")

    session.close()

if __name__ == "__main__":
    main()