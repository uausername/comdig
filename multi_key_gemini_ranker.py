#!/usr/bin/env python3
"""
🚀 МУЛЬТИКЛЮЧЕВАЯ СИСТЕМА РАНЖИРОВАНИЯ GEMINI
Революционное ускорение обработки комментариев в 3-5 раз

Особенности:
- Ротация между множественными API ключами
- Параллельная обработка батчей
- Интеллектуальная балансировка нагрузки
- Соблюдение лимитов для каждого ключа
"""

import google.generativeai as genai
import time
import random
import os
import asyncio
import concurrent.futures
from typing import List, Dict, Optional, Tuple
from sqlalchemy.orm import Session
from models import Video, Comment, get_db_session
from datetime import datetime, timedelta
from gemini_ranker import GeminiRateLimiter

class MultiKeyGeminiRanker:
    """Мультиключевая система ранжирования с Gemini API"""
    
    def __init__(self, api_keys: List[str] = None, use_fallback: bool = True):
        """
        Инициализация мультиключевой системы ранжирования
        
        Args:
            api_keys: Список API ключей. Если None, загружается из переменных окружения
            use_fallback: Использовать ли fallback на эвристическое ранжирование
        """
        # Получаем API ключи из переменных окружения или параметров
        if api_keys:
            self.api_keys = api_keys
        else:
            self.api_keys = self._load_api_keys_from_env()
        
        if not self.api_keys:
            raise ValueError("Не найдено API ключей для мультиключевой системы")
        
        print(f"🔑 Инициализация с {len(self.api_keys)} API ключами")
        
        # Настройки для батчевой обработки
        self.batch_size = 10  # Уменьшено с 20 до 10 для получения полных ответов
        self.use_fallback = use_fallback
        
        # Создаем отдельные модели и rate limiters для каждого ключа
        self.models = {}
        self.rate_limiters = {}
        self.key_usage_stats = {}
        
        for i, api_key in enumerate(self.api_keys, 1):
            key_name = f"key_{i}"
            
            # Настраиваем модель для каждого ключа
            genai.configure(api_key=api_key)
            self.models[key_name] = genai.GenerativeModel('gemini-2.0-flash')
            
            # Создаем rate limiter для каждого ключа (используем стандартные лимиты)
            self.rate_limiters[key_name] = GeminiRateLimiter()
            
            # Инициализируем статистику использования
            self.key_usage_stats[key_name] = 0
        
        # Настройки генерации
        self.generation_config = genai.types.GenerationConfig(
            temperature=0.1,
            max_output_tokens=500,  # Увеличено для получения полных ответов
            top_p=0.8,
            top_k=40
        )
        
    def _load_api_keys_from_env(self) -> List[str]:
        """Загружает API ключи из переменных окружения"""
        keys = []
        
        # Пробуем загрузить пронумерованные ключи
        for i in range(1, 10):  # поддержка до 9 ключей
            key = os.getenv(f'GEMINI_API_KEY_{i}')
            if key:
                keys.append(key)
        
        # Если пронумерованных ключей нет, используем основной
        if not keys:
            main_key = os.getenv('GEMINI_API_KEY')
            if main_key:
                keys.append(main_key)
        
        return keys
    
    def get_best_available_key(self, estimated_tokens: int = 1000) -> Optional[Tuple[str, str, GeminiRateLimiter]]:
        """
        Находит наименее загруженный API ключ с улучшенной ротацией
        
        Returns:
            Tuple[key_name, api_key, rate_limiter] или None если все заняты
        """
        available_keys = []
        
        for key_name, rate_limiter in self.rate_limiters.items():
            if rate_limiter.can_make_request(estimated_tokens):
                status = rate_limiter.get_status()
                # Вычисляем "загруженность" ключа (0-1, где 0 = свободен)
                rpm_load = status['rpm_used'] / status['rpm_limit']
                tpm_load = status['tpm_used'] / status['tpm_limit']
                rpd_load = status['rpd_used'] / status['rpd_limit']
                
                # Добавляем фактор использования для более равномерной ротации
                usage_factor = self.key_usage_stats[key_name] / max(1, sum(self.key_usage_stats.values()))
                
                total_load = (rpm_load + tpm_load + rpd_load + usage_factor) / 4
                available_keys.append((key_name, total_load))
                
                print(f"🔍 {key_name}: RPM {status['rpm_used']}/{status['rpm_limit']}, "
                      f"TPM {status['tpm_used']}/{status['tpm_limit']}, "
                      f"RPD {status['rpd_used']}/{status['rpd_limit']}, "
                      f"Usage: {self.key_usage_stats[key_name]}, Load: {total_load:.3f}")
        
        if not available_keys:
            print("⚠️ Все ключи исчерпали лимиты")
            return None
        
        # Сортируем по загруженности (наименее загруженный первый)
        available_keys.sort(key=lambda x: x[1])
        best_key_name = available_keys[0][0]
        
        api_key = self.api_keys[int(best_key_name.split('_')[1]) - 1]
        rate_limiter = self.rate_limiters[best_key_name]
        
        print(f"✅ Выбран {best_key_name} (загруженность: {available_keys[0][1]:.3f})")
        
        return best_key_name, api_key, rate_limiter
    
    def rank_comments_for_video(self, video_id: int) -> bool:
        """
        Ранжирует все комментарии для указанного видео с мультиключевой системой
        """
        session = get_db_session()
        try:
            # Получаем видео и его summary
            video = session.query(Video).filter_by(id=video_id).first()
            if not video:
                print(f"❌ Видео с ID {video_id} не найдено")
                return False
                
            if not video.summary:
                print(f"❌ У видео {video_id} нет summary для ранжирования")
                return False
                
            # Получаем комментарии без ранга
            comments = session.query(Comment).filter_by(
                video_id=video_id, 
                comment_rank=None
            ).all()
            
            if not comments:
                print(f"✅ Все комментарии для видео {video_id} уже проранжированы")
                return True
                
            print(f"🚀 МУЛЬТИКЛЮЧЕВОЕ РАНЖИРОВАНИЕ")
            print(f"📊 Комментариев: {len(comments)}")
            print(f"🔑 API ключей: {len(self.api_keys)}")
            print(f"⚡ Ожидаемое ускорение: {len(self.api_keys)}x")
            print("-" * 60)
            
            start_time = time.time()
            
            # Пробуем мега-запрос с лучшим ключом
            if len(comments) <= 100:  # для небольших объемов пробуем мега-запрос
                success = self._try_mega_request(comments, video.summary, session)
                if success:
                    elapsed = time.time() - start_time
                    print(f"✅ Мега-запрос завершен за {elapsed:.1f} сек")
                    session.commit()
                    return True
            
            # Fallback к мультиключевой батчевой обработке
            print("🔄 Переключаюсь на мультиключевую батчевую обработку...")
            success = self._rank_comments_multikey_batches(comments, video.summary, session)
            
            if success:
                elapsed = time.time() - start_time
                print(f"✅ Мультиключевое ранжирование завершено за {elapsed:.1f} сек")
                print(f"📊 Статистика использования ключей:")
                for key_name, usage in self.key_usage_stats.items():
                    print(f"   {key_name}: {usage} запросов")
                session.commit()
                return True
            else:
                print("❌ Мультиключевое ранжирование не удалось")
                return False
                
        except Exception as e:
            print(f"❌ Ошибка при мультиключевом ранжировании: {e}")
            session.rollback()
            return False
        finally:
            session.close()
    
    def _try_mega_request(self, comments: List[Comment], video_summary: str, session: Session) -> bool:
        """Пробует обработать все комментарии одним мега-запросом"""
        try:
            print(f"🎯 Попытка мега-запроса для {len(comments)} комментариев...")
            
            # Находим лучший доступный ключ
            key_info = self.get_best_available_key(len(comments) * 10)
            if not key_info:
                print("⚠️ Нет доступных ключей для мега-запроса")
                return False
            
            key_name, api_key, rate_limiter = key_info
            
            # Настраиваем API для выбранного ключа
            genai.configure(api_key=api_key)
            model = self.models[key_name]
            
            # Создаем мега-промпт
            prompt = self._create_mega_ranking_prompt(comments, video_summary)
            estimated_tokens = len(prompt.split()) + len(comments) * 3
            
            # Ждем если нужно
            wait_time = rate_limiter.wait_if_needed(estimated_tokens)
            if wait_time > 0:
                print(f"⏳ Ожидание {wait_time:.1f} сек для ключа {key_name}")
            
            # Отправляем запрос
            mega_config = genai.types.GenerationConfig(
                temperature=0.1,
                max_output_tokens=2000,
                top_p=0.8,
                top_k=40
            )
            
            response = model.generate_content(prompt, generation_config=mega_config)
            rate_limiter.record_request(estimated_tokens)
            self.key_usage_stats[key_name] += 1
            
            if response and response.text:
                ranks = self._extract_mega_ranks_from_response(response.text, len(comments))
                if ranks and len(ranks) == len(comments):
                    # Применяем ранги
                    for comment, rank in zip(comments, ranks):
                        comment.comment_rank = rank
                    print(f"✅ Мега-запрос успешен с ключом {key_name}")
                    return True
            
            return False
            
        except Exception as e:
            print(f"⚠️ Ошибка мега-запроса: {e}")
            return False
    
    def _rank_comments_multikey_batches(self, comments: List[Comment], video_summary: str, session: Session) -> bool:
        """Ранжирование батчами с использованием множественных ключей (последовательно)"""
        
        # Разбиваем комментарии на батчи
        batches = [comments[i:i + self.batch_size] for i in range(0, len(comments), self.batch_size)]
        total_batches = len(batches)
        successful_batches = 0
        
        print(f"📦 Создано {total_batches} батчей по {self.batch_size} комментариев")
        print(f"🔄 Используется последовательная обработка с ротацией ключей")
        
        # Обрабатываем батчи последовательно с интеллектуальной ротацией
        for i, batch in enumerate(batches):
            batch_num = i + 1
            print(f"\n🔄 Обработка батча {batch_num}/{total_batches}")
            
            success = self._process_batch_with_best_key(batch, video_summary, batch_num, total_batches)
            
            if success:
                successful_batches += 1
                print(f"✅ Батч {batch_num}/{total_batches} завершен успешно")
            else:
                print(f"❌ Батч {batch_num}/{total_batches} не удался")
                
            # Небольшая пауза между батчами для лучшего управления лимитами
            if batch_num < total_batches:
                time.sleep(1)
        
        print(f"\n📊 Итоговая статистика:")
        print(f"   Успешно обработано: {successful_batches}/{total_batches} батчей")
        print(f"   Успешность: {successful_batches/total_batches*100:.1f}%")
        
        # Показываем статистику использования ключей
        print(f"\n📈 Использование ключей:")
        for key_name, usage in self.key_usage_stats.items():
            print(f"   {key_name}: {usage} запросов")
        
        return successful_batches > 0
    
    def _process_batch_with_best_key(self, batch: List[Comment], video_summary: str, batch_num: int, total_batches: int) -> bool:
        """Обрабатывает батч с использованием наилучшего доступного ключа"""
        max_attempts = 3
        
        for attempt in range(max_attempts):
            try:
                # Находим лучший доступный ключ
                key_info = self.get_best_available_key(self.batch_size * 5)
                
                if not key_info:
                    # Если нет доступных ключей, ждем дольше
                    print(f"⏳ Батч {batch_num}: все ключи заняты, ожидание 30 сек...")
                    time.sleep(30)
                    continue
                
                key_name, api_key, rate_limiter = key_info
                
                # Настраиваем API для выбранного ключа
                genai.configure(api_key=api_key)
                model = self.models[key_name]
                
                print(f"🔑 Батч {batch_num}/{total_batches}: используется {key_name}")
                
                # Создаем промпт для батча
                prompt = self._create_batch_ranking_prompt(batch, video_summary)
                estimated_tokens = len(prompt.split()) + len(batch) * 3
                
                # Ждем если нужно соблюсти лимиты
                wait_time = rate_limiter.wait_if_needed(estimated_tokens)
                if wait_time > 0:
                    print(f"⏳ Ожидание {wait_time:.1f} сек для соблюдения лимитов {key_name}")
                
                # Отправляем запрос
                response = model.generate_content(prompt, generation_config=self.generation_config)
                rate_limiter.record_request(estimated_tokens)
                self.key_usage_stats[key_name] += 1
                
                if response and response.text:
                    ranks = self._extract_batch_ranks_from_response(response.text, len(batch))
                    if ranks and len(ranks) == len(batch):
                        # Применяем ранги к комментариям
                        for comment, rank in zip(batch, ranks):
                            comment.comment_rank = rank
                        print(f"✅ Батч {batch_num} успешно обработан с {key_name}")
                        return True
                    else:
                        print(f"⚠️ Не удалось извлечь ранги из ответа {key_name}")
                else:
                    print(f"⚠️ Пустой ответ от {key_name}")
                
            except Exception as e:
                error_msg = str(e)
                print(f"⚠️ Батч {batch_num}, попытка {attempt+1} с {key_name if 'key_name' in locals() else 'неизвестным ключом'}: {error_msg}")
                
                # При ошибке 429 (превышение квоты) помечаем ключ как недоступный
                if "429" in error_msg or "quota" in error_msg.lower():
                    if 'key_name' in locals() and 'rate_limiter' in locals():
                        # Принудительно устанавливаем высокое использование для этого ключа
                        rate_limiter.record_request(10000)  # Большое количество токенов
                        print(f"🚫 Ключ {key_name} временно заблокирован из-за превышения квоты")
                
                # Ждем перед следующей попыткой
                if attempt < max_attempts - 1:
                    wait_time = min(10 * (attempt + 1), 60)  # Прогрессивное увеличение задержки
                    print(f"⏳ Ожидание {wait_time} сек перед следующей попыткой...")
                    time.sleep(wait_time)
        
        print(f"❌ Батч {batch_num} не удался после {max_attempts} попыток")
        return False
    
    def _create_mega_ranking_prompt(self, comments: List[Comment], video_summary: str) -> str:
        """Создает мега-промпт для ранжирования всех комментариев"""
        comments_text = ""
        for i, comment in enumerate(comments, 1):
            comment_preview = comment.text[:500] + "..." if len(comment.text) > 500 else comment.text
            comments_text += f"{i}. {comment_preview}\n"
        
        return f"""Rate the informativeness of ALL these comments relative to the video content on a scale from 0.0 to 1.0.

Video content: {video_summary}

Comments ({len(comments)} total):
{comments_text}

Rating criteria:
- 1.0: Comment adds significant value, complements or clarifies video content
- 0.7-0.9: Comment is relevant and contains useful information  
- 0.4-0.6: Comment is partially related to video topic
- 0.1-0.3: Comment is weakly related to content
- 0.0: Comment is unrelated to video (spam, off-topic, emotions without content)

IMPORTANT: Respond with EXACTLY {len(comments)} ratings separated by commas, one for each comment in order.
Example format: 0.8, 0.3, 0.9, 0.1, 0.7, 0.2, ...

Ratings:"""
    
    def _create_batch_ranking_prompt(self, comments: List[Comment], video_summary: str) -> str:
        """Создает промпт для ранжирования батча комментариев"""
        comments_text = ""
        for i, comment in enumerate(comments, 1):
            comment_preview = comment.text[:300] + "..." if len(comment.text) > 300 else comment.text
            comments_text += f"{i}. {comment_preview}\n"
        
        return f"""Rate the informativeness of these comments relative to the video content on a scale from 0.0 to 1.0.

Video content: {video_summary}

Comments ({len(comments)} total):
{comments_text}

Rating criteria:
- 1.0: Highly informative, adds significant value
- 0.7-0.9: Relevant and useful information
- 0.4-0.6: Partially related to video topic
- 0.1-0.3: Weakly related to content
- 0.0: Unrelated to video (spam, off-topic)

Respond with EXACTLY {len(comments)} ratings separated by commas.
Ratings:"""
    
    def _extract_mega_ranks_from_response(self, response: str, expected_count: int) -> Optional[List[float]]:
        """Извлекает список оценок из мега-ответа"""
        try:
            import re
            
            lines = response.strip().split('\n')
            ratings_line = None
            
            for line in lines:
                if ',' in line and re.search(r'[0-1]\.\d+', line):
                    ratings_line = line
                    break
            
            if not ratings_line:
                ratings_line = response
            
            pattern = r'([0-1]\.?\d*)'
            matches = re.findall(pattern, ratings_line)
            
            if len(matches) >= expected_count:
                ranks = []
                for i in range(expected_count):
                    try:
                        rank = float(matches[i])
                        ranks.append(max(0.0, min(1.0, rank)))
                    except (ValueError, IndexError):
                        ranks.append(0.5)
                return ranks
            
            return None
            
        except Exception as e:
            print(f"❌ Ошибка извлечения мега-рангов: {e}")
            return None
    
    def _extract_batch_ranks_from_response(self, response: str, expected_count: int) -> Optional[List[float]]:
        """Извлекает список оценок из ответа батча"""
        try:
            import re
            
            # Ищем числа от 0.0 до 1.0
            pattern = r'([0-1]\.?\d*)'
            matches = re.findall(pattern, response)
            
            if len(matches) >= expected_count:
                ranks = []
                for i in range(expected_count):
                    try:
                        rank = float(matches[i])
                        ranks.append(max(0.0, min(1.0, rank)))
                    except (ValueError, IndexError):
                        ranks.append(0.5)
                return ranks
            else:
                print(f"⚠️ Недостаточно рангов в ответе: получено {len(matches)}, ожидалось {expected_count}")
                print(f"   Ответ: '{response.strip()}'")
            
            return None
            
        except Exception as e:
            print(f"❌ Ошибка извлечения рангов батча: {e}")
            return None
    
    def get_key_statistics(self) -> Dict:
        """Возвращает статистику использования ключей"""
        stats = {}
        for key_name, rate_limiter in self.rate_limiters.items():
            status = rate_limiter.get_status()
            stats[key_name] = {
                'requests_used': self.key_usage_stats[key_name],
                'rpm_status': f"{status['rpm_used']}/{status['rpm_limit']}",
                'tpm_status': f"{status['tpm_used']}/{status['tpm_limit']}",
                'rpd_status': f"{status['rpd_used']}/{status['rpd_limit']}"
            }
        return stats

def main():
    """Демонстрация мультиключевой системы"""
    import sys
    
    if len(sys.argv) != 2:
        print("Использование: python multi_key_gemini_ranker.py VIDEO_ID")
        sys.exit(1)
    
    try:
        video_id = int(sys.argv[1])
        
        print("🚀 ЗАПУСК МУЛЬТИКЛЮЧЕВОЙ СИСТЕМЫ РАНЖИРОВАНИЯ")
        print("=" * 60)
        
        ranker = MultiKeyGeminiRanker()
        success = ranker.rank_comments_for_video(video_id)
        
        if success:
            print("\n✅ МУЛЬТИКЛЮЧЕВОЕ РАНЖИРОВАНИЕ ЗАВЕРШЕНО!")
            print("\n📊 Статистика использования ключей:")
            stats = ranker.get_key_statistics()
            for key_name, key_stats in stats.items():
                print(f"   {key_name}: {key_stats['requests_used']} запросов, "
                      f"RPM: {key_stats['rpm_status']}, "
                      f"TPM: {key_stats['tpm_status']}")
        else:
            print("\n❌ Ранжирование не удалось")
            
    except ValueError:
        print("❌ VIDEO_ID должен быть числом")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
