# Используем легковесный базовый образ
FROM ubuntu:22.04

# Устанавливаем зависимости для сборки llama.cpp и утилиты для скачивания моделей, а также Python и pip
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    curl \
    git \
    python3 \
    python3-pip \
    libopenblas-dev \
    libomp-dev \
    && rm -rf /var/lib/apt/lists/*

# Устанавливаем huggingface_hub для скачивания моделей
RUN pip install --no-cache-dir huggingface_hub

# Клонируем llama.cpp
RUN git clone https://github.com/ggerganov/llama.cpp.git /llama.cpp
WORKDIR /llama.cpp

# --- force rebuild for llama.cpp binary check ---
RUN echo "force rebuild for llama.cpp binary check"
RUN mkdir build && \
    cd build && \
    cmake .. -DLLAMA_BLAS=ON -DLLAMA_BLAS_VENDOR=OpenBLAS -DLLAMA_CURL=OFF && \
    make && \
    ls -l /llama.cpp/build/ && ls -l /llama.cpp/build/bin/ || true

# Проверяем, где реально лежит бинарник main
RUN ls -l /llama.cpp/build/

# Устанавливаем рабочую директорию для нашего приложения
WORKDIR /app

# Создаем директорию для модели
RUN mkdir model
# Создаем директорию для модели и скачиваем GGUF файл
# Используем Qwen2-1.5B-Instruct в квантованном формате q4_k_m (~1GB)
# Ссылка на модель: https://huggingface.co/Qwen/Qwen2-1.5B-Instruct-GGUF
# Создаем директорию перед скачиванием
# RUN mkdir model && \
#     huggingface-cli download Qwen/Qwen2-1.5B-Instruct-GGUF qwen2-1_5b-instruct-q4_k_m.gguf --local-dir model --local-dir-use-symlinks False

# Копируем модель, скачанную вручную, в контейнер
COPY ./model/qwen2-1_5b-instruct-q4_k_m.gguf /app/model/qwen2-1_5b-instruct-q4_k_m.gguf

# Копируем файл API сервиса
COPY summarizer_api.py .

# Устанавливаем зависимости для FastAPI и Uvicorn
RUN pip install --no-cache-dir fastapi uvicorn

# Открываем порт, на котором будет работать FastAPI
EXPOSE 8000

# Определяем команду для запуска FastAPI приложения с помощью Uvicorn
# Используем полный путь до uvicorn если необходимо (зависит от PATH в контейнере)
CMD ["uvicorn", "summarizer_api:app", "--host", "0.0.0.0", "--port", "8000"]
