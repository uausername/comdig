#!/usr/bin/env python3
"""
Скрипт для проверки содержимого JSON файла
"""

import json

def check_json():
    """Проверяет содержимое JSON файла"""
    print("📄 Проверяю содержимое comments.json...")
    
    try:
        with open('comments.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"📊 Всего комментариев: {len(data)}")
        
        # Проверяем первые 3 комментария
        print("\n🔍 Первые 3 комментария:")
        for i, comment in enumerate(data[:3]):
            print(f"\n{i+1}. Comment ID: {comment.get('comment_id')}")
            print(f"   Comment URL: {comment.get('comment_url')}")
            print(f"   Author: {comment.get('author')}")
            print(f"   Text: {comment.get('text', '')[:50]}...")
        
        # Статистика по comment_id
        with_id = sum(1 for c in data if c.get('comment_id'))
        without_id = len(data) - with_id
        
        print(f"\n📈 Статистика:")
        print(f"   С comment_id: {with_id}")
        print(f"   Без comment_id: {without_id}")
        print(f"   Процент с ID: {with_id/len(data)*100:.1f}%")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    check_json() 