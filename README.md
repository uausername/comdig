# 🧠 ComDig - Умный анализатор комментариев YouTube

Веб-сервис для анализа комментариев YouTube с использованием ИИ. Система автоматически собирает комментарии, анализирует содержание видео и ранжирует комментарии по информативности.

## 🎯 Основные возможности

- **📥 Сбор комментариев** без использования официального YouTube API
- **📝 Получение транскриптов** видео (субтитры или ASR)
- **🤖 Генерация summary** содержания видео с помощью локальной LLM
- **📊 Ранжирование комментариев** по информативности (в разработке)
- **🐳 Полная Docker-инфраструктура** для простого развертывания

## 🏗️ Архитектура

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  Comments       │    │   PostgreSQL     │    │  Summarizer     │
│  Downloader     │◄──►│   Database       │    │  LLM Service    │
│                 │    │                  │    │  (Qwen2)        │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

### Компоненты:

1. **Comments Downloader** - основной сервис для сбора и обработки данных
2. **PostgreSQL** - база данных для хранения видео, комментариев и транскриптов
3. **Summarizer LLM** - сервис суммаризации на базе Qwen2 модели

## 🚀 Быстрый старт

### Предварительные требования

- Docker и Docker Compose
- Git

### Установка

1. **Клонируйте репозиторий:**
```bash
git clone https://github.com/uausername/comdig.git
cd comdig
```

2. **Скачайте модель Qwen2:**
```bash
# Создайте папку для модели
mkdir -p summarizer/model

# Скачайте модель (примерно 1GB)
wget -O summarizer/model/qwen2-1_5b-instruct-q4_k_m.gguf \
  https://huggingface.co/Qwen/Qwen2-1.5B-Instruct-GGUF/resolve/main/qwen2-1_5b-instruct-q4_k_m.gguf
```

3. **Запустите систему:**
```bash
docker-compose up -d
```

### Использование

1. **Обработка видео через переменную окружения:**
```bash
# Установите URL видео в docker-compose.yml
VIDEO_URL=https://www.youtube.com/watch?v=YOUR_VIDEO_ID

# Перезапустите сервис
docker-compose restart comments-downloader
```

2. **Проверка результатов:**
```bash
# Просмотр логов
docker-compose logs comments-downloader

# Подключение к базе данных
docker-compose exec db psql -U postgres -d comments
```

## 📊 Структура базы данных

### Таблица `videos`
- `id` - уникальный идентификатор
- `youtube_url` - ссылка на видео
- `title` - название видео
- `summary` - краткое содержание

### Таблица `comments`
- `id` - уникальный идентификатор
- `video_id` - связь с видео
- `author` - автор комментария
- `text` - текст комментария
- `likes` - количество лайков
- `rank` - ранг информативности (в разработке)

### Таблица `transcripts`
- `id` - уникальный идентификатор
- `video_id` - связь с видео
- `content` - текст транскрипта

## 🛠️ Разработка

### Структура проекта

```
comdig/
├── comments_downloader.py    # Основной скрипт обработки
├── models.py                 # Модели базы данных
├── requirements.txt          # Python зависимости
├── docker-compose.yml        # Docker конфигурация
├── dockerfile               # Dockerfile для основного сервиса
└── summarizer/              # Сервис суммаризации
    ├── summarizer_api.py    # FastAPI сервер
    ├── Dockerfile           # Dockerfile для LLM сервиса
    └── model/               # Папка для модели Qwen2
```

### Локальная разработка

1. **Установите зависимости:**
```bash
pip install -r requirements.txt
```

2. **Настройте переменные окружения:**
```bash
export DB_HOST=localhost
export DB_PORT=5432
export DB_NAME=comments
export DB_USER=postgres
export DB_PASSWORD=postgres
```

3. **Запустите PostgreSQL:**
```bash
docker-compose up -d db
```

## 🔧 Конфигурация

### Переменные окружения

| Переменная | Описание | По умолчанию |
|------------|----------|--------------|
| `VIDEO_URL` | URL YouTube видео для обработки | - |
| `DB_HOST` | Хост базы данных | localhost |
| `DB_PORT` | Порт базы данных | 5432 |
| `DB_NAME` | Имя базы данных | comments |
| `DB_USER` | Пользователь БД | postgres |
| `DB_PASSWORD` | Пароль БД | postgres |

## 📈 Текущий статус

### ✅ Реализовано:
- Сбор комментариев YouTube без API
- Получение транскриптов видео
- Генерация summary с помощью LLM
- Сохранение данных в PostgreSQL
- Docker-инфраструктура

### 🔄 В разработке:
- Ранжирование комментариев по информативности
- FastAPI веб-интерфейс
- Интеграция ASR (Whisper) для видео без субтитров

## 🤝 Вклад в проект

1. Форкните репозиторий
2. Создайте ветку для новой функции (`git checkout -b feature/amazing-feature`)
3. Зафиксируйте изменения (`git commit -m 'Add amazing feature'`)
4. Отправьте в ветку (`git push origin feature/amazing-feature`)
5. Откройте Pull Request

## 📝 Лицензия

Этот проект распространяется под лицензией MIT. См. файл `LICENSE` для подробностей.

## 🔗 Полезные ссылки

- [YouTube Comment Downloader](https://github.com/egbertbouman/youtube-comment-downloader)
- [YouTube Transcript API](https://github.com/jdepoix/youtube-transcript-api)
- [Qwen2 Model](https://huggingface.co/Qwen/Qwen2-1.5B-Instruct-GGUF)

## 📞 Поддержка

Если у вас есть вопросы или предложения, создайте issue в этом репозитории.
