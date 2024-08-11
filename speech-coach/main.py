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


@app.function(keep_warm=1, timeout=60 * 60)
@asgi_app()
def wrapper():
    return web_app


def print_emotions(emotions: list[dict[str, Any]]) -> None:
    emotion_map = {e["name"]: e["score"] for e in emotions}
    for emotion in ["Joy", "Sadness", "Anger"]:
        print(f"- {emotion}: {emotion_map[emotion]:4f}")


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

    full_predictions = job.get_predictions()
    for source in full_predictions:
        source_name = source["source"]["url"]
        predictions = source["results"]["predictions"]
        for prediction in predictions:
            prosody_predictions = prediction["models"]["prosody"]["grouped_predictions"]
            for prosody_prediction in prosody_predictions:
                for segment in prosody_prediction["predictions"][:1]:
                    print_emotions(segment["emotions"])

    print("Predictions downloaded to predictions.json")


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
    # Example usage:
    bucket_name = "speech-judge"
    source_blob_name = "recording-20240810_171149.wav"
    destination_file_name = "./downloaded_file.wav"

    download_blob(bucket_name, source_blob_name, destination_file_name)
    analyze_emotion(destination_file_name)
    return {"message": "Hi"}
