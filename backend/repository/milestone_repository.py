from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import List, Optional

from models import Milestone, Task

class MilestoneRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_milestone(self, milestone_data: dict) -> Milestone:
        milestone = Milestone(**milestone_data)
        self.session.add(milestone)
        await self.session.flush()
        await self.session.commit()
        await self.session.refresh(milestone)
        return milestone

    async def get_milestone_by_id(self, milestone_id: int) -> Optional[Milestone]:
        query = select(Milestone).where(Milestone.id == milestone_id).options(
            selectinload(Milestone.tasks)
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_milestone_tasks(self, milestone_id: int) -> List[Task]:
        query = select(Task).where(Task.milestone_id == milestone_id)
        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_plan_milestones(self, plan_id: int) -> List[Milestone]:
        query = select(Milestone).where(Milestone.plan_id == plan_id).options(
            selectinload(Milestone.tasks)
        )
        result = await self.session.execute(query)
        return result.scalars().all() 