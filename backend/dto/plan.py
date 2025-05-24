from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from pydantic import validator

class TaskBase(BaseModel):
    title: str
    description: Optional[str] = None
    due_date: datetime
    priority: str = "medium"
    estimated_hours: Optional[float] = None
    ai_suggestion: Optional[str] = None
    status: str = "pending"

class TaskCreate(TaskBase):
    pass

class TaskUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    due_date: Optional[datetime] = None
    priority: Optional[str] = Field(None, pattern="^(low|medium|high)$")
    estimated_hours: Optional[float] = Field(None, ge=0)
    actual_hours: Optional[float] = Field(None, ge=0)
    status: Optional[str] = Field(None, pattern="^(pending|in_progress|completed)$")

    @validator('actual_hours')
    def validate_actual_hours(cls, v, values):
        if v is not None and 'estimated_hours' in values and values['estimated_hours'] is not None:
            if v < values['estimated_hours']:
                raise ValueError('Фактическое время не может быть меньше предполагаемого')
        return v

class TaskResponse(TaskBase):
    id: int
    user_id: int
    plan_id: int
    milestone_id: int

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

class MilestoneUpdateRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)