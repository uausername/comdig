#!/usr/bin/env python3
"""
Тестовый скрипт для проверки работы Gemini 2.5 Flash Preview 05-20
"""

import os
import sys

def test_gemini_25():
    """Тестирует доступность и работу Gemini 2.5 Flash Preview 05-20"""
    
    print("🔍 Тестирование Gemini 2.5 Flash Preview 05-20")
    print("=" * 50)
    
    # Проверяем API ключ
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        print("❌ GEMINI_API_KEY не найден в переменных окружения")
        return False
    
    print(f"✅ API ключ найден: {api_key[:10]}...")
    
    try:
        # Импортируем библиотеки
        print("📦 Импортирую библиотеки...")
        from google import genai
        from google.genai import types
        print("✅ Библиотеки импортированы успешно")
        
        # Создаем клиент
        print("🔧 Создаю клиент с v1alpha API...")
        client = genai.Client(
            api_key=api_key,
            http_options=types.HttpOptions(api_version='v1alpha')
        )
        print("✅ Клиент создан успешно")
        
        # Тестовый запрос
        print("🚀 Отправляю тестовый запрос...")
        
                 response = client.models.generate_content(
             model='gemini-2.5-flash-preview-05-20',
             contents='Ответь одним словом: тест',
                          config=types.GenerateContentConfig(
                 temperature=0.1,
                 max_output_tokens=50,
                 top_p=0.8,
                 top_k=40
             )
         )
        
        print("📨 Запрос отправлен, обрабатываю ответ...")
        
                 # Проверяем ответ
         if response:
             print(f"📋 Тип ответа: {type(response)}")
             
             # Проверяем прямой доступ к тексту
             if hasattr(response, 'text') and response.text:
                 print(f"✅ Модель работает! Ответ: '{response.text.strip()}'")
                 print("🎉 Gemini 2.5 Flash Preview 05-20 полностью функциональна!")
                 return True
             
             # Проверяем кандидатов
             elif hasattr(response, 'candidates') and response.candidates:
                 candidate = response.candidates[0]
                 print(f"📋 Finish reason: {candidate.finish_reason}")
                 
                 if candidate.content and candidate.content.parts:
                     text = candidate.content.parts[0].text
                     print(f"✅ Модель работает! Ответ: '{text.strip()}'")
                     print("🎉 Gemini 2.5 Flash Preview 05-20 полностью функциональна!")
                     return True
                 else:
                     print("❌ Контент пустой или parts=None")
                     if candidate.finish_reason == 'MAX_TOKENS':
                         print("💡 Причина: Достигнут лимит токенов, увеличьте max_output_tokens")
                     return False
             else:
                 print("❌ Ответ получен, но текст пустой")
                 print(f"📋 Полный ответ: {response}")
                 return False
         else:
             print("❌ Ответ не получен (None)")
             return False
            
    except Exception as e:
        print(f"❌ Ошибка при тестировании: {e}")
        print(f"📋 Тип ошибки: {type(e)}")
        
        # Дополнительная диагностика
        if "404" in str(e):
            print("🔍 Ошибка 404: Модель не найдена")
            print("💡 Возможные причины:")
            print("   - Неправильное название модели")
            print("   - Модель недоступна в v1alpha API")
            print("   - Модель требует специального доступа")
        elif "403" in str(e):
            print("🔍 Ошибка 403: Доступ запрещен")
            print("💡 Возможные причины:")
            print("   - Неверный API ключ")
            print("   - Нет доступа к preview модели")
        elif "429" in str(e):
            print("🔍 Ошибка 429: Превышен лимит запросов")
        
        return False

def test_fallback_model():
    """Тестирует работу с предыдущей моделью для сравнения"""
    
    print("\n🔄 Тестирование предыдущей модели для сравнения...")
    print("=" * 50)
    
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        print("❌ GEMINI_API_KEY не найден")
        return False
    
    try:
        from google import genai
        from google.genai import types
        
        client = genai.Client(
            api_key=api_key,
            http_options=types.HttpOptions(api_version='v1alpha')
        )
        
        # Тестируем предыдущую модель
        response = client.models.generate_content(
            model='gemini-2.0-flash-preview-05-20',
            contents='Ответь одним словом: тест',
            config=types.GenerateContentConfig(
                temperature=0.1,
                max_output_tokens=10
            )
        )
        
        if response and response.text:
            print(f"✅ Предыдущая модель работает! Ответ: '{response.text.strip()}'")
            return True
        else:
            print("❌ Предыдущая модель тоже не отвечает")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка с предыдущей моделью: {e}")
        return False

if __name__ == "__main__":
    print("🧪 ДИАГНОСТИКА GEMINI 2.5 FLASH PREVIEW 05-20")
    print("=" * 60)
    
    # Тестируем новую модель
    success = test_gemini_25()
    
    if not success:
        # Если новая модель не работает, тестируем предыдущую
        fallback_success = test_fallback_model()
        
        if fallback_success:
            print("\n💡 РЕКОМЕНДАЦИЯ: Предыдущая модель работает, новая - нет")
            print("   Возможно, новая модель еще недоступна или требует специального доступа")
        else:
            print("\n❌ ПРОБЛЕМА: Обе модели не работают")
            print("   Проверьте API ключ и подключение к интернету")
    
    print("\n" + "=" * 60)
    print("🏁 Тестирование завершено") 