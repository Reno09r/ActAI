from sqlalchemy import Column, String, Text, Integer, ForeignKey, JSON
from sqlalchemy.orm import relationship
from .base import Base

class AiGeneratedContent(Base):
    __tablename__ = "ai_generated_content"

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    content_type = Column(String(50), nullable=False)  # e.g., "motivation", "advice", "plan"
    content = Column(Text, nullable=False)
    generated_text = Column(Text, nullable=False)
    model_used = Column(String(100), nullable=False)
    model_metadata = Column(JSON)  # Renamed from metadata to model_metadata
    
    # Relationships
    user = relationship("User", back_populates="ai_generated_content") 