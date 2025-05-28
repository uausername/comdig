#!/usr/bin/env python3
import os
from google import genai
from google.genai import types

def test_gemini_25_quick():
    """Быстрый тест Gemini 2.5 Flash Preview 05-20 с правильными настройками"""
    
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        print("❌ GEMINI_API_KEY не найден")
        return False
    
    print("🔍 Быстрый тест Gemini 2.5 Flash Preview 05-20")
    print("=" * 50)
    
    try:
        client = genai.Client(
            api_key=api_key,
            http_options=types.HttpOptions(api_version='v1alpha')
        )
        
        # Тест с увеличенным лимитом токенов
        print("\n🧪 Тест с увеличенным лимитом токенов (1000)")
        response = client.models.generate_content(
            model='gemini-2.5-flash-preview-05-20',
            contents='Rate this comment on a scale 0.0 to 1.0: "This is a great video!"',
            config=types.GenerateContentConfig(
                temperature=0.1,
                max_output_tokens=1000  # Увеличенный лимит
            )
        )
        
        if response and response.text:
            print(f"✅ Успех! Ответ: '{response.text.strip()}'")
            return True
        elif response and hasattr(response, 'candidates') and response.candidates:
            candidate = response.candidates[0]
            print(f"📋 Finish reason: {candidate.finish_reason}")
            
            if candidate.content and candidate.content.parts:
                text = candidate.content.parts[0].text
                print(f"✅ Успех! Ответ: '{text.strip()}'")
                return True
            else:
                print("❌ Контент пустой")
                return False
        else:
            print("❌ Нет ответа")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False

if __name__ == "__main__":
    success = test_gemini_25_quick()
    if success:
        print("\n🎉 Gemini 2.5 Flash Preview 05-20 работает с новыми настройками!")
    else:
        print("\n❌ Проблемы с моделью обнаружены") 