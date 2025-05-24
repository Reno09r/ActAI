from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from typing import List, Optional

from models import Task

class TaskRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_task(self, task_data: dict) -> Task:
        task = Task(**task_data)
        self.session.add(task)
        await self.session.flush()
        await self.session.commit()
        await self.session.refresh(task)
        return task

    async def get_task_by_id(self, task_id: int) -> Optional[Task]:
        query = select(Task).where(Task.id == task_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def update_task(self, task_id: int, task_data: dict) -> Optional[Task]:
        query = update(Task).where(Task.id == task_id).values(**task_data).returning(Task)
        result = await self.session.execute(query)
        await self.session.commit()
        return result.scalar_one_or_none()

    async def get_plan_tasks(self, plan_id: int) -> List[Task]:
        query = select(Task).where(Task.plan_id == plan_id)
        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_user_tasks(self, user_id: int) -> List[Task]:
        query = select(Task).where(Task.user_id == user_id)
        result = await self.session.execute(query)
        return result.scalars().all() 