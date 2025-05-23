# 🛠️ Настройка проекта ComDig

## 📋 Предварительные требования

- **Docker** и **Docker Compose**
- **Git**
- Минимум **2GB** свободного места на диске (для модели)

## 🚀 Пошаговая установка

### 1. Клонирование репозитория

```bash
git clone https://github.com/uausername/comdig.git
cd comdig
```

### 2. Скачивание модели Qwen2

Модель не включена в репозиторий из-за большого размера (940MB). Скачайте её вручную:

#### Вариант A: Через wget (Linux/macOS)
```bash
mkdir -p summarizer/model
wget -O summarizer/model/qwen2-1_5b-instruct-q4_k_m.gguf \
  https://huggingface.co/Qwen/Qwen2-1.5B-Instruct-GGUF/resolve/main/qwen2-1_5b-instruct-q4_k_m.gguf
```

#### Вариант B: Через curl
```bash
mkdir -p summarizer/model
curl -L -o summarizer/model/qwen2-1_5b-instruct-q4_k_m.gguf \
  https://huggingface.co/Qwen/Qwen2-1.5B-Instruct-GGUF/resolve/main/qwen2-1_5b-instruct-q4_k_m.gguf
```

#### Вариант C: Ручное скачивание
1. Перейдите на [страницу модели](https://huggingface.co/Qwen/Qwen2-1.5B-Instruct-GGUF)
2. Скачайте файл `qwen2-1_5b-instruct-q4_k_m.gguf`
3. Поместите его в папку `summarizer/model/`

### 3. Проверка структуры

Убедитесь, что структура проекта выглядит так:

```
comdig/
├── summarizer/
│   ├── model/
│   │   └── qwen2-1_5b-instruct-q4_k_m.gguf  ← Этот файл должен быть!
│   ├── summarizer_api.py
│   └── Dockerfile
├── docker-compose.yml
├── comments_downloader.py
└── ...
```

### 4. Запуск системы

```bash
docker-compose up -d
```

### 5. Проверка работы

```bash
# Проверка статуса контейнеров
docker-compose ps

# Просмотр логов
docker-compose logs summarizer-llm
docker-compose logs comments-downloader
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

### Проблема: Модель не найдена
```
Error: Model file not found
```

**Решение:** Убедитесь, что файл модели находится в правильном месте:
```bash
ls -la summarizer/model/qwen2-1_5b-instruct-q4_k_m.gguf
```

### Проблема: Контейнер не запускается
```
Error: Container failed to start
```

**Решение:** Проверьте логи:
```bash
docker-compose logs summarizer-llm
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

-- Последние комментарии
SELECT author, text, likes FROM comments ORDER BY published_at DESC LIMIT 10;
```

## 🔄 Обновление проекта

```bash
git pull origin main
docker-compose down
docker-compose build
docker-compose up -d
```

## 📞 Поддержка

Если возникли проблемы:

1. Проверьте [Issues](https://github.com/uausername/comdig/issues) на GitHub
2. Создайте новый Issue с описанием проблемы
3. Приложите логи: `docker-compose logs > logs.txt` 