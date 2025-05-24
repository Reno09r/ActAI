from datetime import date, datetime
from typing import Optional, List, Annotated
from pydantic import BaseModel, StringConstraints, Field
from .base import TimestampedDTO

class TaskBase(TimestampedDTO):
    title: Annotated[str, StringConstraints(min_length=1, max_length=255)]
    description: Optional[str] = None
    due_date: date
    status: str = "todo"
    priority: Annotated[int, Field(ge=0, le=5)] = 0
    ai_suggestion: Optional[str] = None
    completed_at: Optional[datetime] = None
    estimated_duration: Optional[float] = None
    tags: Optional[List[str]] = None

class TaskCreate(TaskBase):
    plan_id: int
    user_id: int

class TaskUpdate(TaskBase):
    pass

class TaskInDB(TaskBase):
    id: int
    plan_id: int
    user_id: int

class TaskResponse(TaskBase):
    id: int
    plan_id: int
    user_id: int 

class TaskAdaptationRequest(BaseModel):
    user_message: str 