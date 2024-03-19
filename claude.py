import os
from anthropic import Anthropic
from datetime import datetime, time, timedelta
import pytz
import requests
from bs4 import BeautifulSoup
from google.cloud import storage
import io
import uuid
import json
import wikipedia
from PIL import Image
from openai import OpenAI

from anthropic_tools.base_tool import BaseTool
from anthropic_tools.tool_user import ToolUser

google_api_key = os.getenv("GOOGLE_API_KEY")
google_cse_id = os.getenv("GOOGLE_CSE_ID")
google_cse_id1 = os.getenv("GOOGLE_CSE_ID1")

anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
openai_api_key = os.getenv('OPENAI_API_KEY')

claude_client = Anthropic(
    # This is the default and can be omitted
    api_key=anthropic_api_key,
)

global public_img_url, public_img_url_s
global i_prompt, user_id, message_id, bucket_name, file_age
i_prompt = []
user_id = []
message_id = []
bucket_name = []
file_age = []

public_img_url = ""
public_img_url_s = ""


class Clock(BaseTool):
    def use_tool(self):
        jst = pytz.timezone('Asia/Tokyo')
        nowDate = datetime.now(jst) 
        nowDateStr = nowDate.strftime('%Y/%m/%d %H:%M:%S %Z')
        return "SYSTEM:現在時刻は" + nowDateStr + "です。"

class Googlesearch(BaseTool):
    def use_tool(self, words):
        num = 3
        start_index = 1
        search_lang = 'lang_ja'

        base_url = "https://www.googleapis.com/customsearch/v1"
        params = {
            "key": google_api_key,
            "cx": google_cse_id,
            "q": words,  # 結合された検索クエリ
            "num": num,
            "start": start_index,
            "lr": search_lang
        }

        response = requests.get(base_url, params=params)
        response.raise_for_status()

        search_results = response.json()

        # 検索結果を文字列に整形
        formatted_results = ""
        for item in search_results.get("items", []):
            title = item.get("title")
            link = item.get("link")
            snippet = item.get("snippet")
            formatted_results += f"タイトル: {title}\nリンク: {link}\n概要: {snippet}\n\n"

        return f"SYSTEM:Webページを検索しました。{words}と関係のありそうなURLを読み込んでください。\n" + formatted_results

class Customsearch1(BaseTool):
    def use_tool(self, words):
        num = 3
        start_index = 1
        search_lang = 'lang_ja'
        base_url = "https://www.googleapis.com/customsearch/v1"
        params = {
            "key": google_api_key,
            "cx": google_cse_id1,
            "q": words,
            "num": num,
            "start": start_index,
            "lr": search_lang
        }

        response = requests.get(base_url, params=params)
        response.raise_for_status()

        search_results = response.json()

        # 検索結果を文字列に整形
        formatted_results = ""
        for item in search_results.get("items", []):
            title = item.get("title")
            link = item.get("link")
            snippet = item.get("snippet")
            formatted_results += f"タイトル: {title}\nリンク: {link}\n概要: {snippet}\n\n"

        return f"SYSTEM:Webページを検索しました。{words}と関係のありそうなURLを読み込んでください。\n" + formatted_results

class Wikipediasearch(BaseTool):
    def use_tool(self, words):
        try:
            wikipedia.set_lang("ja")
            search_result = wikipedia.page(words)
            summary = search_result.summary
            page_url = search_result.url

            # 結果を1000文字に切り詰める
            if len(summary) > 2000:
                summary = summary[:2000] + "..."

            return f"SYSTEM: 以下は{page_url}の読み込み結果です。情報を提示するときは情報とともに参照元URLアドレスも案内してください。\n{summary}"
        except wikipedia.exceptions.DisambiguationError as e:
            return f"SYSTEM: 曖昧さ解消が必要です。オプション: {e.options}"
        except wikipedia.exceptions.PageError:
            return "SYSTEM: ページが見つかりませんでした。"

class Scraping(BaseTool):
    def use_tool(self, URL):
        contents = ""
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.82 Safari/537.36",
        }
    
        try:
            response = requests.get(URL, headers=headers, timeout=5)
            response.raise_for_status()
            response.encoding = response.apparent_encoding  # または特定のエンコーディングを指定
            html = response.text
        except requests.RequestException as e:
            return f"SYSTEM: リンクの読み込み中にエラーが発生しました: {e}"

        soup = BeautifulSoup(html, features="html.parser")

        # Remove all 'a' tags
        for a in soup.findAll('a'):
            a.decompose()

        content = soup.select_one("article, .post, .content")

        if content is None or content.text.strip() == "":
            content = soup.select_one("body")

        if content is not None:
            contents = ' '.join(content.text.split()).replace("。 ", "。\n").replace("! ", "!\n").replace("? ", "?\n").strip()

            # 結果を1000文字に切り詰める
            if len(contents) > 2000:
                contents = contents[:2000] + "..."

        return f"SYSTEM:以下はURL「{URL}」の読み込み結果です。情報を提示するときは情報とともにURLも案内してください。\n" + contents

