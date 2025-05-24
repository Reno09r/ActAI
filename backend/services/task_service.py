from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, date

from repository.task_repository import TaskRepository
from repository.plan_repository import PlanRepository
from models import Task

class TaskService:
    def __init__(self, session: AsyncSession):
        self.task_repository = TaskRepository(session)
        self.plan_repository = PlanRepository(session)

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