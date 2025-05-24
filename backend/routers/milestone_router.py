from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from database import get_db
from services.milestone_service import MilestoneService
from services.task_service import TaskService
from dto.plan import TaskResponse, MilestoneResponse, MilestoneUpdateRequest
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

@router.put("/{milestone_id}", response_model=MilestoneResponse)
async def update_milestone(
    milestone_id: int,
    milestone_data: MilestoneUpdateRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Обновляет этап"""
    milestone_service = MilestoneService(db)
    updated_milestone = await milestone_service.update_milestone(
        current_user.id,
        milestone_id, 
        milestone_data
    )
    if not updated_milestone:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Этап не найден или у вас нет прав на его изменение"
        )
    return updated_milestone 