from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic_core import ErrorDetails
from sqlalchemy.orm import Session

from dependencies import get_user_service
from dto.user import LoginRequest, UserCreate, UserResponse
from .security import Token, create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES
from services.user_service import UserService
router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/login", response_model=Token)
async def login_for_access_token(
    login_data: LoginRequest,
    user_service: UserService = Depends(get_user_service),
):
    user = await user_service.authenticate_user(login_data.username, login_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_400_BAD_REQUEST: {"model": ErrorDetails, "description": "Validation Error"},
        # You could add other specific errors like 409 Conflict if you prefer for existing users
        # status.HTTP_409_CONFLICT: {"model": ErrorDetail, "description": "User already exists"},
    }
)
async def register_user(
    user_create: UserCreate,
    user_service: UserService = Depends(get_user_service),
):
    try:
        created_user = await user_service.create_user(user_create)
        return created_user
    except ValueError as e:
        # Catch the specific ValueError from the service and convert to HTTPException
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)  # The message from ValueError will be used as the detail
        )
