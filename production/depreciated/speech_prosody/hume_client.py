# app/hume_client.py
import os
from hume import HumeStreamClient
from hume.models.config import ProsodyConfig

async def process_prosody(audio_data: bytes):
    client = HumeStreamClient(os.getenv("HUME_API_KEY"))
    config = ProsodyConfig()
    async with client.connect([config]) as socket:
        result = await socket.send_audio(audio_data)
    return result