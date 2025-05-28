#!/usr/bin/env python3
import os
from google import genai
from google.genai import types

def test_ranking_prompt():
    """Тест промпта ранжирования комментариев"""
    
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        print("❌ GEMINI_API_KEY не найден")
        return False
    
    print("🔍 Тест промпта ранжирования комментариев")
    print("=" * 50)
    
    try:
        client = genai.Client(
            api_key=api_key,
            http_options=types.HttpOptions(api_version='v1alpha')
        )
        
        # Простой промпт ранжирования
        simple_prompt = """Rate this comment on a binary scale: either 0.0 or 1.0.

Video content: This video shows how to cook pasta.

Comment: "Great recipe! I tried it and it worked perfectly."

Respond with only a number either 0.0 or 1.0:"""
        
        print("\n🧪 Тест простого промпта ранжирования")
        try:
            response = client.models.generate_content(
                model='gemini-2.5-flash-preview-05-20',
                contents=simple_prompt,
                config=types.GenerateContentConfig(
                    temperature=0.1,
                    max_output_tokens=10000
                )
            )
            
            if response and hasattr(response, 'candidates') and response.candidates:
                candidate = response.candidates[0]
                print(f"📋 Finish reason: {candidate.finish_reason}")
                
                if candidate.content and candidate.content.parts:
                    text = candidate.content.parts[0].text
                    print(f"✅ Простой промпт успешен: '{text.strip()}'")
                else:
                    print("❌ Простой промпт: content.parts пустой")
            else:
                print("❌ Простой промпт: нет кандидатов")
        except Exception as e:
            print(f"❌ Простой промпт ошибка: {e}")
        
        # Батчевый промпт ранжирования
        batch_prompt = """Rate the informativeness of these comments relative to the video content on a binary scale: either 0.0 or 1.0.

Video content: This video shows how to cook pasta.

Comments (3 total):
1. Great recipe! I tried it and it worked perfectly.
2. First!
3. What temperature should the water be?

Respond with EXACTLY 3 ratings separated by commas.
Ratings:"""
        
        print("\n🧪 Тест батчевого промпта ранжирования")
        try:
            response = client.models.generate_content(
                model='gemini-2.5-flash-preview-05-20',
                contents=batch_prompt,
                config=types.GenerateContentConfig(
                    temperature=0.1,
                    max_output_tokens=10000
                )
            )
            
            if response and hasattr(response, 'candidates') and response.candidates:
                candidate = response.candidates[0]
                print(f"📋 Finish reason: {candidate.finish_reason}")
                
                if candidate.content and candidate.content.parts:
                    text = candidate.content.parts[0].text
                    print(f"✅ Батчевый промпт успешен: '{text.strip()}'")
                    return True
                else:
                    print("❌ Батчевый промпт: content.parts пустой")
            else:
                print("❌ Батчевый промпт: нет кандидатов")
        except Exception as e:
            print(f"❌ Батчевый промпт ошибка: {e}")
        
        return False
        
    except Exception as e:
        print(f"❌ Общая ошибка: {e}")
        return False

if __name__ == "__main__":
    success = test_ranking_prompt()
    if success:
        print("\n🎉 Промпты ранжирования работают!")
    else:
        print("\n❌ Проблемы с промптами ранжирования") 