from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.orm import selectinload
from typing import List, Optional
from datetime import datetime

from models import Plan, Milestone, Task

class PlanRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_plan(self, plan_data: dict) -> Plan:
        plan = Plan(**plan_data)
        self.session.add(plan)
        await self.session.flush()
        await self.session.commit()
        await self.session.refresh(plan)
        return plan

    async def get_plan_by_id(self, plan_id: int) -> Optional[Plan]:
        query = select(Plan).where(Plan.id == plan_id).options(
            selectinload(Plan.milestones).selectinload(Milestone.tasks)
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_user_plans(self, user_id: int) -> List[Plan]:
        query = select(Plan).where(Plan.user_id == user_id).options(
            selectinload(Plan.milestones).selectinload(Milestone.tasks)
        )
        result = await self.session.execute(query)
        return result.scalars().all()

    async def update_plan(self, plan_id: int, plan_data: dict) -> Optional[Plan]:
        query = update(Plan).where(Plan.id == plan_id).values(**plan_data).returning(Plan)
        result = await self.session.execute(query)
        await self.session.commit()
        return result.scalar_one_or_none()

    async def delete_plan(self, plan_id: int) -> bool:
        query = delete(Plan).where(Plan.id == plan_id)
        result = await self.session.execute(query)
        await self.session.commit()
        return result.rowcount > 0

    async def create_milestone(self, milestone_data: dict) -> Milestone:
        milestone = Milestone(**milestone_data)
        self.session.add(milestone)
        await self.session.flush()
        return milestone

    async def create_task(self, task_data: dict) -> Task:
        task = Task(**task_data)
        self.session.add(task)
        await self.session.flush()
        return task

    async def get_plan_tasks(self, plan_id: int) -> List[Task]:
        query = select(Task).where(Task.plan_id == plan_id)
        result = await self.session.execute(query)
        return result.scalars().all()
