# 🛠️ Настройка проекта ComDig

## 📋 Предварительные требования

- **Docker** и **Docker Compose**
- **Git**
- **Gemini API ключ** (для генерации саммари и ранжирования)

## 🚀 Пошаговая установка

### 1. Клонирование репозитория

```bash
git clone https://github.com/uausername/comdig.git
cd comdig
```

### 2. Настройка API ключей

Создайте файл `.env` в корне проекта:

```bash
# Gemini API ключ (обязательно для лучшего качества)
GEMINI_API_KEY=your_gemini_api_key_here
```

**Получение Gemini API ключа:**
1. Перейдите на [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Создайте новый API ключ
3. Скопируйте его в файл `.env`

### 3. Запуск системы

```bash
docker-compose up -d
```

### 4. Проверка работы

```bash
# Проверка статуса контейнеров
docker-compose ps

# Просмотр логов
docker-compose logs comments-downloader
docker-compose logs db
```

## 🔧 Настройка видео для обработки

Отредактируйте файл `docker-compose.yml` и измените переменную `VIDEO_URL`:

```yaml
environment:
  - VIDEO_URL=https://www.youtube.com/watch?v=YOUR_VIDEO_ID
```

Затем перезапустите сервис:

```bash
docker-compose restart comments-downloader
```

## 🐛 Решение проблем

### Проблема: Нет Gemini API ключа
```
⚠️ GEMINI_API_KEY не найден
🔄 Использую fallback summary...
```

**Решение:** Добавьте API ключ в файл `.env`:
```bash
echo "GEMINI_API_KEY=your_key_here" > .env
docker-compose restart comments-downloader
```

### Проблема: Контейнер не запускается
```
Error: Container failed to start
```

**Решение:** Проверьте логи:
```bash
docker-compose logs comments-downloader
```

### Проблема: Нет доступа к YouTube
```
Error: Failed to download comments
```

**Решение:** Проверьте интернет-соединение и корректность URL видео.

## 📊 Проверка базы данных

Подключение к PostgreSQL:

```bash
docker-compose exec db psql -U postgres -d comments
```

Полезные SQL-запросы:

```sql
-- Список всех видео
SELECT id, youtube_url, title FROM videos;

-- Количество комментариев по видео
SELECT v.youtube_url, COUNT(c.id) as comment_count 
FROM videos v 
LEFT JOIN comments c ON v.id = c.video_id 
GROUP BY v.id, v.youtube_url;

-- Топ комментарии с рангами
SELECT author, text, comment_rank, likes 
FROM comments 
WHERE comment_rank IS NOT NULL 
ORDER BY comment_rank DESC LIMIT 10;
```

## 🔄 Обновление проекта

```bash
git pull origin main
docker-compose down
docker-compose build
docker-compose up -d
```

## 🎯 Использование системы

### Обработка видео
```bash
# Основной пайплайн
docker-compose run --rm comments-downloader python process_video.py

# Только скачивание комментариев
docker-compose run --rm comments-downloader python comments_downloader.py
```

### Ранжирование комментариев
```bash
# Gemini ранжирование (рекомендуется)
docker-compose run --rm comments-downloader python gemini_ranker.py VIDEO_ID --api-key=YOUR_KEY

# Эвристическое ранжирование (fallback)
docker-compose run --rm comments-downloader python comment_ranker.py VIDEO_ID
```

## 📞 Поддержка

Если возникли проблемы:

1. Проверьте [Issues](https://github.com/uausername/comdig/issues) на GitHub
2. Создайте новый Issue с описанием проблемы
3. Приложите логи: `docker-compose logs > logs.txt` 