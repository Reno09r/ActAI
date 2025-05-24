from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from database import get_db
from services.task_service import TaskService
from dto.plan import TaskResponse, TaskUpdate
from auth.dependencies import get_current_active_user
from models.user import User

router = APIRouter(prefix="/tasks", tags=["tasks"])

@router.patch("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: int,
    task_data: TaskUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Обновляет задание"""
    task_service = TaskService(db)
    task = await task_service.update_task(
        user_id=current_user.id,
        task_id=task_id,
        task_data=task_data.dict(exclude_unset=True)
    )
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    return task

@router.patch("/{task_id}/status", response_model=TaskResponse)
async def update_task_status(
    task_id: int,
    status: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Обновляет статус задания"""
    task_service = TaskService(db)
    task = await task_service.update_task_status(
        user_id=current_user.id,
        task_id=task_id,
        status=status
    )
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    return task 