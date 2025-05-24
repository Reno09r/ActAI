from sqlalchemy import Column, String, Text, Integer, ForeignKey, DateTime, Float
from sqlalchemy.orm import relationship
from .base import Base

class Task(Base):
    __tablename__ = "tasks"

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    plan_id = Column(Integer, ForeignKey("plans.id", ondelete="CASCADE"), nullable=False)
    milestone_id = Column(Integer, ForeignKey("milestones.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    due_date = Column(DateTime, nullable=False)
    status = Column(String(50), default="pending")  # pending, in_progress, completed
    priority = Column(String(20), default="medium")  # low, medium, high
    estimated_hours = Column(Float)
    actual_hours = Column(Float)
    ai_suggestion = Column(Text)  # Для хранения AI подсказок
    
    # Relationships
    user = relationship("User", back_populates="tasks")
    plan = relationship("Plan", back_populates="tasks")
    milestone = relationship("Milestone", back_populates="tasks") 