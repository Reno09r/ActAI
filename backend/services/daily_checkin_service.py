from datetime import date
from typing import List, Optional, Dict
from fastapi import HTTPException
from repository.daily_checkin_repository import DailyCheckinRepository

class DailyCheckinService:
    def __init__(self, repository: DailyCheckinRepository):
        self.repository = repository

    async def create_daily_checkin(self, user_id: int, checkin_data: dict) -> dict:
        # Check if checkin already exists for this date
        existing_checkin = await self.repository.get_checkin_by_date(user_id, checkin_data['checkin_date'])
        if existing_checkin:
            raise HTTPException(status_code=400, detail="Check-in already exists for this date")

        # Validate productivity score
        if not 0 <= checkin_data.get('productivity_score', 0) <= 10:
            raise HTTPException(status_code=400, detail="Productivity score must be between 0 and 10")

        checkin = await self.repository.create_checkin(user_id, checkin_data)
        return checkin.__dict__

    async def get_daily_checkin(self, user_id: int, checkin_date: date) -> Optional[dict]:
        checkin = await self.repository.get_checkin_by_date(user_id, checkin_date)
        if not checkin:
            raise HTTPException(status_code=404, detail="Check-in not found")
        return checkin.__dict__

    async def update_daily_checkin(self, checkin_id: int, user_id: int, updates: dict) -> dict:
        # Validate productivity score if provided
        if 'productivity_score' in updates and not 0 <= updates['productivity_score'] <= 10:
            raise HTTPException(status_code=400, detail="Productivity score must be between 0 and 10")

        checkin = await self.repository.update_checkin(checkin_id, user_id, updates)
        if not checkin:
            raise HTTPException(status_code=404, detail="Check-in not found")
        return checkin.__dict__

    async def delete_daily_checkin(self, checkin_id: int, user_id: int) -> bool:
        success = await self.repository.delete_checkin(checkin_id, user_id)
        if not success:
            raise HTTPException(status_code=404, detail="Check-in not found")
        return True

    async def get_user_checkin_history(self, user_id: int, start_date: Optional[date] = None, end_date: Optional[date] = None) -> List[dict]:
        checkins = await self.repository.get_user_checkins(user_id, start_date, end_date)
        return [checkin.__dict__ for checkin in checkins]

    async def get_mood_analytics(self, user_id: int, start_date: Optional[date] = None, end_date: Optional[date] = None) -> Dict:
        return await self.repository.get_mood_statistics(user_id, start_date, end_date)

    async def get_productivity_insights(self, user_id: int, start_date: date, end_date: date) -> List[Dict]:
        return await self.repository.get_productivity_trends(user_id, start_date, end_date) 