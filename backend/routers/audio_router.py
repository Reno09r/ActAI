import os
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from auth.dependencies import get_current_active_user
from models import User
from services.audio_service import AudioService
from database import get_db
from dto.audio import AudioResponse, TextRequest
from repository.audio_repository import AudioRepository

router = APIRouter(
    prefix="/audio",
    tags=["audio"],
)

def get_audio_repository():
    return AudioRepository()

def get_audio_service(
    db: Session = Depends(get_db),
    audio_repository: AudioRepository = Depends(get_audio_repository)
):
    return AudioService(db, audio_repository)

@router.post("/stt/", response_model=AudioResponse)
async def speech_to_text(
    audio_file: UploadFile = File(...),
    audio_service: AudioService = Depends(get_audio_service),
    current_user: User = Depends(get_current_active_user)
):
    """Преобразование аудио в текст без сохранения в БД."""
    try:
        return await audio_service.transcribe_audio(audio_file)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при обработке аудио: {str(e)}")

@router.post("/tts/", response_class=FileResponse)
async def text_to_speech(
    request: TextRequest,
    audio_service: AudioService = Depends(get_audio_service),
    current_user: User = Depends(get_current_active_user)
):
    """Преобразование текста в аудио без сохранения в БД."""
    try:
        await audio_service.change_speaker_gender(request.gender)
        file_path = await audio_service.create_audio_from_text(request.text)
        
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="Файл не найден")
            
        return FileResponse(
            path=file_path,
            media_type="audio/mpeg"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при генерации речи: {str(e)}")
