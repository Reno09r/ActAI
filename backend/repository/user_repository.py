from typing import Optional, List
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from models.user import User
from dto.user import UserCreate, UserUpdate
from auth.security import verify_password

class UserRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, user_data: UserCreate) -> User:
        now = datetime.utcnow()
        db_user = User(
            email=user_data.email,
            username=user_data.username,
            is_active=user_data.is_active,
            password_hash=user_data.password,  # Note: password should be hashed in service layer
            created_at=now,
            updated_at=now
        )
        self.db.add(db_user)
        await self.db.commit()
        await self.db.refresh(db_user)
        return db_user

    async def get_by_id(self, user_id: int) -> Optional[User]:
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> Optional[User]:
        result = await self.db.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()

    async def get_by_username(self, username: str) -> Optional[User]:
        result = await self.db.execute(
            select(User).where(User.username == username)
        )
        return result.scalar_one_or_none()

    async def update(self, user_id: int, user_data: UserUpdate) -> Optional[User]:
        user = await self.get_by_id(user_id)
        if not user:
            return None

        update_data = user_data.model_dump(exclude_unset=True)
        if "password" in update_data:
            update_data["password_hash"] = update_data.pop("password")
        
        update_data["updated_at"] = datetime.utcnow()

        for key, value in update_data.items():
            setattr(user, key, value)

        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def delete(self, user_id: int) -> bool:
        user = await self.get_by_id(user_id)
        if not user:
            return False

        await self.db.delete(user)
        await self.db.commit()
        return True

    async def list_users(self, skip: int = 0, limit: int = 100) -> List[User]:
        result = await self.db.execute(
            select(User).offset(skip).limit(limit)
        )
        return result.scalars().all()

    async def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """Аутентификация пользователя по username и паролю"""
        user = await self.get_by_username(username)
        if not user:
            return None
        if not verify_password(password, user.password_hash):
            return None
        return user 