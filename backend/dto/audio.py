from typing import Optional
from pydantic import BaseModel
from datetime import datetime


class TextRequest(BaseModel):
    text: str
    gender: str = "M"

class AudioResponse(BaseModel):
    processed_text: str
    file_path: Optional[str] = None