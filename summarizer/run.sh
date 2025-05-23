#!/bin/bash

# Проверяем, передан ли текст для суммаризации
if [ -z "$1" ]; then
    echo "Ошибка: Не указан текст для суммаризации."
    echo "Использование: ./run.sh \"Эта ошибка связана с тем, как вы передаете текст для суммаризации в команду docker run. Строка "Вставьте сюда текст, который нужно суммировать." передается как один аргумент скрипту run.sh. Однако run.sh ожидает, что фактический текст для суммаризации будет передан как аргумент, а не эту placeholder-фразу.\""
    exit 1
fi

MODEL_PATH="/app/model/qwen2-1_5b-instruct-q4_k_m.gguf"
# Увеличиваем контекстное окно для обработки более длинных текстов
CONTEXT_SIZE=4096 # Qwen2-1.5B поддерживает больший контекст

# Формат промпта для Qwen2 Instruct (ChatML)
# Подробности формата: https://huggingface.co/Qwen/Qwen2-1.5B-Instruct-GGUF
# Добавляем инструкции для модели
PROMPT="<|im_start|>user\nSummarize the following text concisely:\n\n$1<|im_end|>\n<|im_start|>assistant\n"

# Запускаем llama.cpp с моделью и промптом
# -m: путь к модели
# -p: промпт
# -n 512: ограничение на 512 новых токенов в ответе (можно настроить)
# -c: контекстное окно
# --n-gpu-layers 0: Убеждаемся, что модель работает только на CPU
/llama.cpp/build/bin/main \
    -m "$MODEL_PATH" \
    -p "$PROMPT" \
    -n 512 \
    -c $CONTEXT_SIZE \
    --n-gpu-layers 0 \
    --no-display-prompt # Отключаем вывод промпта от llama.cpp
