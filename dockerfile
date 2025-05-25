FROM python:3.9-slim

# Копируем только requirements.txt для установки зависимостей
COPY requirements.txt /app/requirements.txt

# Устанавливаем рабочую директорию
WORKDIR /app

# Устанавливаем зависимости
RUN pip install -r requirements.txt

# Копируем остальной код
COPY . /app

# Запуск современного пайплайна с мультиключевой системой
# Используем переменную окружения VIDEO_URL из docker-compose.yml
CMD ["sh", "-c", "if [ -n \"$VIDEO_URL\" ]; then python process_video.py \"$VIDEO_URL\"; else echo '❌ Переменная VIDEO_URL не установлена! Установите URL видео в docker-compose.yml'; exit 1; fi"]