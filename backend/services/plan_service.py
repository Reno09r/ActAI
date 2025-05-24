from typing import List, Optional
from datetime import datetime, timedelta
import json
from sqlalchemy.ext.asyncio import AsyncSession

from repository.plan_repository import PlanRepository
from repository.milestone_repository import MilestoneRepository
from repository.task_repository import TaskRepository
from services.llm_service import LLMService
from models import Plan, Task

def datetime_handler(obj):
    """Обработчик для сериализации datetime объектов в JSON"""
    if isinstance(obj, (datetime, timedelta)):
        return obj.isoformat()
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

class PlanService:
    def __init__(self, session: AsyncSession):
        self.plan_repository = PlanRepository(session)
        self.milestone_repository = MilestoneRepository(session)
        self.task_repository = TaskRepository(session)
        self.llm_service = LLMService.get_instance()

    async def generate_and_create_plan(
        self, 
        user_id: int, 
        objective: str, 
        duration: str
    ) -> Plan:
        """Генерирует план через LLM и создает его в БД"""
        # Получаем план от LLM
        plan_data = await self.llm_service.generate_full_plan_step_by_step(
            user_objective=objective,
            desired_plan_duration=duration
        )

        # Создаем план
        plan = await self.plan_repository.create_plan({
            "user_id": user_id,
            "title": plan_data["title"],
            "description": plan_data["description"],
            "start_date": plan_data["start_date"],
            "end_date": plan_data["end_date"],
            "estimated_duration_weeks": plan_data["estimated_duration_weeks"],
            "weekly_commitment_hours": plan_data["weekly_commitment_hours"],
            "difficulty_level": plan_data["difficulty_level"],
            "prerequisites": json.dumps(plan_data["prerequisites"])
        })

        # Создаем этапы
        for order, milestone_data in enumerate(plan_data["milestones"], 1):
            milestone = await self.milestone_repository.create_milestone({
                "plan_id": plan.id,
                "title": milestone_data["title"],
                "description": milestone_data["description"],
                "order": order
            })

            # Создаем задания для этапа
            for task_data in milestone_data["tasks"]:
                await self.task_repository.create_task({
                    "user_id": user_id,
                    "plan_id": plan.id,
                    "milestone_id": milestone.id,
                    "title": task_data["title"],
                    "description": task_data["description"],
                    "due_date": task_data["due_date"],
                    "priority": task_data["priority"],
                    "estimated_hours": task_data["estimated_hours"],
                    "ai_suggestion": task_data["ai_suggestion"]
                })

        return await self.plan_repository.get_plan_by_id(plan.id)

    async def get_user_plan(self, user_id: int, plan_id: int) -> Optional[Plan]:
        """Получает план пользователя"""
        plan = await self.plan_repository.get_plan_by_id(plan_id)
        if plan and plan.user_id == user_id:
            return plan
        return None

    async def get_user_plans(self, user_id: int) -> List[Plan]:
        """Получает все планы пользователя"""
        return await self.plan_repository.get_user_plans(user_id)

    async def update_plan(
        self,
        user_id: int,
        plan_id: int,
        plan_data: dict
    ) -> Optional[Plan]:
        """Обновляет план пользователя"""
        # Проверяем существование плана и права доступа
        plan = await self.get_user_plan(user_id, plan_id)
        if not plan:
            return None

        # Валидация данных
        if 'title' in plan_data and not plan_data['title'].strip():
            raise ValueError("Title cannot be empty")

        if 'description' in plan_data and len(plan_data['description']) > 1000:
            raise ValueError("Description is too long (max 1000 characters)")

        if 'prerequisites' in plan_data and len(plan_data['prerequisites']) > 2000:
            raise ValueError("Prerequisites text is too long (max 2000 characters)")

        # Обновляем план
        try:
            updated_plan = await self.plan_repository.update_plan(plan_id, plan_data)
            return updated_plan
        except Exception as e:
            raise Exception(f"Failed to update plan: {str(e)}")