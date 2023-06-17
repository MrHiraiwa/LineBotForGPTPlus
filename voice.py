import os
from tempfile import NamedTemporaryFile
from google.cloud import texttospeech, storage
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
    #print("stdout:", result.stdout)
    #print("stderr:", result.stderr)

def text_to_speech(text, bucket_name, destination_blob_name, or_chinese, or_english, voice_speed, gender):
    client = texttospeech.TextToSpeechClient()
    synthesis_input = texttospeech.SynthesisInput(text=text)
    
    detected_lang, dialect = detect_language(text)
    name = ''
    pitch = 0

    # Set the gender based on the input parameter
    if gender.lower() == 'male':
        ssml_gender = texttospeech.SsmlVoiceGender.MALE
    else:
        ssml_gender = texttospeech.SsmlVoiceGender.FEMALE  # Default to female

    if detected_lang == 'ja':
        language_code = "ja-JP"
        if gender.lower() == 'male':
            name = "ja-JP-Neural2-C"
        else:
            name = "ja-JP-Neural2-B"    
    elif detected_lang == 'en' and or_english == 'AMERICAN':
        language_code = "en-US"
        if gender.lower() == 'male':
            name = "en-US-Neural2-A"
        else:
            name = "en-US-Neural2-C"
    elif detected_lang == 'en' and or_english == 'AUSTRALIAN':
        language_code = "en-AU"
        if gender.lower() == 'male':
            name = "en-AU-Neural2-B"
        else:
            name = "en-AU-Neural2-A"
    elif detected_lang == 'en' and or_english == 'INDIAN':
        language_code = "en-IN"
        if gender.lower() == 'male':
            name = "en-IN-Standard-B"
        else:
            name = "en-IN-Standard-A"
    elif detected_lang == 'en' and or_english == 'BRIDISH':
        language_code = "en-GB"
        if gender.lower() == 'male':
            name = "en-GB-Neural2-B"
        else:
            name = "en-GB-Neural2-A"
    elif detected_lang == 'zh' and or_chinese == 'MANDARIN':
        language_code = "cmn-CN"
        if gender.lower() == 'male':
            name = "cmn-CN-Standard-B"
        else:
            name = "cmn-CN-Standard-A"
    elif detected_lang == 'zh' and or_chinese == 'CANTONESE':
        language_code = "yue-HK"
        if gender.lower() == 'male':
            name = "yue-HK-Standard-B"
        else:
            name = "yue-HK-Standard-A"
    elif detected_lang == 'ko':
        language_code = "ko-KR"
        if gender.lower() == 'male':
            name = "ko-KR-Neural2-C"
        else:
            name = "ko-KR-Neural2-A"
    elif detected_lang == 'id':
        language_code = "id-ID"
        if gender.lower() == 'male':
            name = "id-ID-Standard-B"
        else:
            name = "id-ID-Standard-A"
    elif detected_lang == 'th':
        language_code = "th-TH"
        if gender.lower() == 'male':
            pitch = -15
        else:
            name = "th-TH-Standard-A"
    else:
        language_code = "ja-JP"  # Default to Japanese if language detection fails
        if gender.lower() == 'male':
            name = "ja-JP-Neural2-C"
        else:
            name = "ja-JP-Neural2-B"   

    if voice_speed == 'slow':
        speaking_rate = 0.75
    elif voice_speed == 'fast':
        speaking_rate = 1.5
    else:
        speaking_rate = 1.0
        
    voice = texttospeech.VoiceSelectionParams(
        language_code=language_code,
        ssml_gender=ssml_gender,
        name=name
    )
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3,
        speaking_rate=speaking_rate,
        pitch=pitch
    )

    response = client.synthesize_speech(
        input=synthesis_input, voice=voice, audio_config=audio_config
    )

    # Save the audio file temporarily
    with NamedTemporaryFile(suffix=".mp3", delete=False) as temp:
        temp.write(response.audio_content)
        temp.flush()

        # Convert the MP3 file to M4A
        m4a_path = temp.name.replace(".mp3", ".m4a")
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

def detect_language(text):
    try:
        lang, dialect = langid.classify(text)
        return lang, dialect
    except:
        return None, None
    

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



def put_audio(userId, message_id, response, BACKET_NAME, FILE_AGE, or_chinese='MANDARIN', or_english='AMERICAN', voice_speed='normal', gender='female'):
    if bucket_exists(BACKET_NAME):
        set_bucket_lifecycle(BACKET_NAME, FILE_AGE)
    else:
        print(f"Bucket {BACKET_NAME} does not exist.")
        return 'OK'
    blob_path = f'{userId}/{message_id}.m4a'
    public_url, local_path, duration = text_to_speech(response, BACKET_NAME, blob_path, or_chinese, or_english, voice_speed, gender)
    return public_url, local_path, duration
