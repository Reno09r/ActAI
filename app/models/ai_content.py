from sqlalchemy import Column, String, Text, ForeignKey, Integer, JSON
from sqlalchemy.orm import relationship
from .base import BaseModel

class AiGeneratedContent(BaseModel):
    __tablename__ = "ai_generated_content"

    user_id = Column(Integer, ForeignKey("users.id"))
    content_type = Column(String(100))
    prompt_text = Column(Text)
    generated_text = Column(Text)
    model_used = Column(String(100))
    
    # Новые поля
    metadata = Column(JSON)  # Дополнительные метаданные
    tokens_used = Column(Integer)
    processing_time = Column(Integer)  # в миллисекундах
    confidence_score = Column(Integer)  # 0-100
    feedback_score = Column(Integer)  # Пользовательская оценка
    context_data = Column(JSON)  # Контекстные данные, использованные для генерации

    # Relationships
    user = relationship("User", back_populates="ai_generated_content") 