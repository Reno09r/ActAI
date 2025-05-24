from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from repository.milestone_repository import MilestoneRepository
from models import Milestone

class MilestoneService:
    def __init__(self, session: AsyncSession):
        self.milestone_repository = MilestoneRepository(session)

    async def get_milestone_by_id(self, milestone_id: int) -> Optional[Milestone]:
        """Получает этап по ID"""
        return await self.milestone_repository.get_milestone_by_id(milestone_id)

    async def get_plan_milestones(self, plan_id: int) -> List[Milestone]:
        """Получает все этапы плана"""
        return await self.milestone_repository.get_plan_milestones(plan_id)

    async def create_milestone(self, milestone_data: dict) -> Milestone:
        """Создает новый этап"""
        return await self.milestone_repository.create_milestone(milestone_data) 