# app/models.py
from pydantic import BaseModel

class AudioSegment(BaseModel):
    audio_data: str  # Base64 encoded audio data
    start: float
    end: float
