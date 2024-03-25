import os
from openai import OpenAI
from datetime import datetime, time, timedelta
import pytz
import requests
from bs4 import BeautifulSoup
from google.cloud import storage
import io
import uuid
import gpt_config as cf
import json
import wikipedia
from PIL import Image
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import base64
import email

google_api_key = os.getenv("GOOGLE_API_KEY")
google_cse_id = os.getenv("GOOGLE_CSE_ID")
google_cse_id1 = os.getenv("GOOGLE_CSE_ID1")

openai_api_key = os.getenv('OPENAI_API_KEY')
gpt_client = OpenAI(api_key=openai_api_key)
    
user_id = []
bucket_name = []
file_age = []

def update_function_descriptions(functions, extra_description, function_name_to_update):
    for func in functions:
        if func["name"] == function_name_to_update:
            func["description"] += extra_description

def downdate_function_descriptions(functions, extra_description, function_name_to_update):
    for func in functions:
        if func["name"] == function_name_to_update:
            func["description"] = ""

def clock():
    jst = pytz.timezone('Asia/Tokyo')
    nowDate = datetime.now(jst) 
    nowDateStr = nowDate.strftime('%Y/%m/%d %H:%M:%S %Z')
    return "SYSTEM:現在時刻は" + nowDateStr + "です。"

def get_googlesearch(words, num=3, start_index=1, search_lang='lang_ja'):
    base_url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "key": google_api_key,
        "cx": google_cse_id,
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

def get_customsearch1(words, num=3, start_index=1, search_lang='lang_ja'):
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

def search_wikipedia(prompt):
    try:
        wikipedia.set_lang("ja")
        search_result = wikipedia.page(prompt)
        summary = search_result.summary
        page_url = search_result.url

        # 結果を1000文字に切り詰める
        if len(summary) > 1000:
            summary = summary[:1000] + "..."

        return f"SYSTEM: 以下は{page_url}の読み込み結果です。情報を提示するときは情報とともに参照元URLアドレスも案内してください。\n{summary}"
    except wikipedia.exceptions.DisambiguationError as e:
        return f"SYSTEM: 曖昧さ解消が必要です。オプション: {e.options}"
    except wikipedia.exceptions.PageError:
        return "SYSTEM: ページが見つかりませんでした。"


def scraping(link):
    contents = ""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.82 Safari/537.36",
    }
    
    try:
        response = requests.get(link, headers=headers, timeout=5)
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
        if len(contents) > 1000:
            contents = contents[:1000] + "..."

    return f"SYSTEM:以下はURL「{link}」の読み込み結果です。情報を提示するときは情報とともにURLも案内してください。\n" + contents

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

def generate_image(paint_prompt, i_prompt, user_id, message_id, bucket_name, file_age):
    filename = str(uuid.uuid4())
    blob_path = f'{user_id}/{message_id}.png'
    preview_blob_path = f'{user_id}/{message_id}_s.png'
    client = OpenAI()
    prompt = paint_prompt + "\n" + i_prompt
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
            return "SYSTEM:バケットが存在しません。", public_img_url, public_img_url_s

        # PNG画像をダウンロード
        png_image = download_image(image_result)
        preview_image = create_preview_image(png_image)
        
        png_image.seek(0)  # ストリームをリセット
        preview_image.seek(0)  # ストリームをリセット

        # 画像をアップロード
        public_img_url = upload_blob(bucket_name, png_image, blob_path)
        public_img_url_s = upload_blob(bucket_name, preview_image, preview_blob_path)

        
        return f"SYSTEM:{i_prompt}のキーワードで画像を生成し、表示しました。画像が生成された旨を伝えてください。", public_img_url, public_img_url_s
    except Exception as e:
        print(f"generate_image error: {e}" )
        return f"SYSTEM: 画像生成にエラーが発生しました。{e}", public_img_url, public_img_url_s

def get_calender(gaccount_access_token, max_chars=1000):
    try:
        # アクセストークンからCredentialsオブジェクトを作成
        credentials = Credentials(token=gaccount_access_token)
    
        # Google Calendar APIのserviceオブジェクトを構築
        service = build('calendar', 'v3', credentials=credentials)

        # 現在時刻
        jst = pytz.timezone('Asia/Tokyo')
        now = datetime.now(jst).isoformat()
    
        # Google Calendar APIを呼び出して、直近の10件のイベントを取得
        events_result = service.events().list(calendarId='primary', timeMin=now,
                                          maxResults=10, singleEvents=True,
                                          orderBy='startTime').execute()
        events = events_result.get('items', [])
    
        if not events:
            return "直近のイベントはありません。"

        # イベントの詳細を結合して最大1000文字までの文字列を生成
        events_str = ""
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            event_str = f"{start} - {event['summary']}\n"
            if len(events_str) + len(event_str) > max_chars:
                break  # 最大文字数を超えたらループを抜ける
            events_str += event_str

        return "SYSTEM:カレンダーのイベントを取得しました。イベント内容を要約してください。" + events_str[:max_chars]
        
    except Exception as e:
        print(f"generate_image error: {e}" )
        return f"SYSTEM: SYSTEM:カレンダーのイベント取得にエラーが発生しました。{e}"

