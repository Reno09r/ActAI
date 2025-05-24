from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from database import get_db
from services.plan_service import PlanService
from dto.plan import PlanCreate, PlanResponse
from auth.dependencies import get_current_active_user
from models.user import User

router = APIRouter(prefix="/plans", tags=["plans"])

@router.post("/", response_model=PlanResponse)
async def create_plan(
    plan_data: PlanCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Создает новый план обучения"""
    plan_service = PlanService(db)
    try:
        plan = await plan_service.generate_and_create_plan(
            user_id=current_user.id,
            objective=plan_data.objective,
            duration=plan_data.duration
        )
        return plan
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/", response_model=List[PlanResponse])
async def get_user_plans(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Получает все планы пользователя"""
    plan_service = PlanService(db)
    return await plan_service.get_user_plans(current_user.id)

@router.get("/{plan_id}", response_model=PlanResponse)
async def get_plan(
    plan_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Получает план по ID"""
    plan_service = PlanService(db)
    plan = await plan_service.get_user_plan(current_user.id, plan_id)
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plan not found"
        )
    return plan 