import asyncio
import os
from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket, Query, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import json
from hume import HumeStreamClient
from hume.models.config import ProsodyConfig
import logging
import base64

# Load environment variables
load_dotenv()

app = FastAPI()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Store active WebSocket connections
active_connections: Dict[str, WebSocket] = {}

class AudioSegment(BaseModel):
    audio_data: str  # Base64 encoded audio data
    start: float
    end: float

async def process_prosody(audio_data: bytes):
    client = HumeStreamClient(os.getenv("HUME_API_KEY"))
    config = ProsodyConfig()
    async with client.connect([config]) as socket:
        result = await socket.send_audio(audio_data)
    return result

@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str, uid: str = Query(...)):
    await websocket.accept()
    active_connections[session_id] = websocket
    try:
        while True:
            data = await websocket.receive_text()
            audio_segment = AudioSegment.parse_raw(data)
            audio_data = base64.b64decode(audio_segment.audio_data)
            prosody_result = await process_prosody(audio_data)
            response = {
                "segment": {
                    "start": audio_segment.start,
                    "end": audio_segment.end
                },
                "prosody_analysis": prosody_result
            }
            await websocket.send_json(response)
    except Exception as e:
        logger.error(f"WebSocket Error: {e}")
    finally:
        del active_connections[session_id]

@app.post("/audio-upload")
async def audio_upload_endpoint(file: UploadFile = File(...), uid: str = Query(...)):
    try:
        contents = await file.read()
        prosody_result = await process_prosody(contents)
        return JSONResponse(content={"prosody_analysis": prosody_result})
    except Exception as e:
        logger.error(f"Audio Upload Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/setup-check")
async def setup_check():
    # Here you would typically check if the plugin is properly set up
    # For demonstration, we'll assume it's always set up
    return JSONResponse(content={"is_setup_completed": True})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)