def add_calendar(gaccount_access_token, summary, start_time, end_time, description=None, location=None):
    try:
        # アクセストークンからCredentialsオブジェクトを作成
        credentials = Credentials(token=gaccount_access_token)
    
        # Google Calendar APIのserviceオブジェクトを構築
        service = build('calendar', 'v3', credentials=credentials)
    
        # イベントの情報を設定
        event = {
            'summary': summary,
            'location': location,
            'description': description,
            'start': {
                'dateTime': start_time,
                'timeZone': 'Asia/Tokyo',
            },
            'end': {
                'dateTime': end_time,
                'timeZone': 'Asia/Tokyo',
            },
            'reminders': {
                'useDefault': False,
                'overrides': [
                    {'method': 'email', 'minutes': 24 * 60},
                    {'method': 'popup', 'minutes': 10},
                ],
            },
        }
    
        # イベントをカレンダーに追加
        event_result = service.events().insert(calendarId='primary', body=event).execute()
    
        # 成功した場合、イベントの詳細を含むメッセージを返す
        return f"次のイベントが追加されました: summary={summary}, start_time={start_time},  end_time={end_time}, description={description}, location={location}"
    
    except Exception as e:
        return f"イベント追加に失敗しました: {e}"

def get_mime_part(parts, mime_type='text/plain'):
    """再帰的に特定のMIMEタイプのパートを探す"""
    for part in parts:
        if part['mimeType'] == mime_type:
            return part
        if 'parts' in part:
            return get_mime_part(part['parts'], mime_type=mime_type)
    return None

def get_gmail(gaccount_access_token, max_chars=1000):
    try:
        credentials = Credentials(token=gaccount_access_token)
        service = build('gmail', 'v1', credentials=credentials)

        results = service.users().messages().list(userId='me', maxResults=5).execute()
        messages = results.get('messages', [])

        if not messages:
            return "直近のメッセージはありません。"

        messages_str = ""
        for msg in messages:
            msg_detail = service.users().messages().get(userId='me', id=msg['id'], format='full').execute()
            payload = msg_detail.get('payload', {})
            headers = payload.get('headers', [])
            subject = next((i['value'] for i in headers if i['name'].lower() == 'subject'), "No Subject")

            # メッセージ本文の処理
            parts = payload.get('parts', [])
            text_part = get_mime_part(parts, mime_type='text/plain') or get_mime_part(parts, mime_type='text/html')
            if text_part:
                msg_body_encoded = text_part['body'].get('data', '')
                msg_body = base64.urlsafe_b64decode(msg_body_encoded).decode('utf-8')
                if text_part['mimeType'] == 'text/html':
                    soup = BeautifulSoup(msg_body, 'html.parser')
                    msg_body = soup.get_text()
            else:
                msg_body = "本文が見つかりません。"

            message_str = f"Subject: {subject}\n{msg_body}\n\n"
            if len(messages_str) + len(message_str) > max_chars:
                break
            messages_str += message_str

        return "SYSTEM: メールの一覧を受信しました。\n" + messages_str[:max_chars]
    except Exception as e:
        return f"SYSTEM: メール取得にエラーが発生しました。{e}"

def run_conversation(GPT_MODEL, messages):
    try:
        response = gpt_client.chat.completions.create(
            model=GPT_MODEL,
            messages=messages,
        )
        return response  # レスポンス全体を返す
    except Exception as e:
        print(f"An error occurred: {e}")
        return None  # エラー時には None を返す

def run_conversation_f(GPT_MODEL, messages, google_description, custom_description, attempt):
    update_function_descriptions(cf.functions, google_description, "get_googlesearch")
    update_function_descriptions(cf.functions, custom_description, "get_customsearch1")

    try:
        response = gpt_client.chat.completions.create(
            model=GPT_MODEL,
            messages=messages,
            functions=cf.functions,
            function_call="auto",
        )
        downdate_function_descriptions(cf.functions, google_description, "get_googlesearch")
        downdate_function_descriptions(cf.functions, custom_description, "get_customsearch1")
        return response  # レスポンス全体を返す
    except Exception as e:
        downdate_function_descriptions(cf.functions, google_description, "get_googlesearch")
        downdate_function_descriptions(cf.functions, custom_description, "get_customsearch1")
        print(f"An error occurred: {e}")
        return None  # エラー時には None を返す

