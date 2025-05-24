from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from models.daily_checkin import DailyCheckin
from datetime import date
from typing import List, Optional, Dict

class DailyCheckinRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_checkin(self, user_id: int, checkin_data: dict) -> DailyCheckin:
        checkin = DailyCheckin(user_id=user_id, **checkin_data)
        self.db.add(checkin)
        await self.db.commit()
        await self.db.refresh(checkin)
        return checkin

    async def get_checkin_by_date(self, user_id: int, checkin_date: date) -> Optional[DailyCheckin]:
        query = select(DailyCheckin).filter(
            DailyCheckin.user_id == user_id,
            DailyCheckin.checkin_date == checkin_date
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_user_checkins(self, user_id: int, start_date: Optional[date] = None, end_date: Optional[date] = None) -> List[DailyCheckin]:
        query = select(DailyCheckin).filter(DailyCheckin.user_id == user_id)
        if start_date:
            query = query.filter(DailyCheckin.checkin_date >= start_date)
        if end_date:
            query = query.filter(DailyCheckin.checkin_date <= end_date)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def update_checkin(self, checkin_id: int, user_id: int, updates: dict) -> Optional[DailyCheckin]:
        query = select(DailyCheckin).filter(
            DailyCheckin.id == checkin_id,
            DailyCheckin.user_id == user_id
        )
        result = await self.db.execute(query)
        checkin = result.scalar_one_or_none()
        
        if checkin:
            for key, value in updates.items():
                setattr(checkin, key, value)
            await self.db.commit()
            await self.db.refresh(checkin)
        return checkin

    async def delete_checkin(self, checkin_id: int, user_id: int) -> bool:
        query = select(DailyCheckin).filter(
            DailyCheckin.id == checkin_id,
            DailyCheckin.user_id == user_id
        )
        result = await self.db.execute(query)
        checkin = result.scalar_one_or_none()
        
        if checkin:
            await self.db.delete(checkin)
            await self.db.commit()
            return True
        return False

    async def get_mood_statistics(self, user_id: int, start_date: Optional[date] = None, end_date: Optional[date] = None) -> Dict:
        query = select(DailyCheckin).filter(DailyCheckin.user_id == user_id)
        if start_date:
            query = query.filter(DailyCheckin.checkin_date >= start_date)
        if end_date:
            query = query.filter(DailyCheckin.checkin_date <= end_date)
        result = await self.db.execute(query)
        checkins = result.scalars().all()
        
        mood_stats = {}
        for checkin in checkins:
            mood = checkin.mood
            mood_stats[mood] = mood_stats.get(mood, 0) + 1
        return mood_stats

    async def get_productivity_trends(self, user_id: int, start_date: date, end_date: date) -> List[Dict]:
        query = select(DailyCheckin).filter(
            DailyCheckin.user_id == user_id,
            DailyCheckin.checkin_date >= start_date,
            DailyCheckin.checkin_date <= end_date
        ).order_by(DailyCheckin.checkin_date)
        
        result = await self.db.execute(query)
        checkins = result.scalars().all()
        
        return [
            {
                "date": checkin.checkin_date,
                "productivity_score": checkin.productivity_score
            }
            for checkin in checkins
        ] 