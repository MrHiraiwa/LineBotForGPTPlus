import requests
import json
import os
from io import BytesIO
from tempfile import NamedTemporaryFile


# Environment variables should be used to securely store the API keys
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
CHANNEL_ACCESS_TOKEN = os.getenv('CHANNEL_ACCESS_TOKEN')

def get_audio(message_id):
    url = f'https://api-data.line.me/v2/bot/message/{message_id}/content'

    headers = {
        'Authorization': f'Bearer {CHANNEL_ACCESS_TOKEN}',
    }

    response = requests.get(url, headers=headers, timeout=30)

    if response.status_code == 200:
        # Save the audio file temporarily
        with NamedTemporaryFile(suffix=".m4a", delete=False) as temp:
            temp.write(response.content)
            temp.flush()

        # Call the speech_to_text function with the temporary file
        return speech_to_text(temp.name)
    else:
        print(f"Failed to fetch audio: {response.content}")
        return None

def speech_to_text(file_path):
    with open(file_path, 'rb') as f:
        payload = {
            'model': 'whisper-1',
            'temperature': 0
        }

        headers = {
            'Authorization': f'Bearer {OPENAI_API_KEY}'
        }

        files = {
            'file': (os.path.basename(file_path), f)
        }

        response = requests.post(
            "https://api.openai.com/v1/audio/transcriptions", 
            headers=headers, 
            data=payload, 
            files=files,
            timeout=30
        )

        if response.status_code == 200:
            return response.json().get('text')
        else:
            print(f"Failed to transcribe audio: {response.content}")
            return None