def chatgpt_functions(GPT_MODEL, messages_for_api, USER_ID, message_id, ERROR_MESSAGE, PAINT_PROMPT, BUCKET_NAME, FILE_AGE, GOOGLE_DESCRIPTION, CUSTOM_DESCRIPTION, gaccount_access_token, max_attempts=5):
    public_img_url = None
    public_img_url_s = None
    user_id = USER_ID
    bucket_name = BUCKET_NAME
    file_age = FILE_AGE
    paint_prompt = PAINT_PROMPT
    google_description = GOOGLE_DESCRIPTION
    custom_description = CUSTOM_DESCRIPTION
    attempt = 0
    i_messages_for_api = messages_for_api.copy()

    clock_called = False
    generate_image_called = False
    search_wikipedia_called = False
    scraping_called = False
    get_googlesearch_called = False
    get_customsearch1_called = False
    get_calender_called = False
    add_calender_called = False
    get_gmail_called = False

    while attempt < max_attempts:
        response = run_conversation_f(GPT_MODEL, i_messages_for_api, google_description, custom_description, attempt)
        if response:
            function_call = response.choices[0].message.function_call
            if function_call:
                if function_call.name == "clock" and not clock_called:
                    clock_called = True
                    bot_reply = clock()
                    i_messages_for_api.append({"role": "assistant", "content": bot_reply})
                    attempt += 1
                elif function_call.name == "generate_image" and not generate_image_called:
                    generate_image_called = True
                    arguments = json.loads(function_call.arguments)
                    bot_reply, public_img_url, public_img_url_s = generate_image(paint_prompt, arguments["prompt"], user_id, message_id, bucket_name, file_age)
                    i_messages_for_api.append({"role": "assistant", "content": bot_reply})
                    attempt += 1
                elif function_call.name == "search_wikipedia" and not search_wikipedia_called:
                    search_wikipedia_called = True
                    arguments = json.loads(function_call.arguments)
                    bot_reply = search_wikipedia(arguments["prompt"])
                    i_messages_for_api.append({"role": "assistant", "content": bot_reply})
                    attempt += 1
                elif function_call.name == "scraping" and not scraping_called:
                    scraping_called = True
                    arguments = json.loads(function_call.arguments)
                    bot_reply = scraping(arguments["link"])
                    i_messages_for_api.append({"role": "assistant", "content": bot_reply})
                    attempt += 1
                elif function_call.name == "get_googlesearch" and not get_googlesearch_called:
                    get_googlesearch_called = True
                    arguments = json.loads(function_call.arguments)
                    bot_reply = get_googlesearch(arguments["words"])
                    i_messages_for_api.append({"role": "assistant", "content": bot_reply})
                    attempt += 1
                elif function_call.name == "get_customsearch1" and not get_customsearch1_called:
                    get_customsearch1_called = True
                    arguments = json.loads(function_call.arguments)
                    bot_reply = get_customsearch1(arguments["words"])
                    i_messages_for_api.append({"role": "assistant", "content": bot_reply})
                    attempt += 1
                elif function_call.name == "get_calender" and not get_calender_called:
                    get_calender_called = True
                    arguments = json.loads(function_call.arguments)
                    bot_reply = get_calender(gaccount_access_token)
                    i_messages_for_api.append({"role": "assistant", "content": bot_reply})
                    attempt += 1
                elif function_call.name == "add_calender" and not add_calender_called:
                    add_calender_called = True
                    arguments = json.loads(function_call.arguments)
                    bot_reply = add_calender(gaccount_access_token, arguments["summary"], arguments["start_time"], arguments["end_time"], arguments["description"], arguments["location"])
                    i_messages_for_api.append({"role": "assistant", "content": bot_reply})
                    attempt += 1
                elif function_call.name == "get_gmail" and not get_gmail_called:
                    get_gmail_called = True
                    arguments = json.loads(function_call.arguments)
                    bot_reply = get_gmail(gaccount_access_token)
                    i_messages_for_api.append({"role": "assistant", "content": bot_reply})
                    attempt += 1
                else:
                    response = run_conversation(GPT_MODEL, i_messages_for_api)
                    if response:
                        bot_reply = response.choices[0].message.content
                    else:
                        bot_reply = "An error occurred while processing the question"
                    return bot_reply, public_img_url, public_img_url_s
            else:
                return response.choices[0].message.content, public_img_url, public_img_url_s
        else:
            return ERROR_MESSAGE + " Fail to connect OpenAI."
    
    return bot_reply, public_img_url, public_img_url_s
