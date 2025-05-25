#!/usr/bin/env python3
"""
Тестовый скрипт для проверки новой логики обработки транскрипта
"""

import os
import sys
from process_video import VideoProcessor

def test_transcript_logic():
    """Тестирует новую логику обработки транскрипта"""
    print("🧪 ТЕСТИРОВАНИЕ НОВОЙ ЛОГИКИ ОБРАБОТКИ ТРАНСКРИПТА")
    print("="*60)
    
    # Создаем процессор
    processor = VideoProcessor()
    
    # Тестируем функцию проверки валидности транскрипта
    print("\n1. Тестирование _is_transcript_valid():")
    
    test_cases = [
        ("Нормальный транскрипт с достаточным содержанием для анализа", True),
        ("Транскрипт недоступен для данного видео", False),
        ("Транскрипт недоступен", False),
        ("", False),
        ("Короткий", False),
        (None, False)
    ]
    
    for transcript, expected in test_cases:
        result = processor._is_transcript_valid(transcript)
        status = "✅" if result == expected else "❌"
        print(f"   {status} '{transcript}' -> {result} (ожидалось: {expected})")
    
    # Тестируем получение транскрипта для несуществующего видео
    print("\n2. Тестирование _get_transcript() с несуществующим видео:")
    fake_video_id = "FAKE_VIDEO_ID_123"
    transcript = processor._get_transcript(fake_video_id)
    print(f"   Результат: {transcript}")
    print(f"   Валидность: {processor._is_transcript_valid(transcript)}")
    
    print("\n🎯 Тестирование завершено!")

if __name__ == "__main__":
    test_transcript_logic() 