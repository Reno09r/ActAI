from concurrent.futures import ThreadPoolExecutor
import os
import time
import asyncio
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
from typing import Tuple, Optional
from fastapi import UploadFile
from faster_whisper import WhisperModel
import re
import nltk
import numpy as np
import soundfile as sf
from sqlalchemy import select
import torch
from TTS.api import TTS
from sqlalchemy.orm import Session
from dto.audio import AudioResponse
from config import SAMPLE_RATE
from model_registry import get_tts_model, get_whisper_model, get_xtts_model
from repository.audio_repository import AudioRepository

class AudioService:
    def __init__(self, db_session: Session, audio_repository: AudioRepository):
        self.db = db_session
        self.audio_repository = audio_repository
        self.executor = ThreadPoolExecutor(max_workers=4)
        
        # Используем загруженные модели из registry вместо создания новых
        self.whisper_model = get_whisper_model()
        self.tts_model = get_tts_model()
        self.xtts_model = get_xtts_model()
        
        # Initialize NLTK for sentence tokenization
        nltk.download('punkt', quiet=True)
        
    async def transcribe_audio_async(self, file_path):
        """Asynchronously transcribe audio using faster-whisper."""
        print("🎙️ Transcribing audio...")
        start = time.perf_counter()
        
        try:
            # Run transcription in a separate thread since it's CPU/GPU intensive
            loop = asyncio.get_event_loop()
            segments, _ = await loop.run_in_executor(
                self.executor, 
                lambda: self.whisper_model.transcribe(file_path)
            )
            
            transcript = " ".join(segment.text for segment in segments)
            
            end = time.perf_counter()
            print(f"📜 Transcribed in {end-start:.2f}s: {transcript}")
            
            # Очищаем память GPU после использования
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
                torch.cuda.synchronize()  # Убеждаемся, что все операции завершены
                
            return transcript
            
        except Exception as e:
            print(f"Error in transcription: {str(e)}")
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            raise
    
    def process_non_speech_sounds(self, text):
        """Process non-speech sounds in the transcribed text."""
        # Implement your specific processing logic here
        # This is a placeholder that returns the original text
        return text
    
    async def process_non_speech_sounds_async(self, text):
        """Asynchronously process non-speech sounds in the transcribed text."""
        print("🔧 Processing non-speech sounds...")
        
        # If this is a lightweight operation, it could be done directly
        # For consistency or if it becomes more complex, use the executor
        loop = asyncio.get_event_loop()
        formatted_text = await loop.run_in_executor(
            self.executor,
            lambda: self.process_non_speech_sounds(text)
        )
        return formatted_text
    
    async def process_sentence(self, sentence, output_file=None):
        """Process a single sentence for TTS with Coqui TTS."""
        loop = asyncio.get_event_loop()
        
        # Process special pronunciation instructions in [brackets]
        if '[' in sentence and ']' in sentence:
            # Extract pronunciation instructions and remove brackets
            pattern = r'\[(.*?)\]'
            sentence = re.sub(pattern, r'\1', sentence)
        
        # Limit sentence length to reduce memory usage
        if len(sentence) > 200:
            sentence = sentence[:200]
        
        # Generate audio with Coqui TTS
        if output_file:
            # Generate directly to file
            await loop.run_in_executor(
                self.executor,
                lambda: self.tts_model.tts_to_file(
                    text=sentence,
                    file_path=output_file,
                    speaker=self.speaker
                )
            )
            # Read the file to get the audio array
            audio_array, _ = await loop.run_in_executor(
                self.executor,
                lambda: sf.read(output_file)
            )
        else:
            # Generate to waveform
            audio_array = await loop.run_in_executor(
                self.executor,
                lambda: self.tts_model.tts(
                    text=sentence,
                    speaker=self.speaker
                )
            )
        
        return audio_array
    
    def speed_up_audio(self, audio_array, speed_factor=1.15):
        """Speed up audio by simple resampling."""
        # Calculate new length based on speed factor
        new_length = int(len(audio_array) / speed_factor)
        # Resample the audio array
        indices = np.linspace(0, len(audio_array) - 1, new_length)
        indices = indices.astype(np.int32)
        return audio_array[indices]
    
    async def text_to_speech_async(self, text, output_file="response.mp3", speaker_wav=None, language="en"):
        """Asynchronously convert text to speech using XTTS or Coqui TTS."""
        print("🔊 Generating speech...")
        start = time.perf_counter()
        
        # Process text to better handle sentence breaks
        text = re.sub(r'(?<![.!?])\n', '. ', text)
        text = re.sub(r'\.(?! )', '. ', text)
        
        if speaker_wav:
            # Use XTTS for voice cloning
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                self.executor,
                lambda: self.xtts_model.tts_to_file(
                    text=text,
                    file_path=output_file,
                    speaker_wav=speaker_wav,
                    language=language,
                    split_sentences=True
                )
            )
        else:
            # Use regular Coqui TTS with optimized settings
            await self._text_to_speech_coqui_async(text, output_file)
        
        end = time.perf_counter()
        print(f"✅ Speech generated in {end-start:.2f}s, saved to {output_file}")
        return output_file

    async def _text_to_speech_coqui_async(self, text, output_file):
        """Internal method for Coqui TTS processing."""
        sentences = nltk.sent_tokenize(text)
        silence = np.zeros(int(0.15 * SAMPLE_RATE), dtype=np.float32)
        pieces = []
        
        if len(sentences) <= 1 and len(text) < 200:
            temp_file = f"{output_file}.temp.mp3"
            audio_array = await self.process_sentence(text, temp_file)
            
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                self.executor,
                lambda: sf.write(output_file, audio_array, SAMPLE_RATE)
            )
            
            if os.path.exists(temp_file):
                os.remove(temp_file)
        else:
            batch_size = 3
            for i in range(0, len(sentences), batch_size):
                batch = sentences[i:i+batch_size]
                batch_tasks = []
                
                for j, sentence in enumerate(batch):
                    if sentence.strip():
                        temp_file = f"{output_file}.{i+j}.temp.mp3"
                        task = asyncio.create_task(self.process_sentence(sentence, temp_file))
                        batch_tasks.append((task, temp_file))
                
                for task, temp_file in batch_tasks:
                    audio_array = await task
                    pieces.append(audio_array)
                    pieces.append(silence.copy())
                    
                    if os.path.exists(temp_file):
                        os.remove(temp_file)
            
            if pieces:
                loop = asyncio.get_event_loop()
                full_audio = await loop.run_in_executor(
                    self.executor,
                    lambda: np.concatenate(pieces).astype(np.float32)
                )
                
                await loop.run_in_executor(
                    self.executor,
                    lambda: sf.write(output_file, full_audio, SAMPLE_RATE)
                )
            else:
                print("Warning: No audio generated, possibly empty text input")
                full_audio = np.zeros(int(0.5 * SAMPLE_RATE), dtype=np.float32)
                await loop.run_in_executor(
                    self.executor,
                    lambda: sf.write(output_file, full_audio, SAMPLE_RATE)
                )

    async def transcribe_audio(self, audio_file: UploadFile) -> AudioResponse:
        """Преобразование аудио-файла в текст."""
        # Проверяем формат файла
        if not audio_file.filename.lower().endswith(('.mp3', '.wav', '.ogg', '.m4a')):
            raise ValueError(f"Неподдерживаемый формат файла: {audio_file.filename}. Поддерживаются: mp3, wav, ogg, m4a")
            
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
                raise ValueError(f"Ошибка при сохранении временного файла: {str(e)}")

        try:
            # Проверяем размер файла
            if os.path.getsize(temp_path) == 0:
                raise ValueError("Загружен пустой файл")

            # Выполняем преобразование речи в текст
            transcript = await self.transcribe_audio_async(temp_path)

            # Обрабатываем нерегулярные звуки, если необходимо
            processed_text = await self.process_non_speech_sounds_async(transcript)
            await asyncio.sleep(0.3)

            # Проверка на wake_word_check
            if "wake_word_check" in audio_file.filename:
                return AudioResponse(
                    processed_text=processed_text
                )

            return AudioResponse(
                processed_text=processed_text
            )

        except Exception as e:
            print(f"Ошибка при транскрибации: {str(e)}")
            raise

        finally:
            # Всегда удаляем временный файл
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    async def change_speaker_gender(self, gender: str):
        if gender == "W":
            self.speaker = "p225" 
        else:
            self.speaker = "p228" 

    async def create_audio_from_text(self, text: str) -> str:
        """Создание аудио из текста."""
        # Создаем временный файл
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as temp_file:
            output_filename = temp_file.name

        try:
            # Преобразуем текст в речь
            if self.speaker == "p228":
                await self.text_to_speech_async(text, output_file=output_filename, speaker_wav="segment-000.wav") 
            else:
                await self.text_to_speech_async(text, output_file=output_filename)
            
            return output_filename
        except Exception as e:
            # Удаляем временный файл в случае ошибки
            if os.path.exists(output_filename):
                os.unlink(output_filename)
            raise
    