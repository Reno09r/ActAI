from sqlalchemy import Column, String, Text, Date, Integer, ForeignKey, Float, DateTime
from sqlalchemy.orm import relationship
from .base import Base

class Plan(Base):
    __tablename__ = "plans"

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    ai_generated_plan_overview = Column(Text)
    status = Column(String(50), default="active", index=True)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    progress_percentage = Column(Float, default=0.0)
    tags = Column(String(255))  # Stored as comma-separated values
    
    # Relationships
    user = relationship("User", back_populates="plans")
    tasks = relationship("Task", back_populates="plan", cascade="all, delete-orphan") 