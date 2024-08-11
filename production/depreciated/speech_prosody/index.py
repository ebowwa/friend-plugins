# main.py
import uvicorn
from fastapi import FastAPI
from speech_prosody.routes import router
from speech_prosody.config import setup_logging

app = FastAPI()
app.include_router(router)

if __name__ == "__main__":
    setup_logging()
    uvicorn.run(app, host="0.0.0.0", port=8000)