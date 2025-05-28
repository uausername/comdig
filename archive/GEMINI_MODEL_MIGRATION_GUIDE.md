# 🔄 Руководство по смене моделей Gemini

## Обзор

Этот документ описывает процесс смены моделей Google Gemini в проекте ComDig. Система поддерживает различные модели Gemini и может быть легко адаптирована для новых версий.

## 📋 Текущие поддерживаемые модели

### Gemini 2.5 Flash Preview 05-20 (Текущая)
- **Модель**: `gemini-2.5-flash-preview-05-20`
- **API версия**: `v1alpha`
- **Input token limit**: 1,048,576
- **Output token limit**: 65,536
- **RPM**: 10
- **TPM**: 250,000
- **RPD**: 500
- **Статус**: ✅ Активно используется

### Gemini 2.0 Flash (Предыдущая)
- **Модель**: `gemini-2.0-flash-preview-05-20`
- **API версия**: `v1alpha`
- **Input token limit**: 1,048,576
- **Output token limit**: 8,192
- **RPM**: 30
- **TPM**: 1,000,000
- **RPD**: 1,500
- **Статус**: ⚠️ Заменена

## 🔧 Процесс смены модели

### Шаг 1: Обновление названия модели

Найти и заменить во всех файлах:

```bash
# Поиск текущих вхождений
grep -r "gemini-2\.5-flash-preview-05-20" .

# Файлы для обновления:
# - process_video.py
# - comments_downloader.py
# - gemini_ranker.py
# - multi_key_gemini_ranker.py
```

**Места замены:**
```python
# В методах generate_content
model='НОВАЯ_МОДЕЛЬ_ЗДЕСЬ',
```

### Шаг 2: Обновление лимитов API

**Файл**: `gemini_ranker.py` → класс `GeminiRateLimiter`

```python
def __init__(self):
    # Лимиты для НОВАЯ_МОДЕЛЬ
    self.rpm_limit = НОВЫЙ_RPM_ЛИМИТ
    self.tpm_limit = НОВЫЙ_TPM_ЛИМИТ  
    self.rpd_limit = НОВЫЙ_RPD_ЛИМИТ
```

**Файл**: `multi_key_gemini_ranker.py` → класс `MultiKeyGeminiRateLimiter`

```python
def __init__(self):
    # Лимиты для НОВАЯ_МОДЕЛЬ
    self.rpm_limit = НОВЫЙ_RPM_ЛИМИТ
    self.tpm_limit = НОВЫЙ_TPM_ЛИМИТ
    self.rpd_limit = НОВЫЙ_RPD_ЛИМИТ
```

### Шаг 3: Проверка версии API

Убедиться, что используется правильная версия API:

```python
# Для preview моделей обычно требуется v1alpha
client = genai.Client(
    api_key=self.api_key,
    http_options=types.HttpOptions(api_version='v1alpha')
)
```

### Шаг 4: Обновление комментариев и документации

1. **Обновить комментарии в коде:**
```python
print(f"🤖 Используется: Google НОВАЯ_МОДЕЛЬ (контекст: ~XM токенов)")
```

2. **Обновить документацию:**
- `project_current_stage.md`
- `PROJECT_FILES_DOCUMENTATION.md`
- `README.md`

## 📊 Сравнение характеристик моделей

| Характеристика | Gemini 2.0 Flash | Gemini 2.5 Flash Preview |
|----------------|-------------------|---------------------------|
| Input Tokens   | 1,048,576        | 1,048,576                |
| Output Tokens  | 8,192            | 65,536                   |
| RPM            | 30               | 10                       |
| TPM            | 1,000,000        | 250,000                  |
| RPD            | 1,500            | 500                      |
| API Version    | v1alpha          | v1alpha                  |

## 🧪 Тестирование новой модели

### Быстрый тест доступности

```bash
# Запуск контейнеров
docker-compose up -d

# Тест на коротком видео
docker exec -it comdig-comments-downloader-1 python process_video.py https://www.youtube.com/watch?v=SHORT_VIDEO_ID

# Проверка логов
docker logs comdig-comments-downloader-1
```

### Полный тест функциональности

```bash
# Тест на полном видео
docker exec -it comdig-comments-downloader-1 python process_video.py https://www.youtube.com/watch?v=FULL_VIDEO_ID

# Проверка ранжирования
docker exec -it comdig-comments-downloader-1 python gemini_ranker.py VIDEO_ID

# Мультиключевое ранжирование
docker exec -it comdig-comments-downloader-1 python multi_key_gemini_ranker.py VIDEO_ID
```

## 🔍 Диагностика проблем

### Проблема: 404 Model not found

**Причина**: Неправильная версия API или модель недоступна

**Решение**:
1. Проверить версию API (`v1alpha` vs `v1beta`)
2. Убедиться, что модель доступна в указанной версии API
3. Проверить правильность названия модели

### Проблема: Пустые ответы от API

**Причина**: Изменения в формате запроса или промптах

**Решение**:
1. Проверить формат запроса
2. Обновить промпты под новую модель
3. Проверить лимиты токенов

### Проблема: Превышение лимитов

**Причина**: Неправильно настроенные лимиты для новой модели

**Решение**:
1. Обновить лимиты в `GeminiRateLimiter`
2. Проверить актуальные лимиты в документации Google
3. Настроить систему ожидания

## 📝 Чек-лист смены модели

- [ ] Обновить название модели во всех файлах
- [ ] Обновить лимиты API (RPM, TPM, RPD)
- [ ] Проверить версию API (v1alpha/v1beta)
- [ ] Обновить комментарии в коде
- [ ] Обновить документацию
- [ ] Провести тест доступности
- [ ] Провести полный функциональный тест
- [ ] Обновить `project_current_stage.md`
- [ ] Зафиксировать изменения в Git

## 🚀 Автоматизация смены модели

Для будущих обновлений можно создать скрипт автоматизации:

```bash
#!/bin/bash
# migrate_gemini_model.sh

OLD_MODEL="$1"
NEW_MODEL="$2"
NEW_RPM="$3"
NEW_TPM="$4"
NEW_RPD="$5"

# Замена названия модели
find . -name "*.py" -exec sed -i "s/$OLD_MODEL/$NEW_MODEL/g" {} \;

# Обновление лимитов (требует ручной настройки)
echo "Не забудьте обновить лимиты в gemini_ranker.py и multi_key_gemini_ranker.py"
echo "RPM: $NEW_RPM, TPM: $NEW_TPM, RPD: $NEW_RPD"
```

## 📚 Полезные ссылки

- [Google AI Studio](https://aistudio.google.com/)
- [Gemini API Documentation](https://ai.google.dev/docs)
- [Rate Limits Documentation](https://ai.google.dev/docs/rate_limits)
- [Model Comparison](https://ai.google.dev/models/gemini)

---

**Последнее обновление**: 27 мая 2025  
**Версия документа**: 1.0  
**Автор**: ComDig Development Team 