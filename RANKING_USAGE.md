# Руководство по использованию системы ранжирования комментариев

## 🎯 Обзор

Система ранжирования комментариев анализирует информативность комментариев YouTube относительно содержания видео и присваивает им оценки от 0.0 до 1.0.

## 🚀 Быстрый старт

### 1. Полный пайплайн обработки видео

```bash
# Запуск Docker-контейнеров
docker-compose up -d

# Обработка видео (скачивание комментариев + ранжирование)
docker-compose exec comments-downloader python process_video.py "https://www.youtube.com/watch?v=VIDEO_ID"
```

### 2. Ранжирование существующих комментариев

```bash
# Gemini ранжирование (рекомендуется)
docker-compose exec comments-downloader python gemini_ranker.py VIDEO_ID --api-key=YOUR_GEMINI_KEY

# Эвристическое ранжирование (fallback)
docker-compose exec comments-downloader python comment_ranker.py VIDEO_ID
```

## 📊 Как работает ранжирование

### Критерии оценки:
- **1.0**: Комментарий добавляет значительную ценность, дополняет содержание видео
- **0.7-0.9**: Релевантен и содержит полезную информацию
- **0.4-0.6**: Частично связан с темой видео
- **0.1-0.3**: Слабо связан с содержанием
- **0.0**: Не связан с видео (спам, оффтоп, эмоции без содержания)

### Процесс:
1. Система получает summary видео из базы данных
2. Для каждого комментария создается промпт с контекстом видео
3. **Gemini AI** анализирует релевантность комментария (или используется эвристический алгоритм)
4. Присваивается числовая оценка от 0.0 до 1.0
5. Результат сохраняется в поле `comment_rank` таблицы `comments`

## 🔧 Настройка

### Параметры CommentRanker (эвристический):

```python
# Создание экземпляра ранкера
ranker = CommentRanker(
    use_fallback=True,  # Использовать эвристику
    batch_size=5  # Размер батча
)
```

### Параметры GeminiCommentRanker (AI):

```python
# Создание экземпляра Gemini ранкера
ranker = GeminiCommentRanker(
    api_key="your_gemini_api_key",
    batch_size=10,
    max_retries=3
)
```

### Переменные окружения:

```bash
DB_HOST=db
DB_PORT=5432
DB_NAME=comments
DB_USER=postgres
DB_PASSWORD=postgres
GEMINI_API_KEY=your_gemini_api_key_here
```

## 📝 Примеры использования

### Получение топ-комментариев:

```python
from comment_ranker import CommentRanker

ranker = CommentRanker()

# Получить комментарии с рангом выше 0.7
top_comments = ranker.get_ranked_comments(
    video_id=1, 
    min_rank=0.7
)

for comment in top_comments[:10]:
    print(f"Ранг: {comment['rank']:.3f}")
    print(f"Текст: {comment['text']}")
    print("---")
```

### Ранжирование конкретного видео:

```python
from gemini_ranker import GeminiCommentRanker

ranker = GeminiCommentRanker(api_key="your_key")
success = ranker.rank_comments_for_video(video_id=1)

if success:
    print("Ранжирование завершено!")
```

## 🗃️ Структура базы данных

Таблица `comments` содержит поле для ранжирования:

```sql
-- Поле для хранения ранга комментария
comment_rank FLOAT
```

### Запросы для анализа:

```sql
-- Топ-10 самых информативных комментариев
SELECT author, text, comment_rank, likes 
FROM comments 
WHERE video_id = 1 AND comment_rank IS NOT NULL
ORDER BY comment_rank DESC 
LIMIT 10;

-- Статистика по рангам
SELECT 
    COUNT(*) as total_comments,
    AVG(comment_rank) as avg_rank,
    COUNT(CASE WHEN comment_rank >= 0.7 THEN 1 END) as high_quality,
    COUNT(CASE WHEN comment_rank < 0.3 THEN 1 END) as low_quality
FROM comments 
WHERE video_id = 1 AND comment_rank IS NOT NULL;
```

## 🛠️ Миграция существующих данных

Если у вас уже есть данные в базе, выполните миграцию:

```bash
docker-compose exec comments-downloader python migrate_add_rank.py
```

## ⚡ Производительность

### Gemini ранжирование:
- **Мега-запрос**: ~10 секунд для всех комментариев
- **Батчевая обработка**: 10-20 комментариев за раз
- **Успешность**: 95-100%

### Эвристическое ранжирование:
- **Скорость**: ~30 секунд для 1000+ комментариев
- **Батчевая обработка**: 5 комментариев за раз
- **Успешность**: 100%

## 🔍 Мониторинг и отладка

### Логи процесса:
```bash
# Просмотр логов ранжирования
docker-compose logs comments-downloader
```

### Проверка результатов:
```bash
# Подключение к базе данных
docker-compose exec db psql -U postgres -d comments

# Проверка проранжированных комментариев
SELECT COUNT(*) FROM comments WHERE comment_rank IS NOT NULL;
```

## 🚨 Устранение неполадок

### Gemini API недоступен:
```bash
# Проверка API ключа
echo $GEMINI_API_KEY

# Использование эвристического ранжирования
docker-compose exec comments-downloader python comment_ranker.py VIDEO_ID
```

### Ошибки базы данных:
```bash
# Проверка подключения к БД
docker-compose exec comments-downloader python -c "from models import get_db_session; print('DB OK')"
```

## 📈 Следующие шаги

1. **Веб-интерфейс**: Создание API для доступа к ранжированным комментариям
2. **Аналитика**: Добавление дополнительных метрик и тегов
3. **Оптимизация**: Улучшение скорости обработки
4. **Кэширование**: Сохранение результатов для повторного использования 