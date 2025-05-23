#!/usr/bin/env python3
"""
Миграция для добавления поля comment_rank в таблицу comments
"""

import os
from sqlalchemy import create_engine, text

def migrate_add_rank_column():
    """Добавляет поле comment_rank в таблицу comments если его нет"""
    
    # Подключение к базе данных
    db_host = os.getenv("DB_HOST", "localhost")
    db_port = os.getenv("DB_PORT", "5432")
    db_name = os.getenv("DB_NAME", "comments")
    db_user = os.getenv("DB_USER", "postgres")
    db_password = os.getenv("DB_PASSWORD", "postgres")
    db_url = f"postgresql+psycopg2://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    
    engine = create_engine(db_url)
    
    try:
        with engine.connect() as connection:
            # Проверяем, существует ли уже поле comment_rank
            result = connection.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='comments' AND column_name='comment_rank'
            """))
            
            if result.fetchone():
                print("✅ Поле 'comment_rank' уже существует в таблице 'comments'")
                return True
            
            # Добавляем поле comment_rank
            connection.execute(text("""
                ALTER TABLE comments 
                ADD COLUMN comment_rank FLOAT
            """))
            
            connection.commit()
            print("✅ Поле 'comment_rank' успешно добавлено в таблицу 'comments'")
            return True
            
    except Exception as e:
        print(f"❌ Ошибка при выполнении миграции: {e}")
        return False

def main():
    """Основная функция"""
    print("🔄 Запуск миграции для добавления поля 'comment_rank'...")
    success = migrate_add_rank_column()
    
    if success:
        print("🎉 Миграция завершена успешно!")
    else:
        print("💥 Миграция завершилась с ошибкой!")

if __name__ == "__main__":
    main() 