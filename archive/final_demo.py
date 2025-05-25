#!/usr/bin/env python3
"""
🚀 ФИНАЛЬНАЯ ДЕМОНСТРАЦИЯ ПРОЕКТА COMDIG
Революционная система ранжирования комментариев YouTube

Демонстрирует:
- Мега-систему ранжирования с Gemini 2.0 Flash
- Полный пайплайн обработки видео
- Интеллектуальную фильтрацию комментариев
- Аналитику и статистику
"""

import os
import sys
import time
from typing import Dict, List
from models import Video, Comment, get_db_session
from gemini_ranker import GeminiCommentRanker
from comment_ranker import CommentRanker

class FinalDemo:
    """Финальная демонстрация возможностей ComDig"""
    
    def __init__(self):
        self.session = get_db_session()
        
    def run_complete_demo(self, api_key: str = None):
        """Запускает полную демонстрацию проекта"""
        print("🚀" + "="*70)
        print("🎯 ФИНАЛЬНАЯ ДЕМОНСТРАЦИЯ ПРОЕКТА COMDIG")
        print("🏆 Революционная система ранжирования комментариев YouTube")
        print("="*72)
        
        # Проверяем наличие данных
        video = self._get_demo_video()
        if not video:
            print("❌ Нет данных для демонстрации. Сначала обработайте видео.")
            return
            
        print(f"\n📹 Демонстрационное видео: {video.title}")
        print(f"🔗 URL: {video.youtube_url}")
        print(f"📝 Summary: {video.summary[:100] if video.summary else 'Нет summary'}...")
        
        # Получаем комментарии
        comments = self._get_comments(video.id)
        print(f"\n💬 Всего комментариев: {len(comments)}")
        
        # Демонстрируем разные системы ранжирования
        self._demo_ranking_systems(video.id, api_key)
        
        # Показываем аналитику
        self._show_analytics(video.id)
        
        # Демонстрируем фильтрацию
        self._demo_filtering(video.id)
        
        print("\n🎉" + "="*70)
        print("✅ ДЕМОНСТРАЦИЯ ЗАВЕРШЕНА УСПЕШНО!")
        print("🌟 Проект готов к промышленному использованию")
        print("="*72)
    
    def _get_demo_video(self) -> Video:
        """Получает демонстрационное видео"""
        return self.session.query(Video).first()
    
    def _get_comments(self, video_id: int) -> List[Comment]:
        """Получает комментарии для видео"""
        return self.session.query(Comment).filter_by(video_id=video_id).all()
    
    def _demo_ranking_systems(self, video_id: int, api_key: str = None):
        """Демонстрирует разные системы ранжирования"""
        print("\n🤖" + "="*50)
        print("🎯 ДЕМОНСТРАЦИЯ СИСТЕМ РАНЖИРОВАНИЯ")
        print("="*52)
        
        # Сбрасываем ранжирование
        self._reset_ranking(video_id)
        
        if api_key:
            print("\n🚀 1. МЕГА-СИСТЕМА GEMINI 2.0 FLASH")
            print("-" * 40)
            self._demo_gemini_mega_ranking(video_id, api_key)
        else:
            print("\n⚠️ API ключ не предоставлен, пропускаем Gemini демо")
        
        print("\n🔧 2. FALLBACK СИСТЕМА (ЭВРИСТИКА)")
        print("-" * 40)
        self._demo_fallback_ranking(video_id)
    
    def _demo_gemini_mega_ranking(self, video_id: int, api_key: str):
        """Демонстрирует мега-систему Gemini"""
        try:
            ranker = GeminiCommentRanker(api_key=api_key, use_fallback=False)
            
            print("📡 Запускаю мега-ранжирование...")
            start_time = time.time()
            
            success = ranker.rank_comments_for_video(video_id)
            
            elapsed = time.time() - start_time
            
            if success:
                print(f"⚡ Мега-ранжирование завершено за {elapsed:.1f} секунд")
                self._show_top_comments(video_id, "Gemini Mega", 5)
            else:
                print("❌ Мега-ранжирование не удалось")
                
        except Exception as e:
            print(f"❌ Ошибка Gemini: {e}")
    
    def _demo_fallback_ranking(self, video_id: int):
        """Демонстрирует fallback систему"""
        try:
            # Сбрасываем ранжирование
            self._reset_ranking(video_id)
            
            ranker = CommentRanker(use_fallback=True)
            
            print("🔧 Запускаю эвристическое ранжирование...")
            start_time = time.time()
            
            success = ranker.rank_comments_for_video(video_id)
            
            elapsed = time.time() - start_time
            
            if success:
                print(f"✅ Эвристическое ранжирование завершено за {elapsed:.1f} секунд")
                self._show_top_comments(video_id, "Эвристика", 5)
            else:
                print("❌ Эвристическое ранжирование не удалось")
                
        except Exception as e:
            print(f"❌ Ошибка fallback: {e}")
    
    def _show_top_comments(self, video_id: int, method: str, limit: int = 5):
        """Показывает топ комментарии"""
        comments = self.session.query(Comment).filter(
            Comment.video_id == video_id,
            Comment.comment_rank.isnot(None)
        ).order_by(Comment.comment_rank.desc()).limit(limit).all()
        
        print(f"\n🏆 ТОП-{limit} КОММЕНТАРИЕВ ({method}):")
        print("-" * 50)
        
        for i, comment in enumerate(comments, 1):
            print(f"\n{i}. Ранг: {comment.comment_rank:.3f}")
            print(f"   Автор: {comment.author}")
            print(f"   Лайки: {comment.likes}")
            print(f"   Текст: {comment.text[:80]}...")
    
    def _show_analytics(self, video_id: int):
        """Показывает аналитику ранжирования"""
        print("\n📊" + "="*50)
        print("📈 АНАЛИТИКА РАНЖИРОВАНИЯ")
        print("="*52)
        
        comments = self.session.query(Comment).filter(
            Comment.video_id == video_id,
            Comment.comment_rank.isnot(None)
        ).all()
        
        if not comments:
            print("❌ Нет проранжированных комментариев")
            return
        
        ranks = [c.comment_rank for c in comments]
        
        # Базовая статистика
        total = len(ranks)
        avg_rank = sum(ranks) / total
        max_rank = max(ranks)
        min_rank = min(ranks)
        
        # Категории
        high_quality = len([r for r in ranks if r >= 0.7])
        medium_quality = len([r for r in ranks if 0.3 <= r < 0.7])
        low_quality = len([r for r in ranks if r < 0.3])
        
        print(f"📊 Общая статистика:")
        print(f"   • Всего комментариев: {total}")
        print(f"   • Средний ранг: {avg_rank:.3f}")
        print(f"   • Максимальный ранг: {max_rank:.3f}")
        print(f"   • Минимальный ранг: {min_rank:.3f}")
        
        print(f"\n🎯 Распределение по качеству:")
        print(f"   • Высокое качество (≥0.7): {high_quality} ({high_quality/total*100:.1f}%)")
        print(f"   • Среднее качество (0.3-0.7): {medium_quality} ({medium_quality/total*100:.1f}%)")
        print(f"   • Низкое качество (<0.3): {low_quality} ({low_quality/total*100:.1f}%)")
        
        # Топ авторы
        author_ranks = {}
        for comment in comments:
            if comment.author not in author_ranks:
                author_ranks[comment.author] = []
            author_ranks[comment.author].append(comment.comment_rank)
        
        top_authors = sorted(
            [(author, sum(ranks)/len(ranks), len(ranks)) 
             for author, ranks in author_ranks.items()],
            key=lambda x: x[1], reverse=True
        )[:3]
        
        print(f"\n👑 Топ-3 авторов по среднему рангу:")
        for i, (author, avg, count) in enumerate(top_authors, 1):
            print(f"   {i}. {author}: {avg:.3f} (комментариев: {count})")
    
    def _demo_filtering(self, video_id: int):
        """Демонстрирует фильтрацию комментариев"""
        print("\n🔍" + "="*50)
        print("🎯 ДЕМОНСТРАЦИЯ ИНТЕЛЛЕКТУАЛЬНОЙ ФИЛЬТРАЦИИ")
        print("="*52)
        
        thresholds = [0.8, 0.6, 0.4, 0.2]
        
        for threshold in thresholds:
            comments = self.session.query(Comment).filter(
                Comment.video_id == video_id,
                Comment.comment_rank >= threshold
            ).count()
            
            print(f"📈 Комментарии с рангом ≥ {threshold}: {comments}")
        
        # Показываем примеры фильтрации
        print(f"\n💎 ПРЕМИУМ КОММЕНТАРИИ (ранг ≥ 0.8):")
        premium_comments = self.session.query(Comment).filter(
            Comment.video_id == video_id,
            Comment.comment_rank >= 0.8
        ).limit(3).all()
        
        for comment in premium_comments:
            print(f"   • {comment.text[:60]}... (ранг: {comment.comment_rank:.3f})")
    
    def _reset_ranking(self, video_id: int):
        """Сбрасывает ранжирование для демонстрации"""
        self.session.query(Comment).filter_by(video_id=video_id).update({'comment_rank': None})
        self.session.commit()
    
    def __del__(self):
        """Закрываем сессию"""
        if hasattr(self, 'session'):
            self.session.close()


def main():
    """Основная функция демонстрации"""
    print("🎬 Запуск финальной демонстрации ComDig...")
    
    # Получаем API ключ из аргументов
    api_key = None
    for arg in sys.argv:
        if arg.startswith("--api-key="):
            api_key = arg.split("=", 1)[1]
            break
    
    if not api_key:
        api_key = os.getenv('GEMINI_API_KEY')
    
    if not api_key:
        print("⚠️ API ключ Gemini не предоставлен. Демонстрация будет ограничена.")
        print("💡 Используйте: python final_demo.py --api-key=YOUR_KEY")
    
    try:
        demo = FinalDemo()
        demo.run_complete_demo(api_key)
        
    except KeyboardInterrupt:
        print("\n\n⏹️ Демонстрация прервана пользователем")
    except Exception as e:
        print(f"\n❌ Ошибка демонстрации: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main() 