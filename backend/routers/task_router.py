from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from datetime import datetime, timedelta
from enum import Enum

from database import get_db
from services.task_service import TaskService
from dto.plan import TaskResponse, TaskUpdate
from auth.dependencies import get_current_active_user
from models.user import User

router = APIRouter(prefix="/tasks", tags=["tasks"])

class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"

@router.put("/{task_id}", response_model=TaskResponse)
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
    status: TaskStatus,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Обновляет статус задания"""
    task_service = TaskService(db)
    task = await task_service.update_task_status(
        user_id=current_user.id,
        task_id=task_id,
        status=status.value
    )
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    return task

@router.get("/in-progress", response_model=List[TaskResponse])
async def get_in_progress_tasks(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Получает задачи в процессе выполнения"""
    task_service = TaskService(db)
    tasks = await task_service.get_tasks_by_status(
        user_id=current_user.id,
        status=TaskStatus.IN_PROGRESS.value
    )
    return tasks

@router.get("/today", response_model=List[TaskResponse])
async def get_today_tasks(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Получает задачи на сегодня"""
    task_service = TaskService(db)
    today = datetime.now().date()
    tasks = await task_service.get_tasks_by_date_range(
        user_id=current_user.id,
        start_date=today,
        end_date=today
    )
    return tasks

@router.get("/tomorrow", response_model=List[TaskResponse])
async def get_tomorrow_tasks(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Получает задачи до завтра"""
    task_service = TaskService(db)
    today = datetime.now().date()
    tomorrow = today + timedelta(days=1)
    tasks = await task_service.get_tasks_by_date_range(
        user_id=current_user.id,
        start_date=today,
        end_date=tomorrow
    )
    return tasks

@router.get("/upcoming", response_model=List[TaskResponse])
async def get_upcoming_tasks(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Получает задачи на следующие 3 дня"""
    task_service = TaskService(db)
    today = datetime.now().date()
    three_days_later = today + timedelta(days=3)
    tasks = await task_service.get_tasks_by_date_range(
        user_id=current_user.id,
        start_date=today,
        end_date=three_days_later
    )
    return tasks 