import os
import openai
from google.cloud import storage
import json

openai_api_key = os.getenv('OPENAI_API_KEY')
openai = OpenAI(api_key=openai_api_key)


# Google Cloud Storage クライアントを初期化
storage_client = storage.Client()
bucket_name = 'your-bucket-name'  # バケット名を設定

def download_text_from_storage(bucket_name, source_blob_name):
    """Download a text file from the bucket."""
    try:
        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(source_blob_name)
        return blob.download_as_text()
    except Exception as e:
        print(f"Failed to download file: {e}")
        raise

def create_embedding(input_text):
    response = openai.Embedding.create(
        model='text-embedding-ada-002',
        input=input_text
    )
    vec = response['data'][0]['embedding']
    return vec

def upload_blob(bucket_name, source_stream, destination_blob_name, content_type='text'):
    """Uploads a file to the bucket from a byte stream."""
    try:
        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(destination_blob_name)

        blob.upload_from_string(source_stream, content_type=content_type)
    
        public_url = f"https://storage.googleapis.com/{bucket_name}/{destination_blob_name}"
        return public_url
    except Exception as e:
        print(f"Failed to upload file: {e}")
        raise

def embedding_from_storage(bucket_name):
    source_blob_name = 'embedding_input.txt'
    destination_blob_name = 'embedding_data.json'
    
    # Cloud Storageからテキストデータをダウンロード
    input_text = download_text_from_storage(bucket_name, source_blob_name)

    # ベクトルデータを生成
    embedding_vector = create_embedding(input_text)

    # ベクトルデータをJSON形式に変換
    embedding_json = json.dumps(embedding_vector)

    # Cloud Storageにアップロードして、公開URLを取得
    public_url = upload_blob(bucket_name, embedding_json, destination_blob_name)
    return public_url
