# main.py
import modal
from fastapi import FastAPI
from config import load_config
from api.routes import router
from services.storage import initialize_storage

app_config = load_config()
app = modal.App(**app_config)

web_app = FastAPI()
web_app.include_router(router)

@app.function(**app_config.get('function_config', {}))
@modal.asgi_app()
def wrapper():
    return web_app