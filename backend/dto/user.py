from datetime import datetime
from typing import Optional, Annotated
from pydantic import BaseModel, EmailStr, StringConstraints
from .base import BaseDTO

class UserBase(BaseDTO):
    email: EmailStr
    username: Optional[Annotated[str, StringConstraints(min_length=3, max_length=100)]] = None
    is_active: bool = True
    last_login_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class UserCreate(BaseDTO):
    email: EmailStr
    username: Optional[Annotated[str, StringConstraints(min_length=3, max_length=100)]] = None
    password: Annotated[str, StringConstraints(min_length=8)]
    is_active: bool = True

class UserUpdate(BaseDTO):
    email: Optional[EmailStr] = None
    username: Optional[Annotated[str, StringConstraints(min_length=3, max_length=100)]] = None
    password: Optional[Annotated[str, StringConstraints(min_length=8)]] = None
    is_active: Optional[bool] = None

class UserInDB(UserBase):
    id: int
    password_hash: str

class UserResponse(UserBase):
    id: int 

class LoginRequest(BaseModel):
    username: str
    password: str