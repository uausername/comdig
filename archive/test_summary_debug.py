#!/usr/bin/env python3
import os
from google import genai
from google.genai import types

def test_summary_debug():
    """Детальная диагностика генерации summary"""
    
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        print("❌ GEMINI_API_KEY не найден")
        return False
    
    print("🔍 Детальная диагностика генерации summary")
    print("=" * 60)
    
    try:
        client = genai.Client(
            api_key=api_key,
            http_options=types.HttpOptions(api_version='v1alpha')
        )
        
        # Тестовый транскрипт (украинский)
        test_transcript = """Одна з найсмачніших взагалі українських кухонь в Києві. Бебі восьмижок. Його я їсти не буду. Його ми відпустимо назад у річку. Феноменальний ресторан. Дуже смачна українська кухня. Тут готують борщ, вареники, котлети по-київськи."""
        
        # Промпт для генерации summary (как в process_video.py)
        prompt = f"""Создай краткое содержание (summary) этого видео на основе транскрипта.
                    
Требования:
- Длина: 20-30 предложений
- Язык: English
- Основные темы и ключевые моменты
- Четкий и информативный стиль

Транскрипт:
{test_transcript}...

Summary:"""
        
        print(f"📝 Длина промпта: {len(prompt)} символов")
        print(f"📝 Примерное количество токенов: ~{len(prompt.split())}")
        
        # Тест с разными лимитами токенов
        for max_tokens in [200, 500, 1000, 2000]:
            print(f"\n🧪 Тест с max_output_tokens={max_tokens}")
            try:
                response = client.models.generate_content(
                    model='gemini-2.5-flash-preview-05-20',
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        temperature=0.3,
                        max_output_tokens=max_tokens,
                        top_p=0.8
                    )
                )
                
                if response and response.text:
                    print(f"✅ Успех! Длина ответа: {len(response.text)} символов")
                    print(f"📄 Ответ: {response.text[:100]}...")
                    return True
                elif response and hasattr(response, 'candidates') and response.candidates:
                    candidate = response.candidates[0]
                    print(f"📋 Finish reason: {candidate.finish_reason}")
                    if candidate.content and candidate.content.parts:
                        text = candidate.content.parts[0].text
                        print(f"✅ Успех! Длина ответа: {len(text)} символов")
                        print(f"📄 Ответ: {text[:100]}...")
                        return True
                    else:
                        print("❌ Контент пустой")
                else:
                    print("❌ Нет ответа")
                    
            except Exception as e:
                print(f"❌ Ошибка с {max_tokens} токенами: {e}")
        
        return False
        
    except Exception as e:
        print(f"❌ Общая ошибка: {e}")
        return False

if __name__ == "__main__":
    success = test_summary_debug()
    if success:
        print("\n🎉 Gemini API работает для генерации summary!")
    else:
        print("\n❌ Проблемы с генерацией summary через Gemini API") 