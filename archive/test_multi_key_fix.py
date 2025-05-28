#!/usr/bin/env python3
"""
Тест исправлений в мультиключевой системе ранжирования
"""

import os
from google import genai
from google.genai import types

def test_simple_ranking():
    """Тест простого ранжирования одного комментария"""
    
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        print("❌ GEMINI_API_KEY не найден")
        return False
    
    print("🔍 Тест простого ранжирования")
    print("=" * 50)
    
    try:
        client = genai.Client(
            api_key=api_key,
            http_options=types.HttpOptions(api_version='v1alpha')
        )
        
        # Простой промпт ранжирования
        prompt = """Rate this comment on a binary scale: either 0.0 or 1.0.

Video content: This video shows how to use cannabis products safely.

Comment: "@sports1226 there's only 10mg in the honey stick..."

Respond with only a number either 0.0 or 1.0:"""
        
        print("🧪 Отправляю простой запрос...")
        
        response = client.models.generate_content(
            model='gemini-2.5-flash-preview-05-20',
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.1,
                max_output_tokens=1000,
                top_p=0.8
            )
        )
        
        print(f"📋 Тип ответа: {type(response)}")
        
        # Проверяем прямой доступ к тексту
        if hasattr(response, 'text') and response.text:
            print(f"✅ Прямой текст: '{response.text.strip()}'")
            return True
        
        # Проверяем кандидатов
        elif hasattr(response, 'candidates') and response.candidates:
            candidate = response.candidates[0]
            print(f"📋 Finish reason: {candidate.finish_reason}")
            
            if candidate.content and candidate.content.parts and candidate.content.parts[0].text:
                text = candidate.content.parts[0].text
                print(f"✅ Текст из кандидата: '{text.strip()}'")
                return True
            else:
                print("❌ Пустой контент в кандидате")
                return False
        else:
            print("❌ Нет ответа")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False

def test_batch_ranking():
    """Тест батчевого ранжирования"""
    
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        print("❌ GEMINI_API_KEY не найден")
        return False
    
    print("\n🔍 Тест батчевого ранжирования")
    print("=" * 50)
    
    try:
        client = genai.Client(
            api_key=api_key,
            http_options=types.HttpOptions(api_version='v1alpha')
        )
        
        # Батчевый промпт
        prompt = """Rate the informativeness of these comments relative to the video content on a binary scale: either 0.0 or 1.0.

Video content: This video shows how to use cannabis products safely.

Comments (3 total):
1. @sports1226 there's only 10mg in the honey stick...
2. THat's correct about 3!...
3. 5mg if you don't have a tolerance....

Respond with EXACTLY 3 ratings separated by commas.
Ratings:"""
        
        print("🧪 Отправляю батчевый запрос...")
        
        response = client.models.generate_content(
            model='gemini-2.5-flash-preview-05-20',
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.1,
                max_output_tokens=1000,
                top_p=0.8
            )
        )
        
        print(f"📋 Тип ответа: {type(response)}")
        
        # Проверяем прямой доступ к тексту
        if hasattr(response, 'text') and response.text:
            print(f"✅ Прямой текст: '{response.text.strip()}'")
            return True
        
        # Проверяем кандидатов
        elif hasattr(response, 'candidates') and response.candidates:
            candidate = response.candidates[0]
            print(f"📋 Finish reason: {candidate.finish_reason}")
            
            if candidate.content and candidate.content.parts and candidate.content.parts[0].text:
                text = candidate.content.parts[0].text
                print(f"✅ Текст из кандидата: '{text.strip()}'")
                return True
            else:
                print("❌ Пустой контент в кандидате")
                return False
        else:
            print("❌ Нет ответа")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False

if __name__ == "__main__":
    print("🚀 ТЕСТ ИСПРАВЛЕНИЙ МУЛЬТИКЛЮЧЕВОЙ СИСТЕМЫ")
    print("=" * 60)
    
    success1 = test_simple_ranking()
    success2 = test_batch_ranking()
    
    if success1 and success2:
        print("\n🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ!")
        print("✅ Исправления работают корректно")
    else:
        print("\n❌ НЕКОТОРЫЕ ТЕСТЫ НЕ ПРОЙДЕНЫ")
        print("⚠️ Требуется дополнительная диагностика") 