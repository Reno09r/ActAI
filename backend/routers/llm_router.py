from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from typing import List, Optional
from pathlib import Path
import shutil
import os
import sys
from pathlib import Path
import logging
import json

# Добавляем путь к корневой директории проекта
sys.path.append(str(Path(__file__).parent.parent))

from services.llm_service import LLMService
from auth.dependencies import get_current_user
from models.user import User
from dto.llm import ChatRequest, GeneratePlanRequest

# Конфигурация
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
ALLOWED_EXTENSIONS = {'.pdf'}

router = APIRouter(
    prefix="/api/llm",
    tags=["llm"]
)

# Создаем директорию для временного хранения файлов
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

# @router.post("/upload-book")
# async def upload_book(
#     file: UploadFile = File(...),
#     current_user: User = Depends(get_current_user)
# ):
#     """
#     Загрузка книги в формате PDF
#     """
#     try:
#         # Проверка расширения файла
#         file_extension = Path(file.filename).suffix.lower()
#         if file_extension not in ALLOWED_EXTENSIONS:
#             raise HTTPException(
#                 status_code=400,
#                 detail=f"Разрешены только файлы с расширениями: {', '.join(ALLOWED_EXTENSIONS)}"
#             )
        
#         # Проверка размера файла
#         file_size = 0
#         chunk_size = 1024 * 1024  # 1 MB
#         while chunk := await file.read(chunk_size):
#             file_size += len(chunk)
#             if file_size > MAX_FILE_SIZE:
#                 raise HTTPException(
#                     status_code=400,
#                     detail=f"Размер файла превышает максимально допустимый ({MAX_FILE_SIZE / 1024 / 1024} MB)"
#                 )
        
#         # Сбрасываем позицию чтения файла
#         await file.seek(0)
        
#         # Сохраняем файл
#         file_path = UPLOAD_DIR / file.filename
#         with file_path.open("wb") as buffer:
#             shutil.copyfileobj(file.file, buffer)
        
#         # Загружаем книгу в индекс
#         llm_service = LLMService.get_instance()
#         success = await llm_service.load_book(str(file_path))
        
#         if not success:
#             # Удаляем файл в случае ошибки
#             os.remove(file_path)
#             raise HTTPException(status_code=500, detail="Не удалось загрузить книгу в индекс")
        
#         return {"message": "Книга успешно загружена"}
    
#     except HTTPException:
#         raise
#     except Exception as e:
#         logging.error(f"Ошибка при загрузке книги: {str(e)}", exc_info=True)
#         raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера при загрузке книги")

@router.post("/generate-plan")
async def generate_plan(
    request: GeneratePlanRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Генерация полного плана обучения с помощью ИИ-коуча
    """
    try:
        llm_service = LLMService.get_instance()
        response = await llm_service.generate_full_plan_step_by_step(
            user_objective=request.user_objective,
            desired_plan_duration=request.desired_plan_duration,
            max_tokens_step1=request.max_tokens_basic,
            max_tokens_step2=request.max_tokens_milestone,
            max_tokens_step3=request.max_tokens_milestone,
            temperature=request.temperature
        )
        return json.loads(response)
    except Exception as e:
        logging.error(f"Ошибка при генерации плана: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера при генерации плана")

@router.post("/generate-plan/step1")
async def generate_basic_plan(
    request: GeneratePlanRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Генерация базового плана (шаг 1)
    """
    try:
        llm_service = LLMService.get_instance()
        response = await llm_service.generate_basic_plan(
            user_objective=request.user_objective,
            desired_plan_duration=request.desired_plan_duration,
            max_tokens=request.max_tokens_basic,
            temperature=request.temperature
        )
        return json.loads(response)
    except Exception as e:
        logging.error(f"Ошибка при генерации базового плана: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера при генерации базового плана")

@router.post("/generate-plan/step2/{milestone_id}")
async def generate_milestone_details(
    milestone_id: int,
    request: GeneratePlanRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Генерация деталей этапа (шаг 2)
    """
    try:
        llm_service = LLMService.get_instance()
        response = await llm_service.generate_milestone_details(
            milestone_id=milestone_id,
            user_objective=request.user_objective,
            desired_plan_duration=request.desired_plan_duration,
            max_tokens=request.max_tokens_milestone,
            temperature=request.temperature
        )
        return json.loads(response)
    except Exception as e:
        logging.error(f"Ошибка при генерации деталей этапа: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера при генерации деталей этапа")

@router.post("/generate-plan/step3/{milestone_id}/{task_id}")
async def generate_task_details(
    milestone_id: int,
    task_id: int,
    request: GeneratePlanRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Генерация деталей задачи (шаг 3)
    """
    try:
        llm_service = LLMService.get_instance()
        response = await llm_service.generate_task_details(
            milestone_id=milestone_id,
            task_id=task_id,
            user_objective=request.user_objective,
            desired_plan_duration=request.desired_plan_duration,
            max_tokens=request.max_tokens_milestone,
            temperature=request.temperature
        )
        return json.loads(response)
    except Exception as e:
        logging.error(f"Ошибка при генерации деталей задачи: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера при генерации деталей задачи")

@router.post("/generate-plan/additional/{milestone_id}")
async def generate_additional_info(
    milestone_id: int,
    request: GeneratePlanRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Генерация дополнительной информации для этапа
    """
    try:
        llm_service = LLMService.get_instance()
        response = await llm_service.generate_additional_info(
            milestone_id=milestone_id,
            user_objective=request.user_objective,
            desired_plan_duration=request.desired_plan_duration,
            max_tokens=request.max_tokens_milestone,
            temperature=request.temperature
        )
        return json.loads(response)
    except Exception as e:
        logging.error(f"Ошибка при генерации дополнительной информации: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера при генерации дополнительной информации")

# @router.get("/books")
# async def get_books(
#     current_user: User = Depends(get_current_user)
# ):
#     """
#     Получение списка загруженных книг
#     """
#     try:
#         llm_service = LLMService.get_instance()
#         books = llm_service.get_books()
#         return {"books": books}
#     except Exception as e:
#         logging.error(f"Ошибка при получении списка книг: {str(e)}", exc_info=True)
#         raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера при получении списка книг") 