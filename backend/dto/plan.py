from datetime import date, datetime
from typing import Optional, List, Annotated
from pydantic import StringConstraints, Field
from .base import TimestampedDTO

class PlanBase(TimestampedDTO):
    title: Annotated[str, StringConstraints(min_length=1, max_length=255)]
    description_goal: Optional[str] = None
    ai_generated_plan_overview: Optional[str] = None
    status: str = "active"
    start_date: date
    target_date: date
    progress_percentage: Annotated[float, Field(ge=0, le=10)] = 0.0
    tags: Optional[List[str]] = None

class PlanCreate(PlanBase):
    user_id: int

class PlanUpdate(PlanBase):
    pass

class PlanInDB(PlanBase):
    id: int
    user_id: int

class PlanResponse(PlanBase):
    id: int
    user_id: int 