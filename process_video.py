#!/usr/bin/env python3
"""
🚀 ПОЛНЫЙ ПАЙПЛАЙН ОБРАБОТКИ ВИДЕО COMDIG
Революционная система с мега-ранжированием комментариев

Включает:
- Загрузку комментариев YouTube
- Получение транскриптов
- Суммаризацию через LLM
- Мега-ранжирование комментариев с Gemini 2.0 Flash
- Fallback системы для надежности
"""

import sys
import os
import time
import json
from urllib.parse import urlparse, parse_qs
from youtube_comment_downloader import YoutubeCommentDownloader
from youtube_transcript_api import YouTubeTranscriptApi
import requests
from models import Video, Comment, get_db_session
from gemini_ranker import GeminiCommentRanker
from comment_ranker import CommentRanker
import re
from multi_key_gemini_ranker import MultiKeyGeminiRanker

class VideoProcessor:
    """Полный пайплайн обработки видео с мега-ранжированием"""
    
    def __init__(self, gemini_api_key: str = None):
        self.session = get_db_session()
        self.downloader = YoutubeCommentDownloader()
        self.gemini_api_key = gemini_api_key or os.getenv('GEMINI_API_KEY')
        
    def _save_comments_to_json(self, video_id: int, video_url: str, youtube_video_id: str):
        """Сохраняет комментарии в JSON файл с дополнительными полями"""
        try:
            print("💾 Сохраняю комментарии в JSON файл...")
            
            # Получаем комментарии из базы данных
            comments = self.session.query(Comment).filter_by(video_id=video_id).all()
            
            comments_data = []
            for comment in comments:
                # Формируем ссылку на комментарий в YouTube
                comment_url = f"https://www.youtube.com/watch?v={youtube_video_id}&lc={comment.comment_id}" if comment.comment_id else None
                
                comment_dict = {
                    "database_id": comment.id,  # ID в базе данных
                    "comment_id": comment.comment_id,
                    "video_url": video_url,  # Адрес исходного видео
                    "comment_url": comment_url,  # Ссылка на комментарий в YouTube
                    "author": comment.author,
                    "text": comment.text,
                    "likes": comment.likes,
                    "published_at": comment.published_at.isoformat() if comment.published_at else None,
                    "parent_id": comment.parent_id,
                    "comment_rank": comment.comment_rank
                }
                comments_data.append(comment_dict)
            
            # Сохраняем в файл
            with open("comments.json", "w", encoding="utf-8") as f:
                json.dump(comments_data, f, ensure_ascii=False, indent=2)
            
            print(f"✅ Сохранено {len(comments_data)} комментариев в comments.json")
            
        except Exception as e:
            print(f"❌ Ошибка сохранения комментариев в JSON: {e}")
    
    def _save_summary_to_json(self, video_id: int, video_url: str, youtube_video_id: str):
        """Сохраняет summary в JSON файл с дополнительными полями"""
        try:
            print("💾 Сохраняю summary в JSON файл...")
            
            # Получаем видео из базы данных
            video = self.session.query(Video).filter_by(id=video_id).first()
            if not video:
                print("❌ Видео не найдено в базе данных")
                return
            
            summary_data = {
                "database_video_id": video.id,  # ID исходного видео в базе
                "youtube_video_id": youtube_video_id,
                "video_title": video.title,  # Название видео
                "video_url": video_url,  # Адрес исходного видео
                "summary": video.summary,
                "created_at": video.upload_date
            }
            
            # Сохраняем в файл
            with open("summary.json", "w", encoding="utf-8") as f:
                json.dump(summary_data, f, ensure_ascii=False, indent=2)
            
            print("✅ Summary сохранен в summary.json")
            
        except Exception as e:
            print(f"❌ Ошибка сохранения summary в JSON: {e}")
    
    def process_video(self, video_url: str) -> bool:
        """
        Полная обработка видео: от URL до ранжированных комментариев
        
        Args:
            video_url: URL YouTube видео
            
        Returns:
            bool: True если обработка прошла успешно
        """
        print("🚀" + "="*70)
        print("🎯 ЗАПУСК ПОЛНОГО ПАЙПЛАЙНА ОБРАБОТКИ ВИДЕО")
        print("🏆 Революционная система с мега-ранжированием")
        print("="*72)
        
        try:
            # 1. Извлекаем video_id из URL
            video_id = self._extract_video_id(video_url)
            if not video_id:
                print("❌ Не удалось извлечь video_id из URL")
                return False
            
            print(f"📹 Video ID: {video_id}")
            print(f"🔗 URL: {video_url}")
            
            # 2. Проверяем, не обработано ли уже это видео
            existing_video = self.session.query(Video).filter_by(video_id=video_id).first()
            if existing_video:
                print(f"⚠️ Видео уже существует в БД (ID: {existing_video.id})")
                
                # Проверяем, есть ли необходимые данные
                has_transcript = existing_video.transcript is not None
                has_summary = existing_video.summary is not None
                
                print(f"📊 Статус данных:")
                print(f"   Транскрипт: {'✅' if has_transcript else '❌'}")
                print(f"   Summary: {'✅' if has_summary else '❌'}")
                
                # Если данных нет, обрабатываем как новое видео
                if not has_transcript or not has_summary:
                    print("🔄 Недостающие данные - запускаю полную обработку...")
                    
                    # Получаем транскрипт если его нет
                    if not has_transcript:
                        print("\n📝 ЭТАП 2: ПОЛУЧЕНИЕ ТРАНСКРИПТА")
                        print("-" * 40)
                        transcript = self._get_transcript(video_id)
                        
                        # Проверяем валидность транскрипта
                        if not transcript:
                            # Спрашиваем пользователя о ручном вводе summary
                            manual_summary = self._ask_user_for_manual_summary(video_id)
                            if not manual_summary:
                                print("\n❌ ОБРАБОТКА ОСТАНОВЛЕНА")
                                print("💡 Причина: Транскрипт недоступен, пользователь отказался от ручного ввода summary")
                                return False
                            
                            # Используем пользовательский summary
                            existing_video.transcript = None
                            existing_video.summary = manual_summary
                            print(f"\n✅ Используется пользовательский summary длиной {len(manual_summary)} символов")
                        else:
                            existing_video.transcript = transcript
                    else:
                        transcript = existing_video.transcript
                    
                    # Генерируем summary если его нет и есть транскрипт
                    if not has_summary and existing_video.transcript:
                        print("\n🤖 ЭТАП 3: ГЕНЕРАЦИЯ SUMMARY")
                        print("-" * 40)
                        summary = self._generate_summary(existing_video.transcript)
                        existing_video.summary = summary
                    
                    # Сохраняем изменения
                    self.session.commit()
                    print("✅ Данные видео обновлены")
                
                # Теперь запускаем ранжирование
                print("\n🚀 ЭТАП 5: МЕГА-РАНЖИРОВАНИЕ КОММЕНТАРИЕВ")
                print("-" * 40)
                ranking_success = self._rank_existing_video(existing_video.id)
                
                # Сохраняем JSON файлы после ранжирования
                print("\n💾 ЭТАП 6: СОХРАНЕНИЕ JSON ФАЙЛОВ")
                print("-" * 40)
                self._save_comments_to_json(existing_video.id, video_url, video_id)
                self._save_summary_to_json(existing_video.id, video_url, video_id)
                
                print("\n🎉" + "="*70)
                if ranking_success:
                    print("✅ ПОЛНАЯ ОБРАБОТКА ЗАВЕРШЕНА УСПЕШНО!")
                    print("🌟 Видео готово к использованию с ранжированными комментариями")
                else:
                    print("⚠️ ОБРАБОТКА ЗАВЕРШЕНА С ПРЕДУПРЕЖДЕНИЯМИ")
                    print("📊 Видео сохранено, но ранжирование может быть неполным")
                print("="*72)
                
                # Показываем результаты для существующего видео
                self._show_results(existing_video.id)
                
                return ranking_success
            
            # 3. Загружаем комментарии
            print("\n📥 ЭТАП 1: ЗАГРУЗКА КОММЕНТАРИЕВ")
            print("-" * 40)
            comments_data = self._download_comments(video_id)
            if not comments_data:
                print("❌ Не удалось загрузить комментарии")
                return False
            
            # 4. Получаем транскрипт
            print("\n📝 ЭТАП 2: ПОЛУЧЕНИЕ ТРАНСКРИПТА")
            print("-" * 40)
            transcript = self._get_transcript(video_id)
            
            # Проверяем валидность транскрипта
            if not transcript:
                # Спрашиваем пользователя о ручном вводе summary
                manual_summary = self._ask_user_for_manual_summary(video_id)
                if not manual_summary:
                    print("\n❌ ОБРАБОТКА ОСТАНОВЛЕНА")
                    print("💡 Причина: Транскрипт недоступен, пользователь отказался от ручного ввода summary")
                    return False
                
                # Используем пользовательский summary
                summary = manual_summary
                print(f"\n✅ Используется пользовательский summary длиной {len(summary)} символов")
                
                # Сохраняем видео с пустым транскриптом но с пользовательским summary
                print("\n💾 ЭТАП 3: СОХРАНЕНИЕ В БАЗУ ДАННЫХ")
                print("-" * 40)
                db_video_id = self._save_video_to_db(video_id, video_url, comments_data, None, summary)
                if not db_video_id:
                    print("❌ Не удалось сохранить в БД")
                    return False
            else:
                # 5. Генерируем summary из транскрипта
                print("\n🤖 ЭТАП 3: ГЕНЕРАЦИЯ SUMMARY")
                print("-" * 40)
                summary = self._generate_summary(transcript)
                
                # 6. Сохраняем видео в БД
                print("\n💾 ЭТАП 4: СОХРАНЕНИЕ В БАЗУ ДАННЫХ")
                print("-" * 40)
                db_video_id = self._save_video_to_db(video_id, video_url, comments_data, transcript, summary)
                if not db_video_id:
                    print("❌ Не удалось сохранить в БД")
                    return False
            
            # 7. МЕГА-РАНЖИРОВАНИЕ КОММЕНТАРИЕВ (только если есть summary)
            next_step = 4 if not transcript else 5
            print(f"\n🚀 ЭТАП {next_step}: МЕГА-РАНЖИРОВАНИЕ КОММЕНТАРИЕВ")
            print("-" * 40)
            ranking_success = self._rank_comments_mega(db_video_id)

            # Сохраняем JSON файлы после ранжирования
            next_step += 1
            print(f"\n💾 ЭТАП {next_step}: СОХРАНЕНИЕ JSON ФАЙЛОВ")
            print("-" * 40)
            self._save_comments_to_json(db_video_id, video_url, video_id)
            self._save_summary_to_json(db_video_id, video_url, video_id)
            
            print("\n🎉" + "="*70)
            if ranking_success:
                print("✅ ПОЛНАЯ ОБРАБОТКА ЗАВЕРШЕНА УСПЕШНО!")
                print("🌟 Видео готово к использованию с ранжированными комментариями")
            else:
                print("⚠️ ОБРАБОТКА ЗАВЕРШЕНА С ПРЕДУПРЕЖДЕНИЯМИ")
                print("📊 Видео сохранено, но ранжирование может быть неполным")
            print("="*72)
            
            # Показываем результаты
            self._show_results(db_video_id)
            
            return True
            
        except Exception as e:
            print(f"\n❌ КРИТИЧЕСКАЯ ОШИБКА: {e}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            self.session.close()
    
    def _extract_video_id(self, url: str) -> str:
        """Извлекает video_id из YouTube URL"""
        try:
            parsed_url = urlparse(url)
            if parsed_url.hostname in ['www.youtube.com', 'youtube.com']:
                return parse_qs(parsed_url.query)['v'][0]
            elif parsed_url.hostname == 'youtu.be':
                return parsed_url.path[1:]
            return None
        except:
            return None
    
    def _download_comments(self, video_id: str) -> list:
        """Загружает комментарии с YouTube"""
        try:
            print(f"📥 Загружаю комментарии для видео {video_id}...")
            comments = list(self.downloader.get_comments(video_id))
            print(f"✅ Загружено {len(comments)} комментариев")
            return comments
        except Exception as e:
            print(f"❌ Ошибка загрузки комментариев: {e}")
            return None
    
    def _get_transcript(self, video_id: str) -> str:
        """Получает транскрипт видео"""
        try:
            print(f"📝 Получаю транскрипт для видео {video_id}...")
            
            # Сначала пробуем получить обычные субтитры
            try:
                transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=['ru', 'en'])
                transcript = ' '.join([item['text'] for item in transcript_list])
                print(f"✅ Получен обычный транскрипт длиной {len(transcript)} символов")
                return transcript
            except:
                print("⚠️ Обычные субтитры недоступны, пробую автоматические...")
            
            # Если обычные не найдены, пробуем автоматически сгенерированные
            try:
                # Получаем список всех доступных транскриптов
                transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
                
                # Ищем автоматически сгенерированные субтитры
                for transcript in transcript_list:
                    if transcript.is_generated:
                        print(f"🤖 Найден автоматический транскрипт на языке: {transcript.language}")
                        transcript_data = transcript.fetch()
                        # Исправляем обращение к атрибутам FetchedTranscriptSnippet
                        transcript_text = ' '.join([item.text for item in transcript_data])
                        print(f"✅ Получен автоматический транскрипт длиной {len(transcript_text)} символов")
                        return transcript_text
                
                # Если автоматических нет, берем первый доступный
                for transcript in transcript_list:
                    print(f"📝 Использую доступный транскрипт на языке: {transcript.language}")
                    transcript_data = transcript.fetch()
                    # Исправляем обращение к атрибутам FetchedTranscriptSnippet
                    transcript_text = ' '.join([item.text for item in transcript_data])
                    print(f"✅ Получен транскрипт длиной {len(transcript_text)} символов")
                    return transcript_text
                    
            except Exception as e:
                print(f"⚠️ Ошибка получения автоматических субтитров: {e}")
            
            # Если ничего не найдено
            print("⚠️ Транскрипт недоступен")
            return None
            
        except Exception as e:
            print(f"⚠️ Общая ошибка получения транскрипта: {e}")
            print("❌ Транскрипт недоступен")
            return None
    
    def _generate_summary(self, transcript: str) -> str:
        """Генерирует summary через Gemini API"""
        try:
            # Проверяем валидность транскрипта
            if not transcript or not self._is_transcript_valid(transcript):
                print("❌ Невозможно сгенерировать summary: транскрипт недоступен")
                return None
                
            print("🤖 Генерирую summary через Gemini API...")
            
            # Если есть API ключ Gemini, используем его
            if self.gemini_api_key:
                try:
                    import google.generativeai as genai
                    genai.configure(api_key=self.gemini_api_key)
                    model = genai.GenerativeModel('gemini-2.0-flash-exp')
                    
                    # Создаем промпт для суммаризации
                    prompt = f"""Создай краткое содержание (summary) этого видео на основе транскрипта.
                    
Требования:
- Длина: 20-30 предложений
- Язык: English
- Основные темы и ключевые моменты
- Четкий и информативный стиль

Транскрипт:
{transcript[:100000]}...

Summary:"""
                    
                    response = model.generate_content(
                        prompt,
                        generation_config=genai.types.GenerationConfig(
                            temperature=0.3,
                            max_output_tokens=200,
                            top_p=0.8
                        )
                    )
                    
                    if response and response.text:
                        summary = response.text.strip()
                        print(f"✅ Сгенерирован summary через Gemini длиной {len(summary)} символов")
                        return summary
                    
                except Exception as e:
                    print(f"⚠️ Ошибка Gemini API: {e}")
            
            # Финальный fallback
            print("🔄 Использую fallback summary...")
            fallback_summary = f"Краткое содержание видео (первые 300 символов транскрипта): {transcript[:300]}..."
            print(f"✅ Создан fallback summary длиной {len(fallback_summary)} символов")
            return fallback_summary
            
        except Exception as e:
            print(f"❌ Ошибка генерации summary: {e}")
            return None
    
    def _save_video_to_db(self, video_id: str, url: str, comments_data: list, transcript: str, summary: str) -> int:
        """Сохраняет видео и комментарии в БД"""
        try:
            print("💾 Сохраняю видео в базу данных...")
            
            # Создаем запись видео
            video = Video(
                video_id=video_id,
                youtube_url=url,
                title=f"Video {video_id}",  # Можно улучшить, получив реальный title
                transcript=transcript,
                summary=summary
            )
            
            self.session.add(video)
            self.session.flush()  # Получаем ID
            
            print(f"✅ Видео сохранено с ID: {video.id}")
            
            # Сохраняем комментарии
            print(f"💬 Сохраняю {len(comments_data)} комментариев...")
            
            saved_count = 0
            skipped_count = 0
            
            for comment_data in comments_data:
                try:
                    # Обрабатываем разные форматы данных комментариев
                    if isinstance(comment_data, dict):
                        comment_id = comment_data.get('cid')  # Получаем cid как comment_id
                        author = comment_data.get('author', 'Unknown')
                        text = comment_data.get('text', '')
                        likes = parse_likes_count(comment_data.get('votes', 0))
                        # Пробуем парсить дату
                        published_at = None
                        if comment_data.get('time'):
                            try:
                                # Если есть time_parsed, используем его
                                if comment_data.get('time_parsed'):
                                    from datetime import datetime
                                    published_at = datetime.fromtimestamp(comment_data['time_parsed'])
                            except:
                                pass
                    else:
                        # Если это объект, пробуем получить атрибуты
                        comment_id = getattr(comment_data, 'cid', None)
                        author = getattr(comment_data, 'author', 'Unknown')
                        text = getattr(comment_data, 'text', '')
                        likes = parse_likes_count(getattr(comment_data, 'votes', 0))
                        published_at = None
                    
                    # Проверяем, существует ли уже комментарий с таким comment_id
                    if comment_id:
                        existing_comment = self.session.query(Comment).filter_by(comment_id=comment_id).first()
                        if existing_comment:
                            skipped_count += 1
                            continue
                    
                    comment = Comment(
                        comment_id=comment_id,  # Добавляем comment_id
                        video_id=video.id,
                        author=author,
                        text=text,
                        likes=likes,
                        published_at=published_at
                    )
                    self.session.add(comment)
                    saved_count += 1
                    
                except Exception as e:
                    print(f"⚠️ Ошибка обработки комментария: {e}")
                    skipped_count += 1
                    continue
            
            print(f"✅ Сохранено новых комментариев: {saved_count}")
            if skipped_count > 0:
                print(f"⏭️ Пропущено дубликатов/ошибок: {skipped_count}")
            
            self.session.commit()
            print(f"✅ Все данные сохранены в БД")
            
            return video.id
            
        except Exception as e:
            print(f"❌ Ошибка сохранения в БД: {e}")
            self.session.rollback()
            return None
    
    def _rank_comments_mega(self, video_id: int) -> bool:
        """Мега-ранжирование комментариев с мультиключевой поддержкой"""
        try:
            # Пробуем мультиключевую систему если доступно несколько ключей
            try:
                multi_ranker = MultiKeyGeminiRanker()
                if len(multi_ranker.api_keys) > 1:
                    print(f"🚀 Используется мультиключевая система ({len(multi_ranker.api_keys)} ключей)")
                    return multi_ranker.rank_comments_for_video(video_id)
            except Exception as e:
                print(f"⚠️ Мультиключевая система недоступна: {e}")
            
            # Fallback к обычной системе
            print("🔄 Переключение на обычную систему ранжирования...")
            if self.gemini_api_key:
                from gemini_ranker import GeminiCommentRanker
                ranker = GeminiCommentRanker(api_key=self.gemini_api_key)
                return ranker.rank_comments_for_video(video_id)
            else:
                print("⚠️ GEMINI_API_KEY не найден, используется fallback")
                from comment_ranker import CommentRanker
                ranker = CommentRanker()
                return ranker.rank_comments_for_video(video_id)
                
        except Exception as e:
            print(f"❌ Ошибка ранжирования: {e}")
            return False
    
    def _rank_existing_video(self, video_id: int) -> bool:
        """Ранжирует комментарии для уже существующего видео"""
        return self._rank_comments_mega(video_id)
    
    def _show_results(self, video_id: int):
        """Показывает результаты обработки"""
        try:
            print("\n📊" + "="*50)
            print("📈 РЕЗУЛЬТАТЫ ОБРАБОТКИ")
            print("="*52)
            
            # Статистика комментариев
            total_comments = self.session.query(Comment).filter_by(video_id=video_id).count()
            ranked_comments = self.session.query(Comment).filter(
                Comment.video_id == video_id,
                Comment.comment_rank.isnot(None)
            ).count()
            
            print(f"💬 Всего комментариев: {total_comments}")
            print(f"📊 Проранжировано: {ranked_comments}")
            print(f"✅ Успешность: {ranked_comments/total_comments*100:.1f}%")
            
            # Топ-5 комментариев
            top_comments = self.session.query(Comment).filter(
                Comment.video_id == video_id,
                Comment.comment_rank.isnot(None)
            ).order_by(Comment.comment_rank.desc()).limit(5).all()
            
            if top_comments:
                print(f"\n🏆 ТОП-5 КОММЕНТАРИЕВ:")
                print("-" * 40)
                for i, comment in enumerate(top_comments, 1):
                    print(f"\n{i}. Ранг: {comment.comment_rank:.3f}")
                    print(f"   Автор: {comment.author}")
                    print(f"   Текст: {comment.text[:60]}...")
            
            # Команды для дальнейшего использования
            print(f"\n🔧 КОМАНДЫ ДЛЯ РАБОТЫ С РЕЗУЛЬТАТАМИ:")
            print("-" * 40)
            print(f"# Показать все ранжированные комментарии:")
            print(f"docker-compose run --rm comments-downloader python -c \"from models import *; [print(f'{{c.comment_rank:.3f}}: {{c.text[:50]}}...') for c in get_db_session().query(Comment).filter_by(video_id={video_id}).filter(Comment.comment_rank.isnot(None)).order_by(Comment.comment_rank.desc()).all()]\"")
            
            print(f"\n# Финальная демонстрация:")
            print(f"docker-compose run --rm comments-downloader python final_demo.py --api-key=YOUR_KEY")
            
        except Exception as e:
            print(f"❌ Ошибка показа результатов: {e}")

    def _is_transcript_valid(self, transcript: str) -> bool:
        """Проверяет, является ли транскрипт валидным (не fallback сообщением)"""
        fallback_messages = [
            "Транскрипт недоступен для данного видео",
            "Транскрипт недоступен",
            ""
        ]
        return transcript and transcript.strip() not in fallback_messages and len(transcript.strip()) > 50

    def _ask_user_for_manual_summary(self, video_id: str) -> str:
        """Спрашивает пользователя, готов ли он предоставить summary вручную"""
        print("\n" + "="*70)
        print("⚠️ ТРАНСКРИПТ НЕДОСТУПЕН")
        print("="*70)
        print(f"📹 Видео ID: {video_id}")
        print("❌ Не удалось получить транскрипт для данного видео")
        print("🤖 Без транскрипта невозможно:")
        print("   • Сгенерировать качественный summary")
        print("   • Ранжировать комментарии по релевантности")
        print("="*70)
        
        while True:
            user_input = input("❓ Готовы ли вы предоставить summary видео самостоятельно? (yes/no): ").strip().lower()
            
            if user_input in ['yes', 'y', 'да', 'д']:
                print("\n📝 Введите summary видео:")
                print("💡 Рекомендации:")
                print("   • Опишите основные темы и ключевые моменты")
                print("   • Длина: 3-5 предложений")
                print("   • Используйте понятный язык")
                print("\n📝 Ваш summary (нажмите Enter дважды для завершения):")
                
                lines = []
                while True:
                    line = input()
                    if line == "" and lines:
                        break
                    lines.append(line)
                
                manual_summary = "\n".join(lines).strip()
                
                if manual_summary and len(manual_summary) > 20:
                    print(f"\n✅ Получен пользовательский summary длиной {len(manual_summary)} символов")
                    return manual_summary
                else:
                    print("❌ Summary слишком короткий. Попробуйте еще раз.")
                    continue
                    
            elif user_input in ['no', 'n', 'нет', 'н']:
                print("\n❌ Обработка остановлена пользователем")
                print("💡 Попробуйте найти видео с доступными субтитрами")
                return None
            else:
                print("❌ Пожалуйста, введите 'yes' или 'no'")


