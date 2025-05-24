from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class TaskBase(BaseModel):
    title: str
    description: Optional[str] = None
    due_date: datetime
    priority: str = "medium"
    estimated_hours: Optional[float] = None
    actual_hours: Optional[float] = None
    ai_suggestion: Optional[str] = None

class TaskCreate(TaskBase):
    pass

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    due_date: Optional[datetime] = None
    priority: Optional[str] = None
    estimated_hours: Optional[float] = None
    actual_hours: Optional[float] = None
    status: Optional[str] = None

class TaskResponse(TaskBase):
    id: int
    user_id: int
    plan_id: int
    milestone_id: int
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class MilestoneBase(BaseModel):
    title: str
    description: Optional[str] = None
    order: int

class MilestoneCreate(MilestoneBase):
    pass

class MilestoneResponse(MilestoneBase):
    id: int
    plan_id: int
    tasks: List[TaskResponse] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class PlanBase(BaseModel):
    title: str
    description: Optional[str] = None
    estimated_duration_weeks: Optional[int] = None
    weekly_commitment_hours: Optional[str] = None
    difficulty_level: Optional[str] = None
    prerequisites: Optional[str] = None

class PlanCreate(BaseModel):
    objective: str
    duration: str

class PlanUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    tags: Optional[str] = None
    estimated_duration_weeks: Optional[int] = None
    weekly_commitment_hours: Optional[str] = None
    difficulty_level: Optional[str] = None
    prerequisites: Optional[str] = None

class PlanResponse(PlanBase):
    id: int
    user_id: int
    ai_generated_plan_overview: Optional[str] = None
    status: str
    start_date: datetime
    end_date: datetime
    progress_percentage: float
    tags: Optional[str] = None
    milestones: List[MilestoneResponse] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True 