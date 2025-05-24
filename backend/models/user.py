from datetime import datetime
from sqlalchemy import Column, String, DateTime, Boolean
from sqlalchemy.orm import relationship
from .base import Base

class User(Base):
    __tablename__ = "users"  # Явно указываем имя таблицы

    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    username = Column(String(100), unique=True, index=True)
    is_active = Column(Boolean, default=True)
    last_login_at = Column(DateTime, nullable=True)
    
    # Relationships
    plans = relationship("Plan", back_populates="user", cascade="all, delete-orphan")
    tasks = relationship("Task", back_populates="user", cascade="all, delete-orphan")
    daily_checkins = relationship("DailyCheckin", back_populates="user", cascade="all, delete-orphan")
    ai_generated_content = relationship("AiGeneratedContent", back_populates="user", cascade="all, delete-orphan") 