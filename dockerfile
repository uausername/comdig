FROM python:3.9-slim

# Копируем только requirements.txt для установки зависимостей
COPY requirements.txt /app/requirements.txt

# Устанавливаем рабочую директорию
WORKDIR /app

# Устанавливаем зависимости
RUN pip install -r requirements.txt

# Копируем остальной код
COPY . /app

# Запуск команды
CMD ["python", "comments_downloader.py"]