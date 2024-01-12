from langchain.agents import initialize_agent, Tool
from langchain.agents import AgentType
from langchain.chat_models import ChatOpenAI
from langchain.utilities.google_search import GoogleSearchAPIWrapper
from langchain.tools import WikipediaQueryRun
from langchain.utilities import WikipediaAPIWrapper
import openai
from datetime import datetime, time, timedelta
import pytz
import requests
from bs4 import BeautifulSoup
from google.cloud import storage
from PIL import Image
import io

public_url = []
public_url_original = []
public_url_preview = []
    
user_id = []
message_id = []
bucket_name = []
file_age = []

llm = ChatOpenAI(model="gpt-3.5-turbo")

google_search = GoogleSearchAPIWrapper()
wikipedia = WikipediaQueryRun(api_wrapper=WikipediaAPIWrapper(lang='ja', doc_content_chars_max=1000, load_all_available_meta=True))

def google_search_results(query):
    return google_search.results(query, 5)

def clock(dummy):
    jst = pytz.timezone('Asia/Tokyo')
    nowDate = datetime.now(jst) 
    nowDateStr = nowDate.strftime('%Y/%m/%d %H:%M:%S %Z')
    return nowDateStr

def scraping(links):
    contents = []
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.82 Safari/537.36" ,
    }
    
    for link in links:
        try:
            response = requests.get(link, headers=headers, timeout=5)  # Use headers
            response.raise_for_status()
            response.encoding = response.apparent_encoding
            html = response.text
        except requests.RequestException:
            html = "<html></html>"
            
        soup = BeautifulSoup(html, "html.parser")

        # Remove all 'a' tags
        for a in soup.findAll('a'):
            a.decompose()

        content = soup.select_one("article, .post, .content")

        if content is None or content.text.strip() == "":
            content = soup.select_one("body")

        if content is not None:
            text = ' '.join(content.text.split()).replace("。 ", "。\n").replace("! ", "!\n").replace("? ", "?\n").strip()
            contents.append(text)

    return contents

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

def download_image(image_url):
    """ PNG画像をダウンロードする """
    response = requests.get(image_url)
    return io.BytesIO(response.content)

def create_preview_image(original_image_stream):
    """ 画像のサイズを縮小してプレビュー用画像を生成する """
    image = Image.open(original_image_stream)
    image.thumbnail((640, 640))  # 画像の最大サイズを1024x1024に制限
    preview_image = io.BytesIO()
    image.save(preview_image, format='PNG')
    preview_image.seek(0)
    return preview_image

def upload_blob(bucket_name, source_stream, destination_blob_name, content_type='image/png'):
    """Uploads a file to the bucket from a byte stream."""
    try:
        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(destination_blob_name)

        blob.upload_from_file(source_stream, content_type=content_type)
    
        public_url = f"https://storage.googleapis.com/{bucket_name}/{destination_blob_name}"
        return public_url
    except Exception as e:
        print(f"Failed to upload file: {e}")
        raise

def generate_image(prompt):
    global public_url_original
    global public_url_preview
    
    blob_path = f'{user_id}/{message_id}.png'
    preview_blob_path = f'{user_id}/{message_id}_s.png'
    response = openai.Image.create(
    prompt=prompt,
    n=1,
    size="1024x1024",
    response_format="url"
    )
    image_result = response['data'][0]['url']

    if bucket_exists(bucket_name):
        set_bucket_lifecycle(bucket_name, file_age)
    else:
        print(f"Bucket {bucket_name} does not exist.")
        return 'OK'

    # PNG画像をダウンロード
    png_image = download_image(image_result)

    # プレビュー画像を生成
    preview_image = create_preview_image(png_image)
    png_image.seek(0)  # ストリームをリセット

    # 元のPNG画像をアップロード
    public_url_original = upload_blob(bucket_name, png_image, blob_path)

    # プレビュー用のPNG画像をアップロード
    public_url_preview = upload_blob(bucket_name, preview_image, preview_blob_path)

    return 'generated the image.'

tools = [
    Tool(
        name = "Search",
        func=google_search_results,
        description="useful for when you need to answer questions about current events. it is single-input tool Search."
    ),
    Tool(
        name = "Clock",
        func=clock,
        description="useful for when you need to know what time it is. it is single-input tool."
    ),
    Tool(
        name = "Scraping",
        func=scraping,
        description="useful for when you need to read a web page by specifying the URL. it is single-input tool."
    ),
    Tool(
        name = "Wikipedia",
        func=wikipedia,
        description="useful for when you need to Read dictionary page by specifying the word. it is single-input tool."
    ),
    Tool(
        name = "Painting",
        func= generate_image,
        description="It is a useful tool that can reply image URL based on the Sentence by specifying the Sentence."
    ),
]
mrkl = initialize_agent(tools, llm, agent=AgentType.OPENAI_FUNCTIONS, verbose=True)

def langchain_agent(question, USER_ID, MESSAGE_ID, BUCKET_NAME=None, FILE_AGE=None):
    global user_id
    global message_id
    global bucket_name
    global file_age
    user_id = USER_ID
    message_id = MESSAGE_ID
    bucket_name = BUCKET_NAME
    file_age = FILE_AGE
    
    try:
        result = mrkl.run(question)
        return result, public_url_original, public_url_preview
    except Exception as e:
        print(f"An error occurred: {e}")
        # 何らかのデフォルト値やエラーメッセージを返す
        return "An error occurred while processing the question"

