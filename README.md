# 🚀 ComDig - Система анализа комментариев YouTube

## 📋 Описание

ComDig - это революционная система для анализа и ранжирования комментариев YouTube с использованием искусственного интеллекта. Система автоматически скачивает комментарии, анализирует их информативность и создает рейтинг наиболее ценных комментариев.

## ✨ Ключевые особенности

- 🤖 **Мультиключевая система Gemini AI** - ускорение обработки в 3x
- 📊 **Интеллектуальное ранжирование** комментариев по информативности
- 🎯 **Автоматическая генерация summary** видео
- 💾 **PostgreSQL база данных** для хранения результатов
- 🐳 **Docker-контейнеризация** для простого развертывания
- 📄 **JSON экспорт** результатов

## 🚀 Быстрый старт

### 1. Запуск системы

```bash
# Простой запуск с предустановленным видео
docker-compose up

# Для другого видео - измените VIDEO_URL в docker-compose.yml
```

### 2. Обработка конкретного видео

```bash
# Обработка любого YouTube видео
docker-compose run --rm comments-downloader python process_video.py "https://www.youtube.com/watch?v=VIDEO_ID"
```

## 📁 Структура проекта

### 🔧 Основные файлы

```
comdig/
├── 🚀 process_video.py              # Главный пайплайн обработки
├── 🤖 multi_key_gemini_ranker.py    # Мультиключевая система ранжирования
├── 📊 gemini_ranker.py              # Базовая система ранжирования Gemini
├── 🔄 comment_ranker.py             # Эвристическое ранжирование (fallback)
├── 📥 comments_downloader.py        # Скачивание комментариев YouTube
├── 🗄️ models.py                     # Модели базы данных
├── 🐳 docker-compose.yml            # Конфигурация Docker
├── 🐳 dockerfile                    # Образ Docker
└── 📋 requirements.txt              # Зависимости Python
```

### 🛠️ Утилиты управления

```
├── 🔄 reset_ranking.py              # Сброс ранжирования комментариев
├── 🔄 reset_video_data.py           # Сброс данных видео (transcript/summary)
└── 📄 .env                          # Переменные окружения (API ключи)
```

### 📚 Документация

```
├── 📖 README.md                     # Основная документация
├── 📋 project_current_stage.md      # Текущий статус проекта
├── 📋 project_description.md        # Описание проекта
├── 🔧 SETUP.md                      # Инструкции по установке
├── 📊 RANKING_USAGE.md              # Руководство по ранжированию
├── 📄 JSON_STRUCTURE.md             # Структура JSON файлов
├── 🗄️ VIDEO_DATA_MANAGEMENT.md      # Управление данными видео
└── 📝 TRANSCRIPT_LOGIC_UPDATE.md    # Обновления логики транскриптов
```

### 📁 Архивные файлы

```
└── archive/                         # Устаревшие и вспомогательные файлы
    ├── 📋 ARCHIVE_DESCRIPTION.md    # Описание архивных файлов
    ├── 🧪 test_*.py                 # Тестовые файлы
    ├── 🔧 migrate_*.py              # Миграции БД (выполнены)
    ├── 🔍 check_*.py                # Диагностические утилиты
    └── 🎭 demo_*.py                 # Демонстрационные файлы
```

## 🔑 Настройка API ключей

### Gemini API ключи (обязательно)

Добавьте ваши API ключи в `docker-compose.yml`:

```yaml
environment:
  - GEMINI_API_KEY_1=your_first_api_key
  - GEMINI_API_KEY_2=your_second_api_key  
  - GEMINI_API_KEY_3=your_third_api_key
```

### Получение API ключей

1. Перейдите на [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Создайте новый API ключ
3. Для мультиключевой системы создайте 3 ключа в разных проектах

## 📊 Результаты работы

После обработки видео вы получите:

### 📄 JSON файлы
- `comments.json` - все комментарии с рангами
- `summary.json` - информация о видео и summary

### 🗄️ База данных PostgreSQL
- Таблица `videos` - данные видео
- Таблица `comments` - комментарии с рангами

### 📈 Консольный вывод
- Топ-5 самых информативных комментариев
- Статистика обработки
- Команды для дальнейшей работы

## 🎯 Примеры использования

### Обработка видео

```bash
# Полный пайплайн
docker-compose up

# Конкретное видео
docker-compose run --rm comments-downloader python process_video.py "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
```

### Ранжирование существующих комментариев

```bash
# Мультиключевое ранжирование
docker-compose run --rm comments-downloader python multi_key_gemini_ranker.py VIDEO_ID

# Базовое ранжирование Gemini
docker-compose run --rm comments-downloader python gemini_ranker.py VIDEO_ID

# Эвристическое ранжирование
docker-compose run --rm comments-downloader python comment_ranker.py VIDEO_ID
```

### Управление данными

```bash
# Сброс ранжирования
docker-compose run --rm comments-downloader python reset_ranking.py VIDEO_ID

# Сброс данных видео
docker-compose run --rm comments-downloader python reset_video_data.py VIDEO_ID

# Статистика
docker-compose run --rm comments-downloader python reset_ranking.py --stats
```

## 🏆 Производительность

### Мультиключевая система (v2.0)
- **442 комментария** за **75 секунд**
- **Ускорение в 3x** по сравнению с одним ключом
- **100% успешность** обработки
- **Равномерная ротация** между API ключами

### Система лимитов
- **15 RPM** на ключ (45 RPM суммарно)
- **1M TPM** на ключ (3M TPM суммарно)
- **1500 RPD** на ключ (4500 RPD суммарно)

## 🔧 Требования

### Системные требования
- Docker и Docker Compose
- 4GB RAM (рекомендуется)
- 2GB свободного места

### API ключи
- Gemini API ключи (1-3 штуки)
- YouTube Data API v3 (опционально, для расширенных функций)

## 📈 Статус проекта

**Текущая версия**: v2.0 (Мультиключевая система)  
**Статус**: ✅ Готов к продакшену  
**Последнее обновление**: 25 мая 2025

### Реализованные функции
- ✅ Скачивание комментариев YouTube
- ✅ Получение транскриптов видео
- ✅ Генерация summary с Gemini AI
- ✅ Мультиключевое ранжирование комментариев
- ✅ Сохранение в PostgreSQL
- ✅ Экспорт в JSON
- ✅ Docker-контейнеризация
- ✅ Система управления лимитами API

## 🤝 Вклад в проект

Проект открыт для улучшений! Основные направления:

1. **Web UI** - веб-интерфейс для удобного использования
2. **API** - REST API для интеграции
3. **Аналитика** - дашборд с метриками
4. **Мультиязычность** - поддержка разных языков

## 📄 Лицензия

MIT License - см. файл [LICENSE](LICENSE)

## 📞 Поддержка

При возникновении проблем:

1. Проверьте [документацию](SETUP.md)
2. Изучите [архивные файлы](archive/ARCHIVE_DESCRIPTION.md)
3. Проверьте логи Docker: `docker-compose logs`

---

**🎉 ComDig - делаем анализ комментариев простым и эффективным!**
