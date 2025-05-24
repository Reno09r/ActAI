from datetime import date
from typing import Annotated, Optional
from pydantic import BaseModel, Field, confloat
from .base import TimestampedDTO

class DailyCheckinBase(TimestampedDTO):
    checkin_date: date
    mood: Optional[str] = None
    reflection_notes: Optional[str] = None
    achievements_today: Optional[str] = None
    ai_motivational_quote: Optional[str] = None
    productivity_score: Optional[Annotated[float, confloat(ge=0, le=10)]] = None

class DailyCheckinCreate(DailyCheckinBase):
    user_id: int

class DailyCheckinUpdate(DailyCheckinBase):
    pass

class DailyCheckinInDB(DailyCheckinBase):
    id: int
    user_id: int

class DailyCheckinResponse(DailyCheckinBase):
    id: int
    user_id: int 


class DailyCheckinCreate(BaseModel):
    checkin_date: date
    mood: Optional[str] = None
    reflection_notes: Optional[str] = None
    achievements_today: Optional[str] = None
    ai_motivational_quote: Optional[str] = None
    productivity_score: Optional[float] = Field(None, ge=0, le=10)

class DailyCheckinUpdate(BaseModel):
    mood: Optional[str] = None
    reflection_notes: Optional[str] = None
    achievements_today: Optional[str] = None
    ai_motivational_quote: Optional[str] = None
    productivity_score: Optional[float] = Field(None, ge=0, le=10)

class DailyCheckinResponse(BaseModel):
    id: int
    user_id: int
    checkin_date: date
    mood: Optional[str]
    reflection_notes: Optional[str]
    achievements_today: Optional[str]
    ai_motivational_quote: Optional[str]
    productivity_score: Optional[float]

    class Config:
        from_attributes = True