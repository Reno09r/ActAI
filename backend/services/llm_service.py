import asyncio
import logging
import threading
import sys
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple
from concurrent.futures import ThreadPoolExecutor
import json
import re
import time
from functools import wraps
import os
from openai import AsyncOpenAI
from datetime import datetime, timedelta
from collections import OrderedDict

# Добавляем путь к родительской директории
sys.path.append(str(Path(__file__).parent.parent))

# --- ДЕКОРАТОРЫ ДЛЯ МОНИТОРИНГА ---
def timing_decorator(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            elapsed = time.time() - start_time
            logging.info(f"{func.__name__} completed in {elapsed:.2f}s")
            return result
        except Exception as e:
            elapsed = time.time() - start_time
            logging.error(f"{func.__name__} failed after {elapsed:.2f}s: {str(e)}")
            raise
    return wrapper

def retry_on_failure(max_retries=2, delay=1.0):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries:
                        logging.warning(f"{func.__name__} failed (attempt {attempt + 1}/{max_retries + 1}): {str(e)}. Retrying in {delay}s...")
                        await asyncio.sleep(delay)
                    else:
                        logging.error(f"{func.__name__} failed after {max_retries + 1} attempts")
                        raise last_exception
        return wrapper
    return decorator

# --- УЛУЧШЕННЫЕ ПРОМПТЫ ---
STEP_1_BASIC_PLAN_PROMPT = """Create a detailed learning plan for: "{user_objective}"
Duration: {desired_plan_duration}

You must follow this EXACT format:

Title: [Clear, specific plan name]
Summary: [Brief 2-sentence description of what the learner will achieve]
Duration: [Only the number of weeks, like: 8]
Weekly: [Hours per week like: 8-10 hours]
Level: [Beginner, Intermediate, or Advanced]
Prerequisites:
- [Prerequisite 1]
- [Prerequisite 2]
- None (if no prerequisites)
Milestones:
- [Milestone 1 title]
- [Milestone 2 title]
- [Milestone 3 title]
- [Milestone 4 title]
END

Important rules:
1. For plans 1-2 weeks long, create only 2-3 milestones
2. For plans 3-4 weeks long, create 3-4 milestones
3. For plans longer than 4 weeks, create 4-5 milestones
4. Each milestone should represent a major learning achievement
5. Make sure milestones are evenly distributed across the plan duration"""

STEP_2_MILESTONE_DETAIL_PROMPT = """Plan: "{plan_title}"
Milestone to detail: "{milestone_title}"
Other milestones in plan: {all_milestone_titles_str}
Plan duration: {plan_duration} weeks

Create detailed information for this milestone. Follow this EXACT format:

Description: [2-3 sentences explaining what will be accomplished in this milestone and why it's important]
Tasks:
- [Specific task 1 - be concrete and actionable]
- [Specific task 2 - be concrete and actionable]  
- [Specific task 3 - be concrete and actionable]
- [Specific task 4 - be concrete and actionable]
END

Important rules:
1. For 1-2 week plans, create 2-3 tasks per milestone
2. For 3-4 week plans, create 3-4 tasks per milestone
3. For longer plans, create 4-5 tasks per milestone
4. Each task should be a clear, actionable item that contributes to completing the milestone
5. Tasks should be evenly distributed across the milestone's time period"""

STEP_3_TASK_DETAIL_PROMPT = """Milestone: "{milestone_title}"
Task to detail: "{task_title}"
Plan duration: {plan_duration} weeks

Provide specific details for this task. Follow this EXACT format:

Description: [2-3 sentences explaining exactly what needs to be done and how to approach it. Focus on building habits rather than daily tasks]
Priority: [High, Medium, or Low]
Hours: [Estimated hours as a number, like: 4]
Tip: [One practical tip or suggestion for completing this task successfully. Focus on habit formation and consistent progress]
END

Important rules:
1. Avoid phrases like "study every day" or "practice daily"
2. Instead, use phrases like "build a habit of", "develop a routine of", "establish a practice of"
3. Focus on sustainable learning habits rather than daily tasks
4. Be specific and actionable in your descriptions
5. Consider the overall plan duration when estimating hours"""

# Константы для расчета оптимального количества этапов
MIN_MILESTONES = 2
MAX_MILESTONES = 5
MIN_TASKS_PER_MILESTONE = 2
MAX_TASKS_PER_MILESTONE = 5
MIN_DAYS_BETWEEN_TASKS = 2

class OptimizedLLMService:
    _instance = None
    _plan_context = {}
    _initialization_lock = threading.Lock()
    _thread_pool = None
    
    # Константы для оптимизации
    MAX_WORKERS = 15  # Увеличиваем количество воркеров
    GENERATION_TIMEOUT = 30  # Оптимизируем таймаут
    CACHE_SIZE = 200  # Увеличиваем размер кэша
    CACHE_TTL = 3600  # TTL для кэша в секундах
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            with cls._initialization_lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    def __init__(self):
        """Оптимизированная инициализация"""
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY not found in environment variables. Please check your .env file and make sure it's properly configured.")
        
        self.client = AsyncOpenAI(api_key=api_key)
        
        if OptimizedLLMService._thread_pool is None:
            OptimizedLLMService._thread_pool = ThreadPoolExecutor(
                max_workers=self.MAX_WORKERS,
                thread_name_prefix="llm_worker"
            )
        
        self._cache = OrderedDict()
        self._cache_timestamps = {}
        logging.info("OptimizedLLMService initialized successfully")

    @classmethod
    def clear_context(cls):
        """Очищает контекст плана"""
        with cls._initialization_lock:
            cls._plan_context = {}
            logging.info("LLMService context cleared.")

    def _get_cache_key(self, prompt: str, max_tokens: int, temperature: float) -> str:
        """Создает ключ для кэширования"""
        return f"{hash(prompt)}_{max_tokens}_{temperature}"

    def _clean_cache(self):
        """Очищает устаревшие данные из кэша"""
        current_time = time.time()
        keys_to_remove = []
        
        for key, timestamp in self._cache_timestamps.items():
            if current_time - timestamp > self.CACHE_TTL:
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            del self._cache[key]
            del self._cache_timestamps[key]

    def _update_cache(self, key: str, value: Any):
        """Обновляет кэш с учетом TTL"""
        self._clean_cache()
        
        if len(self._cache) >= self.CACHE_SIZE:
            # Удаляем самый старый элемент
            oldest_key = next(iter(self._cache))
            del self._cache[oldest_key]
            del self._cache_timestamps[oldest_key]
        
        self._cache[key] = value
        self._cache_timestamps[key] = time.time()

    def _clean_llm_text_output(self, raw_text: str) -> str:
        """Улучшенная очистка текста"""
        if not raw_text:
            return ""
        
        text = raw_text.strip()
        
        # Убираем markdown форматирование
        markdown_prefixes = ["```text", "```", "```python", "```json"]
        for prefix in markdown_prefixes:
            if text.startswith(prefix):
                text = text[len(prefix):].strip()
                break
        
        if text.endswith("```"):
            text = text[:-3].strip()
            
        return text

    def _parse_step1_basic_plan_fast(self, text_response: str) -> Dict[str, Any]:
        """Улучшенный парсер для базового плана"""
        logging.debug(f"Parsing step 1 response: {text_response[:200]}...")
        
        data = {
            "plan_title": "Learning Plan", 
            "plan_summary": "A comprehensive learning plan",
            "estimated_total_duration_weeks": 4, 
            "suggested_weekly_commitment_hours": "5-8 hours",
            "difficulty_level": "Intermediate", 
            "prerequisites": [], 
            "milestone_titles_to_create": []
        }
        
        lines = text_response.split('\n')
        current_section = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            line_lower = line.lower()
            
            # Определяем секции
            if line_lower.startswith("title:"):
                data["plan_title"] = line.split(":", 1)[1].strip()
                current_section = None
            elif line_lower.startswith("summary:"):
                data["plan_summary"] = line.split(":", 1)[1].strip()
                current_section = None
            elif line_lower.startswith("duration:"):
                try:
                    duration_text = line.split(":", 1)[1].strip()
                    numbers = re.findall(r'\d+', duration_text)
                    if numbers:
                        data["estimated_total_duration_weeks"] = int(numbers[0])
                except (IndexError, ValueError) as e:
                    logging.warning(f"Failed to parse duration: {e}")
                current_section = None
            elif line_lower.startswith("weekly:"):
                data["suggested_weekly_commitment_hours"] = line.split(":", 1)[1].strip()
                current_section = None
            elif line_lower.startswith("level:"):
                data["difficulty_level"] = line.split(":", 1)[1].strip()
                current_section = None
            elif line_lower.startswith("prerequisites:"):
                current_section = "prerequisites"
                continue
            elif line_lower.startswith("milestones:"):
                current_section = "milestones"
                continue
            elif line_lower == "end":
                break
            elif line.startswith("- "):
                item = line[2:].strip()
                if current_section == "prerequisites":
                    if item.lower() not in ["none", "no prerequisites", "нет"]:
                        data["prerequisites"].append(item)
                elif current_section == "milestones":
                    if item:  # Проверяем что элемент не пустой
                        data["milestone_titles_to_create"].append(item)
        
        logging.debug(f"Parsed plan data: {data}")
        return data

    def _parse_step2_milestone_details_fast(self, text_response: str, milestone_title: str) -> Dict[str, Any]:
        """Улучшенный парсер для деталей этапа"""
        logging.debug(f"Parsing step 2 response for {milestone_title}: {text_response[:200]}...")
        
        data = {
            "milestone_title": milestone_title,
            "milestone_description": "Milestone description not provided",
            "task_titles_to_create": []
        }
        
        lines = text_response.split('\n')
        current_section = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            line_lower = line.lower()
            
            if line_lower.startswith("description:"):
                data["milestone_description"] = line.split(":", 1)[1].strip()
                current_section = None
            elif line_lower.startswith("tasks:"):
                current_section = "tasks"
                continue
            elif line_lower == "end":
                break
            elif line.startswith("- ") and current_section == "tasks":
                task = line[2:].strip()
                if task:  # Проверяем что задача не пустая
                    data["task_titles_to_create"].append(task)
        
        logging.debug(f"Parsed milestone data: {data}")
        return data

    def _parse_step3_task_details_fast(self, text_response: str, task_title: str) -> Dict[str, Any]:
        """Улучшенный парсер для деталей задачи"""
        logging.debug(f"Parsing step 3 response for {task_title}: {text_response[:200]}...")
        
        data = {
            "task_title": task_title,
            "task_description": "Task description not provided",
            "task_priority": "Medium",
            "task_estimated_hours": 2,
            "task_ai_suggestion": "Complete this task step by step"
        }
        
        lines = text_response.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            line_lower = line.lower()
            
            if line_lower.startswith("description:"):
                data["task_description"] = line.split(":", 1)[1].strip()
            elif line_lower.startswith("priority:"):
                priority = line.split(":", 1)[1].strip()
                if priority.lower() in ["high", "medium", "low"]:
                    data["task_priority"] = priority.capitalize()
            elif line_lower.startswith("hours:"):
                try:
                    hours_text = line.split(":", 1)[1].strip()
                    numbers = re.findall(r'\d+', hours_text)
                    if numbers:
                        data["task_estimated_hours"] = int(numbers[0])
                except (IndexError, ValueError) as e:
                    logging.warning(f"Failed to parse hours: {e}")
            elif line_lower.startswith("tip:"):
                data["task_ai_suggestion"] = line.split(":", 1)[1].strip()
            elif line_lower == "end":
                break
        
        logging.debug(f"Parsed task data: {data}")
        return data

    async def _generate_with_openai(self, prompt: str, max_tokens: int, temperature: float) -> str:
        """Асинхронная генерация через OpenAI API с кэшированием"""
        cache_key = self._get_cache_key(prompt, max_tokens, temperature)
        
        if cache_key in self._cache:
            logging.debug("Cache hit for prompt")
            return self._cache[cache_key]
        
        try:
            response = await self.client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=[
                    {
                        "role": "system", 
                        "content": "You are an expert learning plan creator. Always follow the exact format requested. Be specific, practical, and actionable in your responses."
                    },
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=0.9,
                frequency_penalty=0.0,
                presence_penalty=0.0
            )
            
            result = self._clean_llm_text_output(response.choices[0].message.content)
            self._update_cache(cache_key, result)
            logging.debug(f"OpenAI response: {result[:200]}...")
            return result
            
        except Exception as e:
            logging.error(f"OpenAI API error: {str(e)}")
            raise

    @timing_decorator
    @retry_on_failure(max_retries=2, delay=1.0)
    async def _llm_generate_step1_basic_plan(
        self, user_objective: str, desired_plan_duration: str, max_tokens: int = 800, temperature: float = 0.7
    ) -> Dict[str, Any]:
        """Генерация базового плана"""
        prompt = STEP_1_BASIC_PLAN_PROMPT.format(
            user_objective=user_objective, 
            desired_plan_duration=desired_plan_duration
        )
        
        response_text = await self._generate_with_openai(prompt, max_tokens, temperature)
        return self._parse_step1_basic_plan_fast(response_text)

    @timing_decorator
    @retry_on_failure(max_retries=2, delay=1.0)
    async def _llm_generate_step2_milestone_detail(
        self, user_objective: str, plan_title: str, milestone_title: str, 
        all_milestone_titles: List[str], max_tokens: int = 600, temperature: float = 0.7
    ) -> Dict[str, Any]:
        """Генерация деталей этапа"""
        prompt = STEP_2_MILESTONE_DETAIL_PROMPT.format(
            plan_title=plan_title,
            milestone_title=milestone_title,
            all_milestone_titles_str=", ".join(all_milestone_titles),
            plan_duration=len(all_milestone_titles)
        )
        
        response_text = await self._generate_with_openai(prompt, max_tokens, temperature)
        return self._parse_step2_milestone_details_fast(response_text, milestone_title)

    @timing_decorator  
    @retry_on_failure(max_retries=2, delay=1.0)
    async def _llm_generate_step3_task_detail(
        self, milestone_title: str, task_title: str, plan_duration_weeks: int, 
        max_tokens: int = 400, temperature: float = 0.7
    ) -> Dict[str, Any]:
        """Генерация деталей задачи"""
        prompt = STEP_3_TASK_DETAIL_PROMPT.format(
            milestone_title=milestone_title,
            task_title=task_title,
            plan_duration=plan_duration_weeks
        )
        
        response_text = await self._generate_with_openai(prompt, max_tokens, temperature)
        return self._parse_step3_task_details_fast(response_text, task_title)

    async def _generate_milestone_details_parallel(
        self, 
        user_objective: str, 
        plan_title: str, 
        milestone_titles: List[str],
        max_tokens: int = 600,
        temperature: float = 0.7
    ) -> List[Dict[str, Any]]:
        """Параллельная генерация деталей этапов"""
        tasks = []
        for milestone_title in milestone_titles:
            task = self._llm_generate_step2_milestone_detail(
                user_objective, plan_title, milestone_title,
                milestone_titles, max_tokens, temperature
            )
            tasks.append(task)
        
        return await asyncio.gather(*tasks, return_exceptions=True)

    async def _generate_task_details_parallel(
        self,
        milestone_title: str,
        task_titles: List[str],
        plan_duration_weeks: int,
        max_tokens: int = 400,
        temperature: float = 0.7
    ) -> List[Dict[str, Any]]:
        """Параллельная генерация деталей задач"""
        tasks = []
        for task_title in task_titles:
            task = self._llm_generate_step3_task_detail(
                milestone_title, task_title, plan_duration_weeks, max_tokens, temperature
            )
            tasks.append(task)
        
        return await asyncio.gather(*tasks, return_exceptions=True)

    def _calculate_optimal_milestones(self, plan_duration_weeks: int) -> int:
        """Рассчитывает оптимальное количество этапов в зависимости от длительности плана"""
        if plan_duration_weeks <= 2:
            return min(3, max(2, plan_duration_weeks))
        elif plan_duration_weeks <= 4:
            return min(4, max(3, plan_duration_weeks))
        else:
            return min(MAX_MILESTONES, max(MIN_MILESTONES, plan_duration_weeks // 2))

    def _calculate_optimal_tasks(self, plan_duration_weeks: int, milestone_index: int, total_milestones: int) -> int:
        """Рассчитывает оптимальное количество задач для этапа"""
        if plan_duration_weeks <= 2:
            return min(3, max(2, plan_duration_weeks))
        elif plan_duration_weeks <= 4:
            return min(4, max(3, plan_duration_weeks))
        else:
            return min(MAX_TASKS_PER_MILESTONE, max(MIN_TASKS_PER_MILESTONE, plan_duration_weeks // total_milestones))

    def _calculate_task_dates(self, start_date: datetime, end_date: datetime, 
                            milestone_index: int, total_milestones: int,
                            task_index: int, total_tasks: int,
                            task_priority: str = "Medium") -> datetime:
        """Рассчитывает дату выполнения задачи с учетом равномерного распределения и приоритета"""
        total_days = (end_date - start_date).days
        
        # Рассчитываем границы этапа
        milestone_duration = total_days / total_milestones
        milestone_start = start_date + timedelta(days=milestone_duration * milestone_index)
        milestone_end = milestone_start + timedelta(days=milestone_duration)
        
        # Определяем базовый интервал между задачами
        min_interval = max(MIN_DAYS_BETWEEN_TASKS, milestone_duration / (total_tasks + 1))
        
        # Корректируем интервал в зависимости от приоритета
        priority_multiplier = {
            "high": 0.8,  # Высокий приоритет - задачи ближе к началу этапа
            "medium": 1.0,  # Средний приоритет - равномерное распределение
            "low": 1.2   # Низкий приоритет - задачи ближе к концу этапа
        }.get(task_priority.lower(), 1.0)
        
        # Рассчитываем позицию задачи в этапе
        task_position = (task_index + 1) / (total_tasks + 1)
        task_position = task_position * priority_multiplier
        
        # Ограничиваем позицию в пределах этапа
        task_position = max(0.1, min(0.9, task_position))
        
        # Рассчитываем дату выполнения
        days_from_start = milestone_duration * task_position
        task_date = milestone_start + timedelta(days=days_from_start)
        
        # Проверяем минимальный интервал с предыдущей задачей
        if task_index > 0:
            min_date = milestone_start + timedelta(days=min_interval * task_index)
            task_date = max(task_date, min_date)
        
        # Проверяем, что дата не выходит за пределы этапа
        task_date = min(task_date, milestone_end - timedelta(days=1))
        
        return task_date

    @timing_decorator
    async def generate_full_plan_step_by_step(
        self, 
        user_objective: str, 
        desired_plan_duration: str,
        max_tokens_step1: int = 800,
        max_tokens_step2: int = 600, 
        max_tokens_step3: int = 400,
        temperature: float = 0.7
    ) -> Dict:
        """Генерация полного плана со всеми деталями с параллельной обработкой"""
        logging.info(f"Starting full plan generation for: '{user_objective}'")
        
        try:
            # Извлекаем количество недель из desired_plan_duration
            plan_duration_weeks = int(''.join(filter(str.isdigit, desired_plan_duration)))
            
            # Шаг 1: Базовый план
            logging.info("Step 1: Generating basic plan...")
            basic_plan = await self._llm_generate_step1_basic_plan(
                user_objective, desired_plan_duration, max_tokens_step1, temperature
            )
            
            # Ограничиваем количество этапов в зависимости от длительности плана
            optimal_milestones = self._calculate_optimal_milestones(plan_duration_weeks)
            milestone_titles = basic_plan.pop("milestone_titles_to_create", [])[:optimal_milestones]
            
            if not milestone_titles:
                logging.error("No milestones generated in step 1")
                return {
                    "error": "No milestones generated", 
                    "basic_plan": basic_plan
                }
            
            # Создаем структуру плана
            start_date = datetime.now()
            end_date = start_date + timedelta(weeks=plan_duration_weeks)
            
            plan = {
                "title": basic_plan["plan_title"],
                "description": basic_plan["plan_summary"],
                "estimated_duration_weeks": plan_duration_weeks,
                "weekly_commitment_hours": basic_plan["suggested_weekly_commitment_hours"],
                "difficulty_level": basic_plan["difficulty_level"],
                "prerequisites": basic_plan["prerequisites"],
                "start_date": start_date,
                "end_date": end_date,
                "progress_percentage": 0.0,
                "milestones": []
            }
            
            # Шаг 2: Параллельная генерация деталей этапов
            logging.info(f"Step 2: Generating details for {len(milestone_titles)} milestones in parallel...")
            milestone_details_list = await self._generate_milestone_details_parallel(
                user_objective, plan["title"], 
                milestone_titles, max_tokens_step2, temperature
            )
            
            # Обработка результатов этапов
            for i, milestone_details in enumerate(milestone_details_list):
                if isinstance(milestone_details, Exception):
                    logging.error(f"Failed to generate milestone '{milestone_titles[i]}': {milestone_details}")
                    continue
                
                # Ограничиваем количество задач для этапа
                optimal_tasks = self._calculate_optimal_tasks(
                    plan_duration_weeks, i, len(milestone_titles)
                )
                task_titles = milestone_details.get("task_titles_to_create", [])[:optimal_tasks]
                
                milestone = {
                    "title": milestone_details["milestone_title"],
                    "description": milestone_details["milestone_description"],
                    "order": i + 1,
                    "tasks": []
                }
                
                # Параллельная генерация задач для этапа
                if task_titles:
                    logging.info(f"Step 3: Generating {len(task_titles)} tasks for milestone '{milestone_titles[i]}' in parallel...")
                    task_details_list = await self._generate_task_details_parallel(
                        milestone_titles[i], task_titles, plan_duration_weeks, max_tokens_step3, temperature
                    )
                    
                    # Сортируем задачи по приоритету для правильного распределения дат
                    task_details_list = sorted(
                        [t for t in task_details_list if not isinstance(t, Exception)],
                        key=lambda x: {"high": 0, "medium": 1, "low": 2}.get(x.get("task_priority", "").lower(), 1)
                    )
                    
                    # Обработка результатов задач
                    for j, task_details in enumerate(task_details_list):
                        if isinstance(task_details, Exception):
                            logging.error(f"Failed to generate task '{task_titles[j]}': {task_details}")
                            continue
                            
                        # Рассчитываем дату выполнения задачи с учетом приоритета
                        task_date = self._calculate_task_dates(
                            start_date, end_date,
                            i, len(milestone_titles),
                            j, len(task_details_list),
                            task_details.get("task_priority", "Medium")
                        )
                            
                        task = {
                            "title": task_details["task_title"],
                            "description": task_details["task_description"],
                            "due_date": task_date,
                            "priority": task_details["task_priority"].lower(),
                            "estimated_hours": task_details["task_estimated_hours"],
                            "ai_suggestion": task_details["task_ai_suggestion"],
                            "status": "pending"
                        }
                        milestone["tasks"].append(task)
                
                plan["milestones"].append(milestone)
            
            logging.info("Full plan generation completed successfully")
            return plan
            
        except Exception as e:
            logging.error(f"Full plan generation failed: {str(e)}")
            return {
                "error": f"Plan generation failed: {str(e)}",
                "user_objective": user_objective,
                "desired_plan_duration": desired_plan_duration
            }

    def __del__(self):
        """Очистка ресурсов"""
        if hasattr(self, '_cache'):
            self._cache.clear()
            self._cache_timestamps.clear()

    # --- Методы для совместимости со старым API ---
    async def generate_basic_plan(
        self,
        user_objective: str,
        desired_plan_duration: str,
        max_tokens: int = 800,
        temperature: float = 0.7
    ) -> str:
        """Генерация базового плана (шаг 1)"""
        logging.info(f"Starting basic plan generation for: '{user_objective}'")
        
        self._plan_context = {
            "user_objective": user_objective,
            "desired_plan_duration": desired_plan_duration
        }
        
        basic_plan = await self._llm_generate_step1_basic_plan(
            user_objective, desired_plan_duration, max_tokens, temperature
        )
        
        self._plan_context["basic_plan"] = basic_plan
        return json.dumps(basic_plan, indent=2, ensure_ascii=False)

    async def generate_milestone_details(
        self,
        milestone_id: int,
        user_objective: str,
        desired_plan_duration: str,
        max_tokens: int = 600,
        temperature: float = 0.7
    ) -> str:
        """Генерация деталей этапа (шаг 2)"""
        if "basic_plan" not in self._plan_context:
            raise ValueError("Basic plan not found in context. Generate basic plan first.")
            
        basic_plan = self._plan_context["basic_plan"]
        milestone_titles = basic_plan.get("milestone_titles_to_create", [])
        
        if milestone_id >= len(milestone_titles):
            raise ValueError(f"Invalid milestone_id: {milestone_id}")
            
        milestone_title = milestone_titles[milestone_id]
        logging.info(f"Generating details for milestone: {milestone_title}")
        
        milestone_details = await self._llm_generate_step2_milestone_detail(
            user_objective, basic_plan["plan_title"], milestone_title,
            milestone_titles, max_tokens, temperature
        )
        
        if "milestones" not in self._plan_context:
            self._plan_context["milestones"] = {}
        self._plan_context["milestones"][milestone_id] = milestone_details
        
        return json.dumps(milestone_details, indent=2, ensure_ascii=False)

    async def generate_task_details(
        self,
        milestone_id: int,
        task_id: int,
        user_objective: str,
        desired_plan_duration: str,
        max_tokens: int = 400,
        temperature: float = 0.7
    ) -> str:
        """Генерация деталей задачи (шаг 3)"""
        if "milestones" not in self._plan_context or milestone_id not in self._plan_context["milestones"]:
            raise ValueError("Milestone not found in context. Generate milestone details first.")
            
        milestone = self._plan_context["milestones"][milestone_id]
        task_titles = milestone.get("task_titles_to_create", [])
        
        if task_id >= len(task_titles):
            raise ValueError(f"Invalid task_id: {task_id}")
            
        task_title = task_titles[task_id]
        logging.info(f"Generating details for task: {task_title} in milestone: {milestone['milestone_title']}")
        
        task_details = await self._llm_generate_step3_task_detail(
            milestone["milestone_title"], task_title, len(task_titles), max_tokens, temperature
        )
        
        if "tasks" not in self._plan_context:
            self._plan_context["tasks"] = {}
        if milestone_id not in self._plan_context["tasks"]:
            self._plan_context["tasks"][milestone_id] = {}
        self._plan_context["tasks"][milestone_id][task_id] = task_details
        
        return json.dumps(task_details, indent=2, ensure_ascii=False)

    async def generate_additional_info(
        self,
        milestone_id: int,
        user_objective: str,
        desired_plan_duration: str,
        max_tokens: int = 400,
        temperature: float = 0.7
    ) -> str:
        """Генерация дополнительной информации для этапа"""
        if "milestones" not in self._plan_context or milestone_id not in self._plan_context["milestones"]:
            raise ValueError("Milestone not found in context. Generate milestone details first.")
            
        milestone = self._plan_context["milestones"][milestone_id]
        
        additional_info_prompt = f"""
Plan: "{user_objective}"
Milestone: "{milestone['milestone_title']}"
Description: "{milestone['milestone_description']}"

Provide additional insights for this milestone:

FORMAT:
Insights:
- [Key insight 1]
- [Key insight 2]
Challenges:
- [Common challenge 1]
- [Common challenge 2]
Resources:
- [Helpful resource 1]
- [Helpful resource 2]
Tips:
- [Best practice 1]
- [Best practice 2]
END
        """
        
        response_text = await self._generate_with_openai(additional_info_prompt, max_tokens, temperature)
        
        if "additional_info" not in self._plan_context:
            self._plan_context["additional_info"] = {}
        self._plan_context["additional_info"][milestone_id] = response_text
        
        return json.dumps({"additional_info": response_text}, indent=2, ensure_ascii=False)


# Алиас для обратной совместимости
LLMService = OptimizedLLMService