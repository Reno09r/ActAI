from sqlalchemy import Column, String, Text, Date, Integer, ForeignKey, Float, DateTime
from sqlalchemy.orm import relationship
from .base import Base

class Plan(Base):
    __tablename__ = "plans"

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    status = Column(String(50), default="active", index=True)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    progress_percentage = Column(Float, default=0.0)
    tags = Column(String(255))  # Stored as comma-separated values
    
    # Новые поля для соответствия с LLM сервисом
    estimated_duration_weeks = Column(Integer)
    weekly_commitment_hours = Column(String(50))
    difficulty_level = Column(String(50))
    prerequisites = Column(Text)  # Stored as JSON string
    
    # Relationships
    user = relationship("User", back_populates="plans")
    milestones = relationship("Milestone", back_populates="plan", cascade="all, delete-orphan")
    tasks = relationship("Task", back_populates="plan", cascade="all, delete-orphan") 