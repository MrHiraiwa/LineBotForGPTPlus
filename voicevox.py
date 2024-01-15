import requests
import os
from tempfile import NamedTemporaryFile
from google.cloud import storage
import subprocess
from pydub.utils import mediainfo
import langid
import urllib.parse

LINE_ACCESS_TOKEN = os.getenv('LINE_ACCESS_TOKEN')
VOICEVOX_API_KEY = os.getenv('VOICEVOX_API_KEY')

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

def text_to_speech(text, bucket_name, destination_blob_name, speaker_id="0f56c2f2-644c-49c9-8989-94e11f7129d0"):
    print(f"1c")
    #voicevox main
    text = urllib.parse.quote(text)
    voicevox_api_url = f"https://deprecatedapis.tts.quest/v2/voicevox/audio/?key={VOICEVOX_API_KEY}&speaker={speaker_id}&pitch=0&intonationScale=1&speed=1&text={text}"
    print(f"2c,{voicevox_api_url}")
    # テキストから音声合成のためのクエリを取得
    response = requests.post(voicevox_api_url)
    print("3c")
    if response.status_code != 200:
        raise Exception("Failed to get audio query from VOICEVOX")
    
    # Save the audio file temporarily
    print("4c")
    with NamedTemporaryFile(suffix=".wav", delete=False) as temp:
        print("5c")
        temp.write(response.audio_content)
        temp.flush()
        print("6c")

        # Convert the WAV file to M4A
        m4a_path = temp.name.replace(".wav", ".m4a")
        convert_audio_to_m4a(temp.name, m4a_path)
        print("7c")
        
        # Get the duration of the local file before uploading
        duration = get_duration(m4a_path)
        print("8c")

        # Upload the m4a file
        public_url = upload_blob(bucket_name, m4a_path, destination_blob_name)
        print(f"9c,{public_url},{m4a_path},{duration}")
        
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



def put_audio_voicevox(userId, message_id, response, BACKET_NAME, FILE_AGE, speaker_id):
    if bucket_exists(BACKET_NAME):
        set_bucket_lifecycle(BACKET_NAME, FILE_AGE)
    else:
        print(f"Bucket {BACKET_NAME} does not exist.")
        return 'OK'
    blob_path = f'{userId}/{message_id}.m4a'
    print(f"1a,{userId}, {message_id}, {response}, {BACKET_NAME}, {FILE_AGE}, {speaker_id}")
    public_url, local_path, duration = text_to_speech(response, BACKET_NAME, blob_path, speaker_id)
    print("1b,{public_url},{local_path},{duration}")
    return public_url, local_path, duration
      
