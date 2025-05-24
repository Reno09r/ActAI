from datetime import date
from typing import Annotated, Optional
from pydantic import confloat
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