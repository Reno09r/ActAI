"""
Routers package initialization
""" 

from .user_router import router as user_router
from .plan_router import router as plan_router 
from .task_router import router as task_router
from .milestone_router import router as milestone_router
from .audio_router import router as audio_router

__all__ = [
    "user_router",
    "plan_router",
    "task_router",
    "milestone_router",
    "audio_router"
]