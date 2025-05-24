from sqlalchemy import Column, String, Text, Integer, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base

class Milestone(Base):
    __tablename__ = "milestones"
    
    id = Column(Integer, primary_key=True)
    plan_id = Column(Integer, ForeignKey("plans.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    order = Column(Integer, nullable=False)  # Для сохранения порядка этапов
    
    # Relationships
    plan = relationship("Plan", back_populates="milestones")
    tasks = relationship("Task", back_populates="milestone", cascade="all, delete-orphan") 