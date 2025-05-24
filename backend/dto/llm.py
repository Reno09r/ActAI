from pydantic import BaseModel, Field
from typing import Optional

class ChatRequest(BaseModel):
    prompt: str
    context: str

class GeneratePlanRequest(BaseModel):
    user_objective: str = Field(..., description="Цель пользователя для плана обучения")
    desired_plan_duration: str = Field(..., description="Желаемая продолжительность плана (например, '4 недели', '2 месяца')")
    max_tokens_basic: int = Field(default=1000, description="Максимальное количество токенов для базового плана")
    max_tokens_milestone: int = Field(default=800, description="Максимальное количество токенов для деталей этапов")
    temperature: float = Field(default=0.5, description="Температура для генерации (0.0 - 1.0)") 