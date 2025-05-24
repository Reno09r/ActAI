from sqlalchemy import Column, String, Text, Date, Integer, ForeignKey, Float, UniqueConstraint
from sqlalchemy.orm import relationship
from .base import Base

class DailyCheckin(Base):
    __tablename__ = "daily_checkins"

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    checkin_date = Column(Date, nullable=False)
    mood = Column(String(50), index=True)
    reflection_notes = Column(Text)
    achievements_today = Column(Text)
    ai_motivational_quote = Column(Text)
    productivity_score = Column(Float)  # 0-10 scale
    
    # Relationships
    user = relationship("User", back_populates="daily_checkins")
    
    __table_args__ = (
        UniqueConstraint('user_id', 'checkin_date', name='uix_user_checkin_date'),
    ) 