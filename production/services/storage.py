# services/storage.py
import os
import json
from google.cloud import storage
from google.oauth2 import service_account

def initialize_storage():
    credentials_json = os.environ["GOOGLE_APPLICATION_CREDENTIALS"]
    credentials_info = json.loads(credentials_json)
    credentials = service_account.Credentials.from_service_account_info(credentials_info)
    return storage.Client(credentials=credentials)

async def download_file(file_path: str) -> str:
    client = initialize_storage()
    bucket_name, blob_name = file_path.split('/', 1)
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(blob_name)
    
    local_path = f"/tmp/{blob_name.split('/')[-1]}"
    await blob.download_to_filename(local_path)
    return local_path