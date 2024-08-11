# config.py
import os
from modal import Image, Secret

def load_config():
    return {
        "name": os.getenv("APP_NAME", "speech-coach"),
        "image": Image.debian_slim().pip_install(
            "uvicorn", "google-cloud-storage", "hume", "pydantic"
        ),
        "secrets": [Secret.from_name(s) for s in os.getenv("REQUIRED_SECRETS", "").split(',')],
        "function_config": {
            "keep_warm": int(os.getenv("KEEP_WARM", 1)),
            "timeout": int(os.getenv("TIMEOUT", 3600)),
        }
    }