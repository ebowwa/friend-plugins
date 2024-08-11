# app/routes.py
from fastapi import APIRouter, WebSocket, Query, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
import base64
from speech_prosody.models import AudioSegment
from speech_prosody.hume_client import process_prosody
from speech_prosody.websocket_manager import WebSocketManager
from speech_prosody.config import logger

router = APIRouter()
websocket_manager = WebSocketManager()

@router.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str, uid: str = Query(...)):
    await websocket_manager.connect(session_id, websocket)
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
            await websocket_manager.send_json(session_id, response)
    except Exception as e:
        logger.error(f"WebSocket Error: {e}")
    finally:
        websocket_manager.disconnect(session_id)

@router.post("/audio-upload")
async def audio_upload_endpoint(file: UploadFile = File(...), uid: str = Query(...)):
    try:
        contents = await file.read()
        prosody_result = await process_prosody(contents)
        return JSONResponse(content={"prosody_analysis": prosody_result})
    except Exception as e:
        logger.error(f"Audio Upload Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/setup-check")
async def setup_check():
    return JSONResponse(content={"is_setup_completed": True})