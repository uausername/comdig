from fastapi import FastAPI, Request
from pydantic import BaseModel
import subprocess
import os
import json
import shlex
import time
import re

app = FastAPI()

class TextInput(BaseModel):
    text: str

# Указываем правильный путь к исполняемому файлу llama-cli и модели
LLAMA_MAIN_PATH = "/llama.cpp/build/bin/llama-cli"
MODEL_PATH = "/app/model/qwen2-1_5b-instruct-q4_k_m.gguf"  # путь к скачанной модели

# Максимальный размер одного чанка (примерно 3500-4000 токенов для Qwen2)
CHUNK_SIZE = 1200  # символов (увеличено в 3 раза)

# Функция для разбиения текста на чанки
def split_text(text, chunk_size):
    return [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]

# Функция для извлечения только ответа ассистента
def extract_assistant_answer(text):
    # Найти последнее вхождение 'assistant\n' и взять всё после него до конца или до следующего блока
    parts = text.rsplit('assistant\n', 1)
    if len(parts) == 2:
        answer = parts[1]
        # Обрезать всё после первого служебного блока или EOF
        answer = re.split(r'(<\|im_start\|>|> EOF by user|system\n|user\n)', answer)[0]
        return answer.strip()
    return text.strip()

@app.post("/summarize")
def summarize(input: TextInput):
    print(f"Received text for summarization (first 100 chars): {input.text[:100]}... (len={len(input.text)})")
    try:
        chunks = split_text(input.text, CHUNK_SIZE)
        summaries = []
        for idx, chunk in enumerate(chunks):
            print(f"Summarizing chunk {idx+1}/{len(chunks)} (len={len(chunk)})")
            # Формируем prompt в формате chat template для Qwen2
            prompt = (
                "<|im_start|>system\n"
                "You are a text summarizer. You are given a text and you need to summarize it. Save the key points and the main ideas.<|im_end|>\n"
                "<|im_start|>user\n"
                f"Summarize in English in 40 words: {chunk}<|im_end|>\n"
                "<|im_start|>assistant\n"
            )
            args = [
                LLAMA_MAIN_PATH,
                "-m", MODEL_PATH,
                "-p", prompt,
                "--n-predict", "64",
                "--temp", "0.7"
            ]
            print(f"[DEBUG] Запуск команды: {' '.join(shlex.quote(a) for a in args)[:200]}...")
            start = time.time()
            try:
                result = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=300)
            except subprocess.TimeoutExpired:
                print(f"[ERROR] Таймаут при генерации summary для чанка {idx+1}")
                return {"summary": None, "error": f"Timeout on chunk {idx+1}"}
            print(f"[STDOUT] {result.stdout.strip()[:200]}")
            print(f"[STDERR] {result.stderr.strip()[:200]}")
            print(f"[DEBUG] Время генерации: {time.time() - start:.2f} сек")
            if result.returncode != 0:
                print(f"llama.cpp error: {result.stderr}")
                return {"summary": None, "error": result.stderr}
            cleaned = extract_assistant_answer(result.stdout.strip())
            summaries.append(cleaned)
        final_summary = "\n".join(summaries)
        return {"summary": final_summary}
    except Exception as e:
        print(f"Ошибка при запуске llama.cpp: {e}")
        return {"summary": None, "error": str(e)}