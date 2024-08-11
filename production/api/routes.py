# api/routes.py
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from services.emotion_analysis import analyze_emotion
from services.storage import download_file
from typing import Callable

router = APIRouter()

class AnalysisRequest(BaseModel):
    file_path: str

class AnalysisResponse(BaseModel):
    message: str

def get_analyzer() -> Callable:
    return analyze_emotion

@router.post("/analyze", response_model=AnalysisResponse)
async def analyze(request: AnalysisRequest, analyzer: Callable = Depends(get_analyzer)):
    try:
        local_path = await download_file(request.file_path)
        result = await analyzer(local_path)
        return AnalysisResponse(message=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))