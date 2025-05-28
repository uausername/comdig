#!/usr/bin/env python3
import os
from google import genai
from google.genai import types

def test_gemini_25_fixed():
    """Финальный тест Gemini 2.5 с фиксированными данными"""
    
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        print("❌ GEMINI_API_KEY не найден")
        return False
    
    print("🔍 Финальный тест Gemini 2.5 Flash Preview 05-20")
    print("=" * 60)
    
    try:
        client = genai.Client(
            api_key=api_key,
            http_options=types.HttpOptions(api_version='v1alpha')
        )
        
        # Тест 1: Минимальный промпт
        print("\n🧪 Тест 1: Минимальный промпт")
        try:
            response = client.models.generate_content(
                model='gemini-2.5-flash-preview-05-20',
                contents='Hi there!',
                config=types.GenerateContentConfig(
                    temperature=0.1,
                    max_output_tokens=1000
                )
            )
            
            if response and response.text:
                print(f"✅ Тест 1: '{response.text.strip()}'")
            else:
                print("❌ Тест 1: Нет ответа")
                return False
        except Exception as e:
            print(f"❌ Тест 1 ошибка: {e}")
            return False
        
        # Тест 2: Простой вопрос
        print("\n🧪 Тест 2: Простой вопрос")
        try:
            response = client.models.generate_content(
                model='gemini-2.5-flash-preview-05-20',
                contents='What is 2+2?',
                config=types.GenerateContentConfig(
                    temperature=0.1,
                    max_output_tokens=1000
                )
            )
            
            if response and response.text:
                print(f"✅ Тест 2: '{response.text.strip()}'")
            else:
                print("❌ Тест 2: Нет ответа")
                return False
        except Exception as e:
            print(f"❌ Тест 2 ошибка: {e}")
            return False
        
        # Тест 3: Базовые настройки
        print("\n🧪 Тест 3: Базовые настройки")
        try:
            response = client.models.generate_content(
                model='gemini-2.5-flash-preview-05-20',
                contents='How are you doing today?'
            )
            
            if response and response.text:
                print(f"✅ Тест 3: '{response.text.strip()}'")
                return True
            else:
                print("❌ Тест 3: Нет ответа")
                return False
        except Exception as e:
            print(f"❌ Тест 3 ошибка: {e}")
            return False
        
    except Exception as e:
        print(f"❌ Общая ошибка: {e}")
        return False

if __name__ == "__main__":
    success = test_gemini_25_fixed()
    if success:
        print("\n🎉 Gemini 2.5 Flash Preview 05-20 работает корректно!")
        print("✅ Все базовые тесты пройдены")
        print("✅ Модель готова к использованию")
    else:
        print("\n❌ Проблемы с Gemini 2.5 Flash Preview 05-20") 