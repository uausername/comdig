#!/usr/bin/env python3
import os
from google import genai
from google.genai import types

def test_gemini_25():
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        print("❌ GEMINI_API_KEY не найден")
        return False
    
    print("🔍 Тестирую Gemini 2.5 Flash Preview 05-20...")
    
    try:
        client = genai.Client(
            api_key=api_key,
            http_options=types.HttpOptions(api_version='v1alpha')
        )
        
        response = client.models.generate_content(
            model='gemini-2.5-flash-preview-05-20',
            contents='Ответь одним словом: тест',
            config=types.GenerateContentConfig(
                temperature=0.1,
                max_output_tokens=100
            )
        )
        
        print(f"📋 Ответ получен: {type(response)}")
        
        if response and hasattr(response, 'text') and response.text:
            print(f"✅ Модель работает! Ответ: '{response.text.strip()}'")
            return True
        elif response and hasattr(response, 'candidates') and response.candidates:
            candidate = response.candidates[0]
            print(f"📋 Finish reason: {candidate.finish_reason}")
            
            if candidate.content and candidate.content.parts:
                text = candidate.content.parts[0].text
                print(f"✅ Модель работает! Ответ: '{text.strip()}'")
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
    success = test_gemini_25()
    if success:
        print("🎉 Gemini 2.5 Flash Preview 05-20 работает!")
    else:
        print("❌ Модель не работает") 