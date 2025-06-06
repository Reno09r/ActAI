from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, date

from repository.task_repository import TaskRepository
from repository.plan_repository import PlanRepository
from repository.milestone_repository import MilestoneRepository
from services.llm_service import LLMService
from models import Task
from dto.plan import TaskResponse

class TaskService:
    def __init__(self, session: AsyncSession):
        self.task_repository = TaskRepository(session)
        self.plan_repository = PlanRepository(session)
        self.milestone_repository = MilestoneRepository(session)
        self.llm_service = LLMService.get_instance()

    async def update_task(
        self, 
        user_id: int, 
        task_id: int, 
        task_data: Dict[str, Any]
    ) -> Optional[Task]:
        """Обновляет задание"""
        task = await self.task_repository.get_task_by_id(task_id)
        if not task or task.user_id != user_id:
            return None

        # Удаляем системные поля
        task_data.pop('user_id', None)
        task_data.pop('plan_id', None)
        task_data.pop('milestone_id', None)
        task_data.pop('ai_suggestion', None)

        updated_task = await self.task_repository.update_task(task_id, task_data)
        if updated_task:
            await self._update_plan_progress(task.plan_id)
        return updated_task

    async def update_task_status(
        self, 
        user_id: int, 
        task_id: int, 
        status: str
    ) -> Optional[Task]:
        """Обновляет статус задания"""
        task = await self.task_repository.get_task_by_id(task_id)
        if not task or task.user_id != user_id:
            return None

        updated_task = await self.task_repository.update_task(task_id, {"status": status})
        if updated_task:
            await self._update_plan_progress(task.plan_id)
        return updated_task

    async def _update_plan_progress(self, plan_id: int) -> Optional[Task]:
        """Обновляет прогресс плана"""
        tasks = await self.task_repository.get_plan_tasks(plan_id)
        if not tasks:
            return None

        total_tasks = len(tasks)
        completed_tasks = sum(1 for task in tasks if task.status == "completed")
        progress = (completed_tasks / total_tasks) * 100 if total_tasks > 0 else 0

        return await self.plan_repository.update_plan(plan_id, {
            "progress_percentage": progress
        })

    async def get_milestone_tasks(self, milestone_id: int) -> List[Task]:
        """Получает все задания этапа"""
        return await self.task_repository.get_plan_tasks(milestone_id)

    async def get_tasks_by_date_range(
        self,
        user_id: int,
        start_date: date,
        end_date: date
    ) -> List[Task]:
        """Получает задачи в указанном диапазоне дат"""
        return await self.task_repository.get_tasks_by_date_range(
            user_id=user_id,
            start_date=start_date,
            end_date=end_date
        )

    async def get_tasks_by_status(
        self,
        user_id: int,
        status: str
    ) -> List[Task]:
        """Получает задачи по статусу"""
        return await self.task_repository.get_tasks_by_status(
            user_id=user_id,
            status=status
        )

    async def adapt_task(
        self,
        user_id: int,
        task_id: int,
        user_message: str
    ) -> Optional[TaskResponse]:
        """Адаптирует задачу на основе сообщения пользователя"""
        # Получаем задачу и проверяем права доступа
        task = await self.task_repository.get_task_by_id(task_id)
        if not task or task.user_id != user_id:
            return None
            
        # Получаем этап
        milestone = await self.milestone_repository.get_milestone_by_id(task.milestone_id)
        if not milestone:
            return None
            
        # Получаем рекомендации от ИИ
        adaptation = await self.llm_service.analyze_and_adapt_task(
            task=task,
            milestone=milestone,
            user_message=user_message
        )
        
        # Подготавливаем данные для обновления
        update_data = {
            "title": task.title,
            "description": task.description,
            "priority": adaptation["priority"].lower()
        }
        
        # Добавляем изменения из рекомендаций
        if adaptation["changes"]:
            update_data["description"] = (update_data["description"] or "") + "\n\nChanges:\n" + "\n".join(adaptation["changes"])
        
        # Обновляем сроки если они указаны
        if adaptation["new_timeline"]:
            try:
                new_date = datetime.fromisoformat(adaptation["new_timeline"][0])
                update_data["due_date"] = new_date
            except (ValueError, IndexError):
                pass
                
        # Обновляем задачу
        updated_task_data = await self.task_repository.adapt_task(task_id, update_data)
        if updated_task_data:
            await self._update_plan_progress(task.plan_id)
            return TaskResponse(**updated_task_data)
        return None 