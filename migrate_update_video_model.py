#!/usr/bin/env python3
"""
Миграция для обновления модели Video:
- Добавление поля video_id
- Добавление поля transcript
- Перенос данных из таблицы transcripts
"""

import os
from sqlalchemy import create_engine, text
from models import get_db_session

def migrate_video_model():
    """Выполняет миграцию модели Video"""
    print("🔄 Начинаю миграцию модели Video...")
    
    # Создаем подключение к БД
    db_host = os.getenv("DB_HOST", "localhost")
    db_port = os.getenv("DB_PORT", "5432")
    db_name = os.getenv("DB_NAME", "comments")
    db_user = os.getenv("DB_USER", "postgres")
    db_password = os.getenv("DB_PASSWORD", "postgres")
    db_url = f"postgresql+psycopg2://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    engine = create_engine(db_url)
    
    with engine.connect() as conn:
        try:
            # 1. Добавляем поле video_id если его нет
            print("📝 Добавляю поле video_id...")
            try:
                conn.execute(text("ALTER TABLE videos ADD COLUMN video_id VARCHAR"))
                conn.commit()
                print("✅ Поле video_id добавлено")
            except Exception as e:
                if "already exists" in str(e):
                    print("ℹ️ Поле video_id уже существует")
                else:
                    print(f"⚠️ Ошибка добавления video_id: {e}")
            
            # 2. Добавляем поле transcript если его нет
            print("📝 Добавляю поле transcript...")
            try:
                conn.execute(text("ALTER TABLE videos ADD COLUMN transcript TEXT"))
                conn.commit()
                print("✅ Поле transcript добавлено")
            except Exception as e:
                if "already exists" in str(e):
                    print("ℹ️ Поле transcript уже существует")
                else:
                    print(f"⚠️ Ошибка добавления transcript: {e}")
            
            # 3. Извлекаем video_id из youtube_url для существующих записей
            print("🔄 Обновляю video_id для существующих записей...")
            result = conn.execute(text("""
                UPDATE videos 
                SET video_id = CASE 
                    WHEN youtube_url LIKE '%youtube.com/watch?v=%' THEN 
                        substring(youtube_url from 'v=([^&]+)')
                    WHEN youtube_url LIKE '%youtu.be/%' THEN 
                        substring(youtube_url from 'youtu.be/([^?]+)')
                    ELSE NULL
                END
                WHERE video_id IS NULL
            """))
            conn.commit()
            print(f"✅ Обновлено {result.rowcount} записей video_id")
            
            # 4. Переносим данные из таблицы transcripts если она существует
            print("🔄 Переношу данные из таблицы transcripts...")
            try:
                result = conn.execute(text("""
                    UPDATE videos 
                    SET transcript = t.content
                    FROM transcripts t
                    WHERE videos.id = t.video_id AND videos.transcript IS NULL
                """))
                conn.commit()
                print(f"✅ Перенесено {result.rowcount} транскриптов")
                
                # Удаляем старую таблицу transcripts
                print("🗑️ Удаляю старую таблицу transcripts...")
                conn.execute(text("DROP TABLE IF EXISTS transcripts"))
                conn.commit()
                print("✅ Таблица transcripts удалена")
                
            except Exception as e:
                print(f"ℹ️ Таблица transcripts не найдена или уже обработана: {e}")
            
            print("🎉 Миграция модели Video завершена успешно!")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка миграции: {e}")
            conn.rollback()
            return False

if __name__ == "__main__":
    migrate_video_model() 