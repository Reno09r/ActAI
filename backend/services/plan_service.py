from typing import List, Optional
from datetime import datetime, timedelta
import json
from sqlalchemy.ext.asyncio import AsyncSession

from repository.plan_repository import PlanRepository
from repository.milestone_repository import MilestoneRepository
from repository.task_repository import TaskRepository
from services.llm_service import LLMService
from models import Plan

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
        llm_response = await self.llm_service.generate_full_plan_step_by_step(
            user_objective=objective,
            desired_plan_duration=duration
        )
        plan_data = json.loads(llm_response)

        # Создаем план
        plan = await self.plan_repository.create_plan({
            "user_id": user_id,
            "title": plan_data["plan_title"],
            "description": plan_data["plan_summary"],
            "ai_generated_plan_overview": llm_response,
            "start_date": datetime.now(),
            "end_date": datetime.now() + timedelta(weeks=plan_data["estimated_total_duration_weeks"]),
            "estimated_duration_weeks": plan_data["estimated_total_duration_weeks"],
            "weekly_commitment_hours": plan_data["suggested_weekly_commitment_hours"],
            "difficulty_level": plan_data["difficulty_level"],
            "prerequisites": json.dumps(plan_data["prerequisites"])
        })

        # Создаем этапы
        for order, milestone_data in enumerate(plan_data["milestones"], 1):
            milestone = await self.milestone_repository.create_milestone({
                "plan_id": plan.id,
                "title": milestone_data["milestone_title"],
                "description": milestone_data["milestone_description"],
                "order": order
            })

            # Создаем задания для этапа
            for task_data in milestone_data["tasks"]:
                await self.task_repository.create_task({
                    "user_id": user_id,
                    "plan_id": plan.id,
                    "milestone_id": milestone.id,
                    "title": task_data["task_title"],
                    "description": task_data["task_description"],
                    "due_date": datetime.now() + timedelta(days=7),  # По умолчанию через неделю
                    "priority": task_data["task_priority"].lower(),
                    "estimated_hours": task_data["task_estimated_hours"],
                    "ai_suggestion": task_data["task_ai_suggestion"]
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