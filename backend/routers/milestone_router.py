from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from database import get_db
from services.milestone_service import MilestoneService
from services.task_service import TaskService
from dto.plan import TaskResponse
from auth.dependencies import get_current_active_user
from models.user import User

router = APIRouter(prefix="/milestones", tags=["milestones"])

@router.get("/{milestone_id}/tasks", response_model=List[TaskResponse])
async def get_milestone_tasks(
    milestone_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Получает все задания этапа"""
    task_service = TaskService(db)
    return await task_service.get_milestone_tasks(milestone_id) 