import requests
import os
from tempfile import NamedTemporaryFile
from google.cloud import storage
import subprocess
from pydub.utils import mediainfo
import langid

LINE_ACCESS_TOKEN = os.getenv('LINE_ACCESS_TOKEN')

def upload_blob(bucket_name, source_file_name, destination_blob_name):
    """Uploads a file to the bucket."""
    try:
        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(destination_blob_name)

        blob.upload_from_filename(source_file_name)
    
        # Construct public url
        public_url = f"https://storage.googleapis.com/{bucket_name}/{destination_blob_name}"
        #print(f"Successfully uploaded file to {public_url}")
        return public_url
    except Exception as e:
        print(f"Failed to upload file: {e}")
        raise
        
def convert_audio_to_m4a(input_path, output_path):
    command = ['ffmpeg', '-i', input_path, '-c:a', 'aac', output_path]
    result = subprocess.run(command, check=True, capture_output=True, text=True)

def text_to_speech(text, bucket_name, destination_blob_name, voicevox_url, style_id):
    #voicevox main
    audio_query_endpoint = f"{voicevox_url}/audio_query"
    audio_synthesis_endpoint = f"{voicevox_url}/synthesis"
    query_params = {
        'text': text,
        'style_id': style_id
    }

    query_response = requests.post(audio_query_endpoint, params=query_params)
    
    if query_response.status_code == 200:
        query_data = query_response.json()
    else:
        print('Error: Failed to get audio query.')
        exit()
        
    synthesis_body = query_data

    synthesis_response = requests.post(synthesis_endpoint, json=synthesis_body, params={'style_id': style_id})
    
    with NamedTemporaryFile(suffix=".wav", delete=False) as temp:
        temp.write(synthesis_response.content)
        temp.flush()

        # Convert the WAV file to M4A
        m4a_path = temp.name.replace(".wav", ".m4a")
        convert_audio_to_m4a(temp.name, m4a_path)
        
        # Get the duration of the local file before uploading
        duration = get_duration(m4a_path)

        # Upload the m4a file
        public_url = upload_blob(bucket_name, m4a_path, destination_blob_name)
        
        # Return the public url, local path of the file, and duration
        return public_url, m4a_path, duration
    
def delete_local_file(file_path):
    """Deletes a local file."""
    if os.path.isfile(file_path):
        os.remove(file_path)
        #print(f"Local file {file_path} deleted.")
    #else:
        #print(f"No local file found at {file_path}.")    

def delete_blob(bucket_name, blob_name):
    """Deletes a blob from the bucket."""
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(blob_name)
    blob.delete()
    #print(f"Blob {blob_name} deleted.")
    
def get_duration(file_path):
    info = mediainfo(file_path)
    #print(f"mediainfo: {info}")
    duration = info.get('duration')  # durationの値がない場合はNoneを返す
    if duration is None:
        print(f"No duration information found for {file_path}.")
        return 0  # または適当なデフォルト値
    else:
        return int(float(duration)) * 1000  # Convert to milliseconds

def set_bucket_lifecycle(bucket_name, age):
    storage_client = storage.Client()
    bucket = storage_client.get_bucket(bucket_name)

    rule = {
        'action': {'type': 'Delete'},
        'condition': {'age': age}  # The number of days after object creation
    }
    
    bucket.lifecycle_rules = [rule]
    bucket.patch()

    #print(f"Lifecycle rule set for bucket {bucket_name}.")
    
def bucket_exists(bucket_name):
    """Check if a bucket exists."""
    storage_client = storage.Client()

    bucket = storage_client.bucket(bucket_name)

    return bucket.exists()



def put_audio_voicevox(userId, message_id, response, BACKET_NAME, FILE_AGE, voicevox_url, style_id):
    if bucket_exists(BACKET_NAME):
        set_bucket_lifecycle(BACKET_NAME, FILE_AGE)
    else:
        print(f"Bucket {BACKET_NAME} does not exist.")
        return 'OK'
    blob_path = f'{userId}/{message_id}.m4a'
    public_url, local_path, duration = text_to_speech(response, BACKET_NAME, blob_path, voicevox_url, style_id)
    return public_url, local_path, duration
      
