#!/usr/bin/env python3
import os
from google import genai
from google.genai import types

def test_gemini_25_debug():
    """Отладочный тест для диагностики проблем с Gemini 2.5"""
    
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        print("❌ GEMINI_API_KEY не найден")
        return False
    
    print("🔍 Отладочный тест Gemini 2.5 Flash Preview 05-20")
    print("=" * 60)
    
    try:
        client = genai.Client(
            api_key=api_key,
            http_options=types.HttpOptions(api_version='v1alpha')
        )
        
        # Тест 1: Очень большой лимит токенов
        print("\n🧪 Тест 1: Очень большой лимит токенов (10000)")
        try:
            response = client.models.generate_content(
                model='gemini-2.5-flash-preview-05-20',
                contents='Hi',
                config=types.GenerateContentConfig(
                    temperature=0.1,
                    max_output_tokens=10000
                )
            )
            
            print(f"📋 Response type: {type(response)}")
            if response and hasattr(response, 'candidates') and response.candidates:
                candidate = response.candidates[0]
                print(f"📋 Finish reason: {candidate.finish_reason}")
                print(f"📋 Content: {candidate.content}")
                
                if candidate.content and candidate.content.parts:
                    text = candidate.content.parts[0].text
                    print(f"✅ Тест 1 успешен: '{text}'")
                else:
                    print("❌ Тест 1: content.parts пустой")
            else:
                print("❌ Тест 1: нет кандидатов")
        except Exception as e:
            print(f"❌ Тест 1 ошибка: {e}")
        
        # Тест 2: Без ограничений токенов
        print("\n🧪 Тест 2: Без ограничений токенов")
        try:
            response = client.models.generate_content(
                model='gemini-2.5-flash-preview-05-20',
                contents='Hello'
            )
            
            if response and hasattr(response, 'candidates') and response.candidates:
                candidate = response.candidates[0]
                print(f"📋 Finish reason: {candidate.finish_reason}")
                
                if candidate.content and candidate.content.parts:
                    text = candidate.content.parts[0].text
                    print(f"✅ Тест 2 успешен: '{text}'")
                else:
                    print("❌ Тест 2: content.parts пустой")
            else:
                print("❌ Тест 2: нет кандидатов")
        except Exception as e:
            print(f"❌ Тест 2 ошибка: {e}")
        
        # Тест 3: Минимальные настройки
        print("\n🧪 Тест 3: Минимальные настройки")
        try:
            response = client.models.generate_content(
                model='gemini-2.5-flash-preview-05-20',
                contents='Test',
                config=types.GenerateContentConfig(
                    temperature=0.0,
                    max_output_tokens=65536  # Максимум для модели
                )
            )
            
            if response and hasattr(response, 'candidates') and response.candidates:
                candidate = response.candidates[0]
                print(f"📋 Finish reason: {candidate.finish_reason}")
                
                if candidate.content and candidate.content.parts:
                    text = candidate.content.parts[0].text
                    print(f"✅ Тест 3 успешен: '{text}'")
                    return True
                else:
                    print("❌ Тест 3: content.parts пустой")
            else:
                print("❌ Тест 3: нет кандидатов")
        except Exception as e:
            print(f"❌ Тест 3 ошибка: {e}")
        
        # Тест 4: Проверим доступные модели
        print("\n🧪 Тест 4: Проверка доступных моделей")
        try:
            models = client.models.list()
            gemini_models = [m for m in models if 'gemini' in m.name.lower()]
            print(f"📋 Найдено Gemini моделей: {len(gemini_models)}")
            for model in gemini_models:
                print(f"   - {model.name}")
                if '2.5' in model.name:
                    print(f"     ✅ Gemini 2.5 модель найдена!")
        except Exception as e:
            print(f"❌ Тест 4 ошибка: {e}")
        
        return False
        
    except Exception as e:
        print(f"❌ Общая ошибка: {e}")
        return False

if __name__ == "__main__":
    success = test_gemini_25_debug()
    if success:
        print("\n🎉 Gemini 2.5 Flash Preview 05-20 работает!")
    else:
        print("\n❌ Проблемы с моделью требуют дальнейшего исследования") 