def parse_likes_count(likes_str):
    """Парсит количество лайков из строки YouTube"""
    if not likes_str or likes_str == '':
        return 0
    
    # Если это уже число
    if isinstance(likes_str, int):
        return likes_str
    
    # Преобразуем в строку
    likes_str = str(likes_str).strip()
    
    # Если пустая строка
    if not likes_str:
        return 0
    
    # Убираем пробелы и приводим к нижнему регистру
    likes_str = likes_str.lower().replace(' ', '')
    
    # Обрабатываем сокращения
    if 'тыс' in likes_str or 'k' in likes_str:
        # Извлекаем число перед "тыс" или "k"
        match = re.search(r'(\d+(?:[,\.]\d+)?)', likes_str)
        if match:
            number = match.group(1).replace(',', '.')
            return int(float(number) * 1000)
    
    if 'млн' in likes_str or 'm' in likes_str:
        # Извлекаем число перед "млн" или "m"
        match = re.search(r'(\d+(?:[,\.]\d+)?)', likes_str)
        if match:
            number = match.group(1).replace(',', '.')
            return int(float(number) * 1000000)
    
    # Пробуем извлечь просто число
    match = re.search(r'(\d+)', likes_str)
    if match:
        return int(match.group(1))
    
    # Если ничего не получилось
    return 0