def set_bucket_lifecycle(bucket_name, age):
    storage_client = storage.Client()
    bucket = storage_client.get_bucket(bucket_name)

    rule = {
        'action': {'type': 'Delete'},
        'condition': {'age': age}  # The number of days after object creation
    }
    
    bucket.lifecycle_rules = [rule]
    bucket.patch()
    return

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
class Generateimage(BaseTool):
    def use_tool(self, sentence):
        filename = str(uuid.uuid4())
        blob_path = f'{user_id}/{message_id}.png'
        preview_blob_path = f'{user_id}/{message_id}_s.png'
        client = OpenAI(api_key=openai_api_key)
        prompt = sentence + "\n" + i_prompt
        public_img_url = ""
        public_img_url_s = ""
    
        try:
            response = client.images.generate(
                model="dall-e-3",
                prompt=prompt,
                size="1024x1024",
                quality="standard",
                n=1,
            )
            image_result = response.data[0].url
            if bucket_exists(bucket_name):
                set_bucket_lifecycle(bucket_name, file_age)
            else:
                print(f"Bucket {bucket_name} does not exist.")
                return "SYSTEM:バケットが存在しません。"

            # PNG画像をダウンロード
            png_image = download_image(image_result)
            preview_image = create_preview_image(png_image)
        
            png_image.seek(0)  # ストリームをリセット
            preview_image.seek(0)  # ストリームをリセット

            # 画像をアップロード
            public_img_url = upload_blob(bucket_name, png_image, blob_path)
            public_img_url_s = upload_blob(bucket_name, preview_image, preview_blob_path)

        
            return f"SYSTEM:{i_prompt}のキーワードで画像を生成し、表示しました。画像が生成された旨を伝えてください。"
        except Exception as e:
            print(f"generate_image error: {e}" )
            return f"SYSTEM: 画像生成にエラーが発生しました。{e}"

clock_tool_name = "perform_clock"
clock_tool_description = "useful for when you need to know what time it is."
clock_tool_parameters = [
]

googlesearch_tool_name = "perform_googlesearch"
googlesearch_tool_description = "useful for when you need to answer questions about current events."
googlesearch_tool_parameters = [
    {"name": "words", "type": "str", "description": "a search key word"}
]

customsearch1_tool_name = "perform_customsearch1"
customsearch1_tool_description = "unable use."
customsearch1_tool_parameters = [
    {"name": "words", "type": "str", "description": "a search key word"}
]

wikipediasearch_tool_name = "perform_wikipediasearch"
wikipediasearch_tool_description = "useful for when you need to Read dictionary page by specifying the word."
wikipediasearch_tool_parameters = [
    {"name": "words", "type": "str", "description": "a search key word"}
]

scraping_tool_name = "perform_scraping"
scraping_tool_description = "useful for when you need to read a web page by specifying the URL."
scraping_tool_parameters = [
    {"name": "URL", "type": "str", "description": "a URL for scraping"}
]

generateimage_tool_name = "perform_generateimage"
generateimage_tool_description = "If you specify a long sentence, you can generate an image that matches the sentence."
generateimage_tool_parameters = [
    {"name": "sentence", "type": "str", "description": "a text for image generation"}
]

clock_tool = Clock(clock_tool_name, clock_tool_description, clock_tool_parameters)
googlesearch_tool = Googlesearch(googlesearch_tool_name, googlesearch_tool_description, googlesearch_tool_parameters)
customsearch1_tool = Customsearch1(customsearch1_tool_name, customsearch1_tool_description, customsearch1_tool_parameters)
wikipediasearch_tool = Wikipediasearch(wikipediasearch_tool_name, wikipediasearch_tool_description, wikipediasearch_tool_parameters)
scraping_tool = Scraping(scraping_tool_name, scraping_tool_description, scraping_tool_parameters)
generateimage_tool = Generateimage(generateimage_tool_name, generateimage_tool_description, generateimage_tool_parameters)

def run_conversation(CLAUDE_MODEL, SYSTEM_PROMPT, messages):
    try:
        response = claude_client.messages.create(
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            messages=messages,
            model="claude-3-opus-20240229",
        )
        return response  # レスポンス全体を返す
    except Exception as e:
        print(f"An error occurred: {e}")
        return None  # エラー時には None を返す

def run_conversation_f(CLAUDE_MODEL, SYSTEM_PROMPT, messages):

    try:
        all_tool_user = ToolUser([googlesearch_tool, customsearch1_tool, wikipediasearch_tool, scraping_tool, generateimage_tool], SYSTEM_PROMPT)
        response = all_tool_user.use_tools(messages, execution_mode='automatic')
        print(f"response: {response}")
        return response  # レスポンス全体を返す
    except Exception as e:
        print(f"An error occurred: {e}")
        return None  # エラー時には None を返す

def claude_functions(CLAUDE_MODEL, SYSTEM_PROMPT ,messages_for_api, USER_ID, MESSAGE_ID, ERROR_MESSAGE, PAINT_PROMPT, BUCKET_NAME, FILE_AGE, GOOGLE_DESCRIPTION, CUSTOM_DESCRIPTION, max_attempts=5):
    public_img_url = None
    public_img_url_s = None
    i_prompt = PAINT_PROMPT
    user_id = USER_ID
    message_id = MESSAGE_ID
    bucket_name = BUCKET_NAME
    file_age = FILE_AGE
    i_messages_for_api = messages_for_api.copy()
    last_messages_for_api = i_messages_for_api[-1]
    print(f"last_messages_for_api: {last_messages_for_api}")
    response = run_conversation_f(CLAUDE_MODEL, SYSTEM_PROMPT, i_messages_for_api)
    print(f"response: {response}")
    bot_reply = response
    #i_messages_for_api.append({'role': 'assistant', 'content': bot_reply})
    #i_messages_for_api.append({'role': 'user', 'content': 'SYSTEM:以上の結果を元に回答してください。'})
    #response = run_conversation(CLAUDE_MODEL, SYSTEM_PROMPT, i_messages_for_api)
    #print(f"response: {response}")
    bot_reply = response.content[0].text

    return bot_reply, public_img_url, public_img_url_s
