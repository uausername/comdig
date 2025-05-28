#!/usr/bin/env python3
import os
from google import genai
from google.genai import types
from sqlalchemy.orm import Session
from models import Video, Comment, get_db_session

def debug_real_prompt():
    """Отладка реального промпта ранжирования"""
    
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        print("❌ GEMINI_API_KEY не найден")
        return False
    
    print("🔍 Отладка реального промпта ранжирования")
    print("=" * 60)
    
    # Получаем реальные данные из БД
    session = get_db_session()
    try:
        video = session.query(Video).filter_by(id=13).first()
        if not video:
            print("❌ Видео с ID 13 не найдено")
            return False
        
        comments = session.query(Comment).filter_by(video_id=13).limit(3).all()
        if not comments:
            print("❌ Комментарии не найдены")
            return False
        
        print(f"📹 Видео: {video.title}")
        print(f"📝 Summary длина: {len(video.summary) if video.summary else 0} символов")
        print(f"💬 Комментариев для теста: {len(comments)}")
        
        # Создаем реальный промпт
        comments_text = ""
        for i, comment in enumerate(comments, 1):
            comment_preview = comment.text[:300] + "..." if len(comment.text) > 300 else comment.text
            comments_text += f"{i}. {comment_preview}\n"
        
        real_prompt = f"""Rate the informativeness of these comments relative to the video content on a binary scale: either 0.0 or 1.0.

Video content: {video.summary}

Comments ({len(comments)} total):
{comments_text}


**Rating Criteria:**

*   **1.0: Significant and Valuable Comment**
    *   Assign this rating to comments that are highly informative and directly relevant to the video's topic.
    *   These comments add significant value by:
        *   Contributing meaningfully to the discussion.
        *   Offering a new perspective, viewpoint, or insight on the subject.
        *   Posing new, relevant questions that stimulate further thought or discussion.
    *   Choose only comments that truly enhance the understanding or dialogue around the video's topic.

*   **0.0: Insignificant or Unrelated Comment**
    *   Assign this rating to comments that do *not* meet the criteria for a 1.0 rating.
    *   This includes comments that are:
        *   Unrelated to the video (e.g., spam, off-topic discussions).
        *   Only weakly or partially related to the video's topic without adding substantive value.
        *   Insignificant, such as those that:
            *   Simply praise or criticize the author or channel without adding to the topic (e.g., "Great video!", "Love your channel!", "Didn't like it").
            *   Only express a simple emotion without further substance of the topic (e.g., "Wow!", "Haha", "Sad", "Will watch again").
            *   Add nothing new, insightful, or questioning to the discussion of the topic.
    *   Essentially, ignore comments that are trivial or do not contribute to the topic at hand.

Respond with EXACTLY {len(comments)} ratings separated by commas.
Ratings:"""
        
        print(f"\n📏 Длина промпта: {len(real_prompt)} символов")
        print(f"📏 Примерное количество токенов: ~{len(real_prompt.split())}")
        
        # Показываем начало промпта
        print(f"\n📄 Начало промпта:")
        print(real_prompt[:500] + "..." if len(real_prompt) > 500 else real_prompt)
        
        # Тестируем реальный промпт
        client = genai.Client(
            api_key=api_key,
            http_options=types.HttpOptions(api_version='v1alpha')
        )
        
        print("\n🧪 Тест реального промпта")
        try:
            response = client.models.generate_content(
                model='gemini-2.5-flash-preview-05-20',
                contents=real_prompt,
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
                    print(f"✅ Реальный промпт успешен: '{text.strip()}'")
                    return True
                else:
                    print("❌ Реальный промпт: content.parts пустой")
                    print(f"📋 Candidate: {candidate}")
            else:
                print("❌ Реальный промпт: нет кандидатов")
                print(f"📋 Response: {response}")
        except Exception as e:
            print(f"❌ Реальный промпт ошибка: {e}")
        
        return False
        
    finally:
        session.close()

if __name__ == "__main__":
    success = debug_real_prompt()
    if success:
        print("\n🎉 Реальный промпт работает!")
    else:
        print("\n❌ Проблемы с реальным промптом") 