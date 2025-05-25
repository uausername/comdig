#!/usr/bin/env python3
"""
Демонстрационный скрипт системы ранжирования комментариев с моковыми данными
"""

import random
from models import get_db_session, Video, Comment
from comment_ranker import CommentRanker
import time

class MockCommentRanker(CommentRanker):
    """Моковая версия ранжировщика для демонстрации"""
    
    def _rank_single_comment(self, comment_text: str, video_summary: str) -> float:
        """Генерирует моковый ранг на основе эвристик"""
        
        # Простые эвристики для демонстрации
        rank = 0.5  # базовый ранг
        
        # Длинные комментарии обычно более информативны
        if len(comment_text) > 100:
            rank += 0.2
        elif len(comment_text) < 20:
            rank -= 0.2
            
        # Комментарии с вопросами могут быть более информативными
        if '?' in comment_text:
            rank += 0.1
            
        # Комментарии только с эмодзи менее информативны
        if len(comment_text.strip()) < 10 and any(ord(char) > 127 for char in comment_text):
            rank -= 0.3
            
        # Комментарии с ключевыми словами более релевантны
        keywords = ['рецепт', 'ингредиент', 'приготовление', 'вкус', 'температура', 'время']
        for keyword in keywords:
            if keyword.lower() in comment_text.lower():
                rank += 0.15
                break
                
        # Добавляем немного случайности
        rank += random.uniform(-0.1, 0.1)
        
        # Ограничиваем диапазон
        return max(0.0, min(1.0, rank))

def create_demo_data():
    """Создает демонстрационные данные если их нет"""
    session = get_db_session()
    try:
        # Проверяем есть ли уже демо-видео
        demo_video = session.query(Video).filter(
            Video.youtube_url.like("%DEMO%")
        ).first()
        
        if demo_video:
            print("✅ Демонстрационные данные уже существуют")
            return demo_video.id
            
        print("🔄 Создаю демонстрационные данные...")
        
        # Создаем демо-видео
        demo_video = Video(
            youtube_url="https://www.youtube.com/watch?v=DEMO123",
            title="Демо: Как приготовить идеальный торт",
            channel="Кулинарный канал",
            upload_date="2024-12-20",
            summary="В этом видео показан рецепт приготовления шоколадного торта. Рассказывается о выборе ингредиентов, температуре выпечки и секретах приготовления крема."
        )
        session.add(demo_video)
        session.commit()
        
        # Создаем демо-комментарии
        demo_comments = [
            "Отличный рецепт! Попробовал - получилось очень вкусно 👍",
            "А какую температуру духовки лучше использовать?",
            "😍😍😍",
            "Спасибо за подробное объяснение! Особенно понравилось про крем",
            "Можно ли заменить шоколад на какао-порошок?",
            "Первый раз пеку торт, получилось не очень... Что могло пойти не так?",
            "👏👏👏",
            "У меня нет миксера, можно ли взбить вручную?",
            "Сколько времени торт должен остывать?",
            "Классное видео, но музыка слишком громкая",
            "А сколько калорий в одном кусочке?",
            "Попробовала добавить орехи - стало еще вкуснее!",
            "Где купить такую форму для выпечки?",
            "Мой торт получился сухой, что делать?",
            "Спасибо! Теперь знаю как правильно взбивать белки",
            "🎂🎂🎂",
            "А можно использовать растительное масло вместо сливочного?",
            "Отличное объяснение техники! Очень помогло",
            "Когда будет следующий рецепт?",
            "Попробую на выходных, выглядит несложно"
        ]
        
        for i, text in enumerate(demo_comments, 1):
            comment = Comment(
                comment_id=f"demo_comment_{i}",
                video_id=demo_video.id,
                author=f"Пользователь{i}",
                text=text,
                likes=random.randint(0, 50),
                published_at=None,
                parent_id=None,
                comment_rank=None
            )
            session.add(comment)
            
        session.commit()
        print(f"✅ Создано демо-видео и {len(demo_comments)} комментариев")
        return demo_video.id
        
    finally:
        session.close()

