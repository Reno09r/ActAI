from typing import Tuple, Optional
from fastapi import UploadFile
import numpy as np
import soundfile as sf
import tempfile
import shutil
import os

class AudioRepository:
    def __init__(self):
        pass

    async def process_audio_file(self, audio_file: UploadFile) -> Tuple[str, np.ndarray]:
        """Обработка загруженного аудио файла в памяти."""
        # Создаем временный файл для обработки
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as temp_file:
            try:
                # Перемещаем указатель в начало файла
                await audio_file.seek(0)
                # Копируем содержимое
                shutil.copyfileobj(audio_file.file, temp_file)
                temp_path = temp_file.name
            except Exception as e:
                os.unlink(temp_file.name)
                raise ValueError(f"Ошибка при обработке аудио файла: {str(e)}")

        try:
            # Проверяем размер файла
            if os.path.getsize(temp_path) == 0:
                raise ValueError("Загружен пустой файл")

            # Читаем аудио данные
            audio_array, sample_rate = sf.read(temp_path)
            return temp_path, audio_array

        finally:
            # Удаляем временный файл
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    async def generate_audio(self, audio_array: np.ndarray, sample_rate: int) -> bytes:
        """Генерация аудио в памяти."""
        # Создаем временный файл для записи
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as temp_file:
            try:
                # Записываем аудио данные
                sf.write(temp_file.name, audio_array, sample_rate)
                
                # Читаем сгенерированный файл
                with open(temp_file.name, 'rb') as f:
                    audio_data = f.read()
                
                return audio_data
            finally:
                # Удаляем временный файл
                if os.path.exists(temp_file.name):
                    os.unlink(temp_file.name) 