def main():
    """Основная функция"""
    if len(sys.argv) < 2:
        print("🎬 Использование: python process_video.py <YOUTUBE_URL> [--api-key=GEMINI_KEY]")
        print("\n📝 Примеры:")
        print("  python process_video.py 'https://www.youtube.com/watch?v=VIDEO_ID'")
        print("  python process_video.py 'https://youtu.be/VIDEO_ID' --api-key=YOUR_GEMINI_KEY")
        return
    
    video_url = sys.argv[1]
    
    # Извлекаем API ключ
    gemini_api_key = None
    for arg in sys.argv:
        if arg.startswith("--api-key="):
            gemini_api_key = arg.split("=", 1)[1]
            break
    
    if not gemini_api_key:
        gemini_api_key = os.getenv('GEMINI_API_KEY')
    
    if not gemini_api_key:
        print("⚠️ API ключ Gemini не предоставлен")
        print("🔧 Будет использована fallback система ранжирования")
        print("💡 Для мега-ранжирования добавьте: --api-key=YOUR_GEMINI_KEY")
    
    try:
        processor = VideoProcessor(gemini_api_key)
        success = processor.process_video(video_url)
        
        if success:
            print("\n🎉 Обработка завершена успешно!")
        else:
            print("\n❌ Обработка завершена с ошибками")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\n⏹️ Обработка прервана пользователем")
    except Exception as e:
        print(f"\n💥 Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main() 