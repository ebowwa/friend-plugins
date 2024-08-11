import os
import json

def detect_gcp_credentials(directory='.'):
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.json'):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r') as f:
                        data = json.load(f)
                    
                    # Check for common keys in GCP credentials JSON
                    if all(key in data for key in ['type', 'project_id', 'private_key_id', 'private_key']):
                        print(f"Potential GCP credentials file found: {file_path}")
                except json.JSONDecodeError:
                    pass  # Not a valid JSON file
                except Exception as e:
                    print(f"Error reading {file_path}: {str(e)}")

if __name__ == "__main__":
    detect_gcp_credentials()