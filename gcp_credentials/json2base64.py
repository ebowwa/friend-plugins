import json
import base64
import sys

def convert_credentials_to_base64(file_path):
    try:
        # Read the JSON file
        with open(file_path, 'r') as file:
            credentials = json.load(file)
        
        # Convert the JSON to a string
        credentials_str = json.dumps(credentials)
        
        # Encode the string to base64
        credentials_base64 = base64.b64encode(credentials_str.encode('utf-8')).decode('utf-8')
        
        return credentials_base64
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.")
        return None
    except json.JSONDecodeError:
        print(f"Error: '{file_path}' is not a valid JSON file.")
        return None
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return None

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python script.py <path_to_credentials.json>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    base64_credentials = convert_credentials_to_base64(file_path)
    
    if base64_credentials:
        print("Base64 encoded credentials:")
        print(base64_credentials)