import modal
import logging

logging.basicConfig(
    format="%(asctime)s %(levelname)-8s %(message)s",
    level=logging.INFO,
    datefmt="%Y-%m-%d %H:%M:%S",
)

app = modal.App(
    "speech-coach",
    image=modal.Image.debian_slim().pip_install(
        "uvicorn", "google-cloud-storage", "hume", "pydantic==1.10.11"
    ),
    secrets=[modal.Secret.from_name("friend-gcp"), modal.Secret.from_name("hume-ai")],
)


from modal import asgi_app
import fastapi
from fastapi import Request
from typing import Any


web_app = fastapi.FastAPI()


test_volume = modal.Volume.from_name("test", create_if_missing=True)


@app.function(
    keep_warm=1,
    timeout=60 * 60,
    volumes={"/test": test_volume},
)
@asgi_app()
def wrapper():
    return web_app


def analyze_emotion(filename: str):
    import os
    from hume import HumeBatchClient
    from hume.models.config import ProsodyConfig

    client = HumeBatchClient(os.environ["HUME_API_KEY"])
    filepaths = [filename]
    prosody_config = ProsodyConfig()
    job = client.submit_job(None, [prosody_config], files=filepaths)

    print("Running...", job)
    job.await_complete()
    print("Job completed with status: ", job.get_status())

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
    import base64
    import json
    import os
    from google.cloud import storage
    from google.oauth2 import service_account

    """
    Downloads a blob from the bucket.

    :param bucket_name: Name of the GCP bucket
    :param source_blob_name: Name of the file in the bucket
    :param destination_file_name: Path to where the file will be saved
    """
    credentials_json = base64.b64decode(
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"]
    ).decode("utf-8")
    credentials_info = json.loads(credentials_json)

    # Create credentials object
    credentials = service_account.Credentials.from_service_account_info(
        credentials_info
    )

    # Initialize the GCP Storage client with the credentials
    storage_client = storage.Client(credentials=credentials)

    # Get the bucket
    bucket = storage_client.bucket(bucket_name)
    print(bucket)
    # Get the blob (file) from the bucket
    blob = bucket.blob(source_blob_name)
    print(blob)

    # Download the file to the specified location
    blob.download_to_filename(destination_file_name)

    print(f"File {source_blob_name} downloaded to {destination_file_name}.")


@web_app.post("/memory")
async def memory(
    request: Request,
    uid: str,
):
    import json

    # Example usage:
    bucket_name = "speech-judge"
    source_blob_name = "recording-20240810_200556.wav"
    destination_file_name = "/test/downloaded_file.wav"
    download_blob(bucket_name, source_blob_name, destination_file_name)
    test_volume.commit()

    return {"message": analyze_emotion(destination_file_name)}
