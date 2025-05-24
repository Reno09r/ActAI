from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date
from typing import List, Optional
from pydantic import BaseModel
from dto.daily_checkin import DailyCheckinResponse, DailyCheckinCreate, DailyCheckinUpdate
from database import get_db
from services.daily_checkin_service import DailyCheckinService
from repository.daily_checkin_repository import DailyCheckinRepository
from auth.dependencies import get_current_active_user

router = APIRouter(prefix="/daily-checkin", tags=["daily-checkin"])

@router.post("", response_model=DailyCheckinResponse)
async def create_checkin(
    checkin_data: DailyCheckinCreate,
    current_user = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    repository = DailyCheckinRepository(db)
    service = DailyCheckinService(repository)
    return await service.create_daily_checkin(current_user.id, checkin_data.dict())

@router.get("/history", response_model=List[DailyCheckinResponse])
async def get_checkin_history(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    current_user = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    repository = DailyCheckinRepository(db)
    service = DailyCheckinService(repository)
    return await service.get_user_checkin_history(current_user.id, start_date, end_date)

@router.get("/analytics/mood")
async def get_mood_analytics(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    current_user = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    repository = DailyCheckinRepository(db)
    service = DailyCheckinService(repository)
    return await service.get_mood_analytics(current_user.id, start_date, end_date)

@router.get("/analytics/productivity")
async def get_productivity_insights(
    start_date: date,
    end_date: date,
    current_user = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    repository = DailyCheckinRepository(db)
    service = DailyCheckinService(repository)
    return await service.get_productivity_insights(current_user.id, start_date, end_date)

@router.get("/{checkin_date}", response_model=DailyCheckinResponse)
async def get_checkin(
    checkin_date: date,
    current_user = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    repository = DailyCheckinRepository(db)
    service = DailyCheckinService(repository)
    return await service.get_daily_checkin(current_user.id, checkin_date)

@router.put("/{checkin_id}", response_model=DailyCheckinResponse)
async def update_checkin(
    checkin_id: int,
    updates: DailyCheckinUpdate,
    current_user = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    repository = DailyCheckinRepository(db)
    service = DailyCheckinService(repository)
    return await service.update_daily_checkin(checkin_id, current_user.id, updates.dict(exclude_unset=True))

@router.delete("/{checkin_id}")
async def delete_checkin(
    checkin_id: int,
    current_user = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    repository = DailyCheckinRepository(db)
    service = DailyCheckinService(repository)
    await service.delete_daily_checkin(checkin_id, current_user.id)
    return {"message": "Check-in deleted successfully"} 