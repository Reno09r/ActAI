from datetime import datetime
from typing import Any
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy import Column, DateTime, Integer
from sqlalchemy.ext.declarative import declarative_base

class CustomBase:
    @declared_attr
    def __tablename__(cls) -> str:
        return cls.__name__.lower()

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    deleted_at = Column(DateTime, nullable=True)

Base = declarative_base(cls=CustomBase) 