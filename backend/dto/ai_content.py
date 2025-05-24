from typing import Optional, Dict, Any, Annotated
from pydantic import StringConstraints
from .base import TimestampedDTO

class AiGeneratedContentBase(TimestampedDTO):
    content_type: Annotated[str, StringConstraints(min_length=1, max_length=100)]
    prompt_text: str
    generated_text: str
    model_used: Annotated[str, StringConstraints(min_length=1, max_length=100)]
    model_metadata: Optional[Dict[str, Any]] = None

class AiGeneratedContentCreate(AiGeneratedContentBase):
    user_id: Optional[int] = None

class AiGeneratedContentUpdate(AiGeneratedContentBase):
    pass

class AiGeneratedContentInDB(AiGeneratedContentBase):
    id: int
    user_id: Optional[int]

class AiGeneratedContentResponse(AiGeneratedContentBase):
    id: int
    user_id: Optional[int] 