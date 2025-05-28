#!/usr/bin/env python3
from process_video import VideoProcessor
import os

def test_summary_fix():
    """Тестирует исправление генерации summary"""
    
    print("🔍 Тест исправления генерации summary")
    print("=" * 50)
    
    processor = VideoProcessor(os.getenv('GEMINI_API_KEY'))
    video_id = '3TMWNkgbJL0'
    
    # Получаем транскрипт
    print("📝 Получение транскрипта...")
    transcript = processor._get_transcript(video_id)
    
    if transcript:
        print(f"✅ Транскрипт получен: {len(transcript)} символов")
        print(f"📋 Валидный: {processor._is_transcript_valid(transcript)}")
        
        # Генерируем summary
        print("\n🤖 Генерация summary...")
        summary = processor._generate_summary(transcript)
        
        if summary:
            is_gemini = "fallback" not in summary.lower()
            print(f"✅ Summary создан: {len(summary)} символов")
            print(f"🤖 Через Gemini API: {is_gemini}")
            if is_gemini:
                print(f"📄 Summary: {summary[:200]}...")
            else:
                print("⚠️ Используется fallback summary")
        else:
            print("❌ Summary не создан")
    else:
        print("❌ Транскрипт не получен")

if __name__ == "__main__":
    test_summary_fix() 