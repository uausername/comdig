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

def ask_user_for_manual_summary(video_id: str) -> str:
    """Спрашивает пользователя, готов ли он предоставить summary вручную"""
    print("\n" + "="*70)
    print("⚠️ ТРАНСКРИПТ НЕДОСТУПЕН")
    print("="*70)
    print(f"📹 Видео ID: {video_id}")
    print("❌ Не удалось получить транскрипт для данного видео")
    print("🤖 Без транскрипта невозможно:")
    print("   • Сгенерировать качественный summary")
    print("   • Ранжировать комментарии по релевантности")
    print("="*70)
    
    while True:
        user_input = input("❓ Готовы ли вы предоставить summary видео самостоятельно? (yes/no): ").strip().lower()
        
        if user_input in ['yes', 'y', 'да', 'д']:
            print("\n📝 Введите summary видео:")
            print("💡 Рекомендации:")
            print("   • Опишите основные темы и ключевые моменты")
            print("   • Длина: 3-5 предложений")
            print("   • Используйте понятный язык")
            print("\n📝 Ваш summary (нажмите Enter дважды для завершения):")
            
            lines = []
            while True:
                line = input()
                if line == "" and lines:
                    break
                lines.append(line)
            
            manual_summary = "\n".join(lines).strip()
            
            if manual_summary and len(manual_summary) > 20:
                print(f"\n✅ Получен пользовательский summary длиной {len(manual_summary)} символов")
                return manual_summary
            else:
                print("❌ Summary слишком короткий. Попробуйте еще раз.")
                continue
                
        elif user_input in ['no', 'n', 'нет', 'н']:
            print("\n❌ Обработка остановлена пользователем")
            print("💡 Попробуйте найти видео с доступными субтитрами")
            return None
        else:
            print("❌ Пожалуйста, введите 'yes' или 'no'")

# Обновленная функция для генерации summary с помощью HTTP запроса к сервису суммаризации
def generate_summary(text):
    if not text:
        return None
    
    # Пробуем использовать Gemini API
    try:
        from google import genai
        from google.genai import types
        import os
        
        gemini_api_key = os.getenv('GEMINI_API_KEY')
        if gemini_api_key:
            print("🤖 Генерирую summary через Gemini API...")
            
            # Создаем клиент с v1alpha API
            client = genai.Client(
                api_key=gemini_api_key,
                http_options=types.HttpOptions(api_version='v1alpha')
            )
            
            prompt = f"""
            Создай краткое содержание видео на русском языке в 2-3 предложениях.
            
            Транскрипт видео:
            {text[:4000]}  # Ограничиваем длину для API
            
            Краткое содержание:
            """
            
            generation_config = types.GenerateContentConfig(
                temperature=0.3,
                max_output_tokens=200,
                top_p=0.8
            )
            
            response = client.models.generate_content(
                model='gemini-2.0-flash',
                contents=prompt,
                config=generation_config
            )
            
            if response.text:
                summary = response.text.strip()
                print(f"✅ Сгенерирован summary через Gemini API длиной {len(summary)} символов")
                return summary
        else:
            print("⚠️ GEMINI_API_KEY не найден")
    except Exception as e:
        print(f"⚠️ Ошибка Gemini API: {e}")
    
    # Fallback: используем первые 300 символов транскрипта
    print("🔄 Использую fallback summary...")
    fallback_summary = f"Краткое содержание видео (первые 300 символов транскрипта): {text[:300]}..."
    print(f"✅ Создан fallback summary длиной {len(fallback_summary)} символов")
    return fallback_summary

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
                print("❌ Не удалось скачать транскрипт.")
                # Спрашиваем пользователя о ручном вводе summary
                manual_summary = ask_user_for_manual_summary(video_id)
                if not manual_summary:
                    print("❌ Обработка остановлена пользователем.")
                    session.close()
                    return  # Завершаем main() без аварии
                
                # Используем пользовательский summary
                video.summary = manual_summary
                session.commit()
                print("✅ Пользовательский summary сохранен в базу.")
                
                # Сохраняем summary в файл
                video_id_youtube = extract_video_id(video_url)
                summary_data = {
                    "database_video_id": video.id,
                    "youtube_video_id": video_id_youtube,
                    "video_title": video.title,
                    "video_url": video_url,
                    "summary": manual_summary,
                    "created_at": video.upload_date
                }
                with open("summary.json", "w", encoding="utf-8") as f:
                    json.dump(summary_data, f, ensure_ascii=False, indent=2)
                    print("Пользовательский summary сохранен в summary.json")
                
                session.close()
                return

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