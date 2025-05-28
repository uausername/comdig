#!/usr/bin/env python3
import os
from google import genai
from google.genai import types

def test_summary_generation():
    """Тест генерации summary через Gemini"""
    
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        print("❌ GEMINI_API_KEY не найден")
        return False
    
    print("🔍 Тест генерации summary через Gemini")
    print("=" * 50)
    
    try:
        client = genai.Client(
            api_key=api_key,
            http_options=types.HttpOptions(api_version='v1alpha')
        )
        
        # Тестовый транскрипт
        test_transcript = """
        Привет всем! Сегодня я покажу вам, как приготовить вкусную пасту карбонара.
        Для этого нам понадобятся: спагетти, яйца, бекон, сыр пармезан и черный перец.
        Сначала отварим пасту в подсоленной воде до состояния аль денте.
        Затем обжарим бекон до золотистого цвета.
        """
        
        # Промпт для генерации summary
        summary_prompt = f"""Создай краткое содержание видео на русском языке в 2-3 предложениях на основе этого транскрипта:

{test_transcript}

Краткое содержание:"""
        
        print("\n🧪 Тест генерации summary")
        try:
            response = client.models.generate_content(
                model='gemini-2.5-flash-preview-05-20',
                contents=summary_prompt,
                config=types.GenerateContentConfig(
                    temperature=0.3,
                    max_output_tokens=5000
                )
            )
            
            if response and hasattr(response, 'candidates') and response.candidates:
                candidate = response.candidates[0]
                print(f"📋 Finish reason: {candidate.finish_reason}")
                
                if candidate.content and candidate.content.parts:
                    text = candidate.content.parts[0].text
                    print(f"✅ Summary успешно создан:")
                    print(f"   {text.strip()}")
                    return True
                else:
                    print("❌ Summary: content.parts пустой")
                    print(f"📋 Candidate: {candidate}")
            else:
                print("❌ Summary: нет кандидатов")
                print(f"📋 Response: {response}")
        except Exception as e:
            print(f"❌ Summary ошибка: {e}")
        
        return False
        
    except Exception as e:
        print(f"❌ Общая ошибка: {e}")
        return False

if __name__ == "__main__":
    success = test_summary_generation()
    if success:
        print("\n🎉 Генерация summary работает!")
    else:
        print("\n❌ Проблемы с генерацией summary") 