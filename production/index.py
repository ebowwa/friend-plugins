import modal
import logging
from fastapi import FastAPI, HTTPException, Request
from typing import Optional
import os
from hume import HumeBatchClient
from hume.models.config import ProsodyConfig
from google.cloud import storage
from google.oauth2 import service_account
import base64
import json

logging.basicConfig(format="%(asctime)s %(levelname)-8s %(message)s", level=logging.INFO, datefmt="%Y-%m-%d %H:%M:%S")

app = modal.App("speech-coach", 
                image=modal.Image.debian_slim().pip_install("uvicorn", "google-cloud-storage", "hume", "pydantic==1.10.11"),
                secrets=[modal.Secret.from_name("friend_gcp"), modal.Secret.from_name("HUME_API_KEY")])

web_app = FastAPI()
test_volume = modal.Volume.from_name("test", create_if_missing=True)

@app.function(keep_warm=1, timeout=60*60, volumes={"/test": test_volume})
@modal.asgi_app()
def wrapper():
    return web_app

def analyze_emotion(filename):
    client = HumeBatchClient(os.environ["HUME_API_KEY"])
    job = client.submit_job(None, [ProsodyConfig()], files=[filename])
    job.await_complete()
    
    emotion_scores = {}
    emotion_counts = {}
    full_predictions = job.get_predictions()
    for source in full_predictions:
        predictions = source["results"]["predictions"]
        for prediction in predictions:
            prosody_predictions = prediction["models"]["prosody"]["grouped_predictions"]
            for prosody_prediction in prosody_predictions:
                for segment in prosody_prediction["predictions"]:
                    for emotion in segment["emotions"]:
                        if emotion["name"] in emotion_scores:
                            emotion_scores[emotion["name"]] += emotion["score"]
                            emotion_counts[emotion["name"]] += 1
                        else:
                            emotion_scores[emotion["name"]] = emotion["score"]
                            emotion_counts[emotion["name"]] = 1
    sorted_emotions = sorted(emotion_scores.items(), key=lambda x: x[1], reverse=True)
    message = "Your speech was "
    emotion_messages = []
    for i in range(3):
        emotion = sorted_emotions[i][0]
        score = int(sorted_emotions[i][1] * 100 / emotion_counts[emotion])
        emotion_messages.append(f"{emotion} {score}%")
    message += ", ".join(emotion_messages)
    return message

def download_blob(bucket_name, source_blob_name, destination_file_name):
    credentials_json = base64.b64decode(os.environ["GOOGLE_APPLICATION_CREDENTIALS"]).decode("utf-8")
    credentials_info = json.loads(credentials_json)
    credentials = service_account.Credentials.from_service_account_info(credentials_info)
    storage_client = storage.Client(credentials=credentials)
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(source_blob_name)
    blob.download_to_filename(destination_file_name)
    logging.info(f"File {source_blob_name} downloaded to {destination_file_name}.")

@web_app.middleware("http")
async def log_requests(request: Request, call_next):
    logging.info(f"Request: {request.method} {request.url}")
    logging.info(f"Headers: {request.headers}")
    body = await request.body()
    logging.info(f"Body: {body.decode()}")
    response = await call_next(request)
    logging.info(f"Response Status: {response.status_code}")
    return response

@web_app.post("/")
async def root(request: Request):
    logging.info("Received request at root path")
    body = await request.json()
    
    uid = request.query_params.get("uid")
    transcript_segments = body.get("transcript_segments", [])
    
    if not transcript_segments:
        logging.error("No transcript segments found in request body")
        raise HTTPException(status_code=400, detail="No transcript segments provided")
    
    full_text = " ".join(segment["text"] for segment in transcript_segments)
    
    filename = f"{uid}_{body['id']}.txt"
    file_path = f"/test/{filename}"
    
    with open(file_path, "w") as f:
        f.write(full_text)
    
    logging.info(f"Saved transcript to {file_path}")
    
    try:
        analysis_result = analyze_emotion(file_path)
        logging.info(f"Analysis result: {analysis_result}")
        return {"message": analysis_result}
    except Exception as e:
        logging.error(f"Error analyzing emotion: {str(e)}")
        raise HTTPException(status_code=500, detail="Error analyzing audio file")

@web_app.post("/memory")
async def memory(request: Request, uid: str, filename: Optional[str] = None):
    logging.info(f"Received request - UID: {uid}, Filename: {filename}")
    if not filename:
        logging.error("Filename is missing")
        raise HTTPException(status_code=400, detail="Filename is required")
    
    try:
        download_blob("friend-hume-test", filename, f"/test/{filename}")
        test_volume.commit()
        logging.info(f"File downloaded: /test/{filename}")
        analysis_result = analyze_emotion(f"/test/{filename}")
        logging.info(f"Analysis result: {analysis_result}")
        return {"message": analysis_result}
    except Exception as e:
        logging.error(f"Error: {str(e)}")
        raise HTTPException(status_code=500, detail="Error processing request")

@web_app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def catch_all(request: Request, path: str):
    logging.error(f"404 Not Found: {request.method} {request.url}")
    raise HTTPException(status_code=404, detail="Not Found")