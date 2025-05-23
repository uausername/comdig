# Управление данными видео

## 📋 Обзор

Скрипт `reset_video_data.py` предназначен для управления данными видео в системе ComDig. Позволяет сбрасывать транскрипты и summary для повторной обработки.

## 🔧 Команды

### Просмотр статистики
```bash
# Показать статистику всех видео
docker-compose run --rm comments-downloader python reset_video_data.py --stats
```

### Сброс данных конкретного видео
```bash
# Сбросить все данные видео (транскрипт + summary)
docker-compose run --rm comments-downloader python reset_video_data.py 5

# Сбросить только транскрипт
docker-compose run --rm comments-downloader python reset_video_data.py 5 --transcript-only

# Сбросить только summary
docker-compose run --rm comments-downloader python reset_video_data.py 5 --summary-only
```

### Массовые операции
```bash
# Сбросить данные всех видео (с подтверждением)
docker-compose run --rm comments-downloader python reset_video_data.py --all
```

## 📊 Пример вывода статистики

```
📊 Статистика данных видео:
============================================================

🎬 Видео ID: 5
   YouTube ID: I7WwYLGI6TQ
   Транскрипт: ✅ (1234 символов)
   Summary: ✅ (192 символа)
   Комментарии: 130 (ранжировано: 130)

📈 Общая статистика:
   Всего видео: 1
   С транскриптом: 1 (100.0%)
   С summary: 1 (100.0%)
   С полными данными: 1 (100.0%)
```

## 🔄 Типичные сценарии использования

### 1. Повторная обработка видео с исправленным транскриптом
```bash
# 1. Сбросить данные видео
docker-compose run --rm comments-downloader python reset_video_data.py 5

# 2. Запустить повторную обработку
docker-compose run --rm comments-downloader python process_video.py "https://www.youtube.com/watch?v=I7WwYLGI6TQ"
```

### 2. Обновление только summary
```bash
# 1. Сбросить только summary
docker-compose run --rm comments-downloader python reset_video_data.py 5 --summary-only

# 2. Запустить повторную обработку (транскрипт останется)
docker-compose run --rm comments-downloader python process_video.py "https://www.youtube.com/watch?v=I7WwYLGI6TQ"
```

### 3. Диагностика проблем
```bash
# Проверить статистику данных
docker-compose run --rm comments-downloader python reset_video_data.py --stats

# Проверить статистику ранжирования
docker-compose run --rm comments-downloader python reset_ranking.py --stats
```

## ⚠️ Важные замечания

- **Безопасность**: Операция `--all` требует подтверждения
- **Связанные данные**: Сброс данных видео не влияет на комментарии и их ранжирование
- **Повторная обработка**: После сброса данных можно запустить `process_video.py` для повторной обработки
- **Резервные копии**: Рекомендуется делать резервные копии БД перед массовыми операциями

## 🔗 Связанные команды

- `reset_ranking.py` - управление ранжированием комментариев
- `process_video.py` - полная обработка видео
- `demo_ranking.py` - демонстрация результатов 