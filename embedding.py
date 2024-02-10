import os
import openai
from google.cloud import storage

openai_api_key = os.getenv('OPENAI_API_KEY')
openai = OpenAI(api_key=openai_api_key)

# Google Cloud Storage クライアントを初期化
storage_client = storage.Client()
bucket_name = 'your-bucket-name'  # バケット名を設定
bucket = storage_client.bucket(bucket_name)

def create_embedding(input_text):
    response = openai.Embedding.create(
        model='text-embedding-ada-002',
        input=input_text
    )
    vec = response['data'][0]['embedding']
    return vec

def upload_to_storage(bucket, file_name, data):
    blob = bucket.blob(file_name)
    blob.upload_from_string(data)