def demo_ranking():
    """Демонстрирует работу системы ранжирования"""
    print("🎯 ДЕМОНСТРАЦИЯ СИСТЕМЫ РАНЖИРОВАНИЯ КОММЕНТАРИЕВ")
    print("=" * 60)
    
    # Создаем демо-данные если нужно
    demo_video_id = create_demo_data()
    
    if not demo_video_id:
        # Если не удалось создать, попробуем найти существующее
        session = get_db_session()
        try:
            demo_video = session.query(Video).filter(
                Video.youtube_url.like("%DEMO%")
            ).first()
            
            if not demo_video:
                # Используем первое доступное видео
                demo_video = session.query(Video).first()
                if not demo_video:
                    print("❌ Нет видео в базе данных для демонстрации")
                    return
                print(f"🔄 Используем существующее видео для демонстрации")
            demo_video_id = demo_video.id
        finally:
            session.close()
    
    # Получаем информацию о видео
    session = get_db_session()
    try:
        demo_video = session.query(Video).filter_by(id=demo_video_id).first()
        if not demo_video:
            print("❌ Видео не найдено")
            return
            
        print(f"\n🎬 Обрабатываем видео: {demo_video.title}")
        print(f"📝 Summary: {demo_video.summary[:100] if demo_video.summary else 'Нет summary'}...")
        
        # Показываем комментарии до ранжирования
        comments = session.query(Comment).filter_by(video_id=demo_video_id).all()
        print(f"\n📊 Всего комментариев: {len(comments)}")
        
        unranked = [c for c in comments if c.comment_rank is None]
        print(f"🔄 Не проранжировано: {len(unranked)}")
        
    finally:
        session.close()
    
    # Запускаем ранжирование
    print("\n🚀 Запускаю ранжирование с моковыми данными...")
    ranker = MockCommentRanker()
    
    success = ranker.rank_comments_for_video(demo_video_id)
    
    if success:
        print("\n🏆 Результаты ранжирования:")
        print("=" * 50)
        
        ranked_comments = ranker.get_ranked_comments(demo_video_id, min_rank=0.0)
        
        if ranked_comments:
            print(f"\n📈 Статистика:")
            ranks = [c['rank'] for c in ranked_comments]
            avg_rank = sum(ranks) / len(ranks)
            high_quality = len([r for r in ranks if r >= 0.7])
            medium_quality = len([r for r in ranks if 0.3 <= r < 0.7])
            low_quality = len([r for r in ranks if r < 0.3])
            
            print(f"Средний ранг: {avg_rank:.3f}")
            print(f"Высокое качество (≥0.7): {high_quality}")
            print(f"Среднее качество (0.3-0.7): {medium_quality}")
            print(f"Низкое качество (<0.3): {low_quality}")
            
            print(f"\n🥇 Топ-5 самых информативных комментариев:")
            for i, comment in enumerate(ranked_comments[:5], 1):
                print(f"\n{i}. Ранг: {comment['rank']:.3f} | Лайки: {comment['likes']}")
                print(f"   Автор: {comment['author']}")
                print(f"   Текст: {comment['text']}")
                
            if len(ranked_comments) >= 3:
                print(f"\n🥉 Топ-3 наименее информативных комментария:")
                for i, comment in enumerate(ranked_comments[-3:], 1):
                    print(f"\n{i}. Ранг: {comment['rank']:.3f} | Лайки: {comment['likes']}")
                    print(f"   Автор: {comment['author']}")
                    print(f"   Текст: {comment['text']}")
        else:
            print("❌ Нет проранжированных комментариев")
    
    print(f"\n✨ Демонстрация завершена!")

def main():
    """Основная функция"""
    try:
        demo_ranking()
    except KeyboardInterrupt:
        print("\n👋 Демонстрация прервана пользователем")
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 