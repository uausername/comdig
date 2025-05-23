#!/usr/bin/env python3
"""
Тестовый скрипт для демонстрации системы ранжирования комментариев
"""

from models import get_db_session, Video, Comment
from comment_ranker import CommentRanker
import json

def show_video_stats():
    """Показывает статистику по видео в базе данных"""
    session = get_db_session()
    try:
        videos = session.query(Video).all()
        print("📊 Статистика видео в базе данных:")
        print("=" * 50)
        
        for video in videos:
            comments_count = session.query(Comment).filter_by(video_id=video.id).count()
            ranked_count = session.query(Comment).filter(
                Comment.video_id == video.id,
                Comment.rank.isnot(None)
            ).count()
            
            print(f"\n🎬 Видео ID: {video.id}")
            print(f"   URL: {video.youtube_url}")
            print(f"   Комментариев: {comments_count}")
            print(f"   Проранжировано: {ranked_count}")
            print(f"   Есть summary: {'✅' if video.summary else '❌'}")
            
    finally:
        session.close()

def show_top_comments(video_id: int, limit: int = 5):
    """Показывает топ комментарии для видео"""
    ranker = CommentRanker()
    comments = ranker.get_ranked_comments(video_id, min_rank=0.0)
    
    if not comments:
        print(f"❌ Нет проранжированных комментариев для видео {video_id}")
        return
    
    print(f"\n🏆 Топ-{limit} комментариев для видео {video_id}:")
    print("=" * 60)
    
    for i, comment in enumerate(comments[:limit], 1):
        print(f"\n{i}. Ранг: {comment['rank']:.3f} | Лайки: {comment['likes']}")
        print(f"   Автор: {comment['author']}")
        print(f"   Текст: {comment['text'][:200]}...")
        if len(comment['text']) > 200:
            print("   [...]")

def analyze_ranking_distribution(video_id: int):
    """Анализирует распределение рангов"""
    session = get_db_session()
    try:
        comments = session.query(Comment).filter(
            Comment.video_id == video_id,
            Comment.rank.isnot(None)
        ).all()
        
        if not comments:
            print(f"❌ Нет проранжированных комментариев для видео {video_id}")
            return
        
        ranks = [c.rank for c in comments]
        
        # Статистика
        total = len(ranks)
        avg_rank = sum(ranks) / total
        high_quality = len([r for r in ranks if r >= 0.7])
        medium_quality = len([r for r in ranks if 0.3 <= r < 0.7])
        low_quality = len([r for r in ranks if r < 0.3])
        
        print(f"\n📈 Анализ рангов для видео {video_id}:")
        print("=" * 40)
        print(f"Всего комментариев: {total}")
        print(f"Средний ранг: {avg_rank:.3f}")
        print(f"Высокое качество (≥0.7): {high_quality} ({high_quality/total*100:.1f}%)")
        print(f"Среднее качество (0.3-0.7): {medium_quality} ({medium_quality/total*100:.1f}%)")
        print(f"Низкое качество (<0.3): {low_quality} ({low_quality/total*100:.1f}%)")
        
        # Топ и худшие комментарии
        sorted_comments = sorted(comments, key=lambda x: x.rank, reverse=True)
        
        print(f"\n🥇 Лучший комментарий (ранг: {sorted_comments[0].rank:.3f}):")
        print(f"   {sorted_comments[0].text[:150]}...")
        
        print(f"\n🥉 Худший комментарий (ранг: {sorted_comments[-1].rank:.3f}):")
        print(f"   {sorted_comments[-1].text[:150]}...")
        
    finally:
        session.close()

def export_ranked_comments(video_id: int, filename: str = "ranked_comments.json"):
    """Экспортирует проранжированные комментарии в JSON"""
    ranker = CommentRanker()
    comments = ranker.get_ranked_comments(video_id, min_rank=0.0)
    
    if not comments:
        print(f"❌ Нет проранжированных комментариев для видео {video_id}")
        return
    
    # Добавляем метаданные
    export_data = {
        "video_id": video_id,
        "total_comments": len(comments),
        "export_timestamp": "2024-12-20",
        "comments": comments
    }
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(export_data, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Экспортировано {len(comments)} комментариев в {filename}")

def main():
    """Основная функция для демонстрации"""
    print("🎯 ДЕМОНСТРАЦИЯ СИСТЕМЫ РАНЖИРОВАНИЯ КОММЕНТАРИЕВ")
    print("=" * 60)
    
    # Показываем статистику
    show_video_stats()
    
    # Запрашиваем ID видео для анализа
    try:
        video_id = input("\n🔍 Введите ID видео для анализа (или Enter для выхода): ").strip()
        
        if not video_id:
            print("👋 До свидания!")
            return
            
        video_id = int(video_id)
        
        # Показываем топ комментарии
        show_top_comments(video_id, limit=5)
        
        # Анализируем распределение
        analyze_ranking_distribution(video_id)
        
        # Предлагаем экспорт
        export_choice = input("\n💾 Экспортировать комментарии в JSON? (y/n): ").strip().lower()
        if export_choice == 'y':
            filename = f"ranked_comments_video_{video_id}.json"
            export_ranked_comments(video_id, filename)
        
    except ValueError:
        print("❌ Неверный формат ID видео")
    except KeyboardInterrupt:
        print("\n👋 Прервано пользователем")
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    main() 