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
from google.auth.transport.requests import Request
import dateutil.parser as parser
from vertexai.preview.vision_models import ImageGenerationModel

import base64
import email

google_api_key = os.getenv("GOOGLE_API_KEY")
google_cse_id = os.getenv("GOOGLE_CSE_ID")
google_cse_id1 = os.getenv("GOOGLE_CSE_ID1")

openai_api_key = os.getenv('OPENAI_API_KEY')
gpt_client = OpenAI(api_key=openai_api_key)

google_client_id = os.getenv("GOOGLE_CLIENT_ID")
google_client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
    
user_id = []
bucket_name = []
file_age = []

def update_function_descriptions(functions, extra_description, function_name_to_update):
    # 関数リストの深いコピーを作成します。
    # これにより、元のリストは変更されずに保持されます。
    updated_functions = []
    for func in functions:
        # 辞書（またはオブジェクト）のコピーを作成します。
        updated_func = func.copy()
        if updated_func["name"] == function_name_to_update:
            updated_func["description"] += extra_description
        updated_functions.append(updated_func)
    
    # 変更された新しいリストを返します。
    return updated_functions


#def downdate_function_descriptions(functions, extra_description, function_name_to_update):
#    for func in functions:
#        if func["name"] == function_name_to_update:
#            func["description"] = ""

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

def generate_image(CORE_IMAGE_TYPE, VERTEX_IMAGE_MODEL, paint_prompt, i_prompt, user_id, message_id, bucket_name, file_age):
    filename = str(uuid.uuid4())
    blob_path = f'{user_id}/{message_id}.png'
    preview_blob_path = f'{user_id}/{message_id}_s.png'
    client = OpenAI()
    prompt = paint_prompt + "\n" + i_prompt
    public_img_url = ""
    public_img_url_s = ""
    image_result = None
    
    try:
        if CORE_IMAGE_TYPE == "Vertex":
            image_model = ImageGenerationModel.from_pretrained(VERTEX_IMAGE_MODEL)
            response = model.generate_images(
                prompt=prompt,
                number_of_images=1,
                guidance_scale=float("1024"),
                aspect_ratio="1:1",
                language="ja",
                seed=None,
            )
            image_result = response[0]
        else:
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

        
        return f"SYSTEM:{i_prompt}のキーワードで画像を生成し、表示しました。画像が生成された旨をメッセージで伝えてください。", public_img_url, public_img_url_s
    except Exception as e:
        print(f"generate_image error: {e}" )
        return f"SYSTEM: 画像生成にエラーが発生しました。{e}", public_img_url, public_img_url_s

def create_credentials(gaccount_access_token, gaccount_refresh_token):
    return Credentials(
        token=gaccount_access_token,
        refresh_token=gaccount_refresh_token,
        client_id=google_client_id,
        client_secret=google_client_secret,
        token_uri='https://oauth2.googleapis.com/token'
    )

def get_calendar(gaccount_access_token, gaccount_refresh_token, max_chars=1000):
    try:
        credentials = create_credentials(
            gaccount_access_token,
            gaccount_refresh_token
        )

        # トークン更新をチェック
        if credentials.expired:
            credentials.refresh(Request())

        # Google Calendar APIのserviceオブジェクトを構築
        service = build('calendar', 'v3', credentials=credentials)

        # 現在時刻
        jst = pytz.timezone('Asia/Tokyo')
        now = datetime.now(jst).isoformat()
    
        # Google Calendar APIを呼び出して、直近のイベントを取得
        events_result = service.events().list(calendarId='primary', timeMin=now,
                                              maxResults=50, singleEvents=True,
                                              orderBy='startTime').execute()
        events = events_result.get('items', [])
    
        if not events:
            return "直近のイベントはありません。", credentials.token, credentials.refresh_token  # イベントがない場合はアクセストークンとリフレッシュトークンと共にメッセージを返す

        # イベントの詳細を結合して最大1000文字までの文字列を生成
        events_str = ""
        for event in events:
            event_id = event['id']
            start = event['start'].get('dateTime', event['start'].get('date'))
            end = event['end'].get('dateTime', event['end'].get('date'))
            summary = event.get('summary', '無題')
            description = event.get('description', '説明なし')
            location = event.get('location', '場所なし')
            event_str = f"ID: {event_id}, Summary: {summary}, Start: {start}, End: {end}, Description: {description}, Location: {location}\n"
            if len(events_str) + len(event_str) > max_chars:
                break  # 最大文字数を超えたらループを抜ける
            events_str += event_str

        updated_access_token = credentials.token

        return "SYSTEM:カレンダーのイベントを取得しました。イベント内容を要約してください。" + events_str[:max_chars], updated_access_token, credentials.refresh_token
        
    except Exception as e:
        print(f"Error during calendar event retrieval: {e}")
        return f"SYSTEM: カレンダーのイベント取得にエラーが発生しました。{e}", gaccount_access_token, gaccount_refresh_token

def add_calendar(gaccount_access_token, gaccount_refresh_token, summary, start_time, end_time, description=None, location=None):
    try:
        credentials = create_credentials(
            gaccount_access_token,
            gaccount_refresh_token
        )

        # トークン更新をチェック
        if credentials.expired:
            credentials.refresh(Request())
    
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

        updated_access_token = credentials.token
    
        # 成功した場合、イベントの詳細を含むメッセージを返す
        return f"次のイベントが追加されました: summary={summary}, start_time={start_time},  end_time={end_time}, description={description}, location={location}。追加した内容をユーザーに伝えてください。", updated_access_token, credentials.refresh_token
    
    except Exception as e:
        return f"イベント追加に失敗しました: {e}", gaccount_access_token, gaccount_refresh_token

def update_calendar(gaccount_access_token, gaccount_refresh_token, event_id, summary=None, start_time=None, end_time=None, description=None, location=None):
    try:
        credentials = create_credentials(
            gaccount_access_token,
            gaccount_refresh_token
        )

        if credentials.expired:
            credentials.refresh(Request())
    
        service = build('calendar', 'v3', credentials=credentials)

        # 現在のイベント情報を取得
        current_event = service.events().get(calendarId='primary', eventId=event_id).execute()

        # 更新が提供されていない項目は現在の情報をそのまま使用
        updated_event = {
            'summary': summary if summary is not None else current_event.get('summary'),
            'location': location if location is not None else current_event.get('location'),
            'description': description if description is not None else current_event.get('description'),
            'start': {'dateTime': start_time, 'timeZone': 'Asia/Tokyo'} if start_time is not None else current_event.get('start'),
            'end': {'dateTime': end_time, 'timeZone': 'Asia/Tokyo'} if end_time is not None else current_event.get('end'),
        }
        
        # イベントを更新
        updated_event_result = service.events().update(calendarId='primary', eventId=event_id, body=updated_event).execute()

        updated_access_token = credentials.token

        return f"イベントが更新されました: {updated_event_result['summary']}", updated_access_token, credentials.refresh_token
    except Exception as e:
        return f"イベント更新に失敗しました: {e}", gaccount_access_token, gaccount_refresh_token

def delete_calendar(gaccount_access_token, gaccount_refresh_token, event_id):
    try:
        credentials = create_credentials(
            gaccount_access_token,
            gaccount_refresh_token
        )

        if credentials.expired:
            credentials.refresh(Request())
    
        service = build('calendar', 'v3', credentials=credentials)
        
        # 削除するイベントの詳細を取得（特にsummaryを含む）
        event_to_delete = service.events().get(calendarId='primary', eventId=event_id).execute()
        event_summary = event_to_delete.get('summary', '無題のイベント')  # イベントにsummaryがない場合のデフォルト値

        # イベントを削除
        service.events().delete(calendarId='primary', eventId=event_id).execute()

        updated_access_token = credentials.token

        return f"イベント「{event_summary}」が削除された旨をユーザーに伝えてください。", updated_access_token, credentials.refresh_token
    except Exception as e:
        return f"イベント削除に失敗しました: {e}", gaccount_access_token, gaccount_refresh_token



def get_mime_part(parts, mime_type='text/plain'):
    """再帰的に特定のMIMEタイプのパートを探す"""
    for part in parts:
        if part['mimeType'] == mime_type:
            return part
        if 'parts' in part:
            return get_mime_part(part['parts'], mime_type=mime_type)
    return None


def get_gmail_list(gaccount_access_token, gaccount_refresh_token, max_results=20):
    try:
        credentials = create_credentials(
            gaccount_access_token,
            gaccount_refresh_token
        )
        
        if credentials.expired:
            credentials.refresh(Request())
        
        service = build('gmail', 'v1', credentials=credentials)

        # maxResultsを20に設定して20件のメールを取得
        results = service.users().messages().list(userId='me', maxResults=max_results).execute()
        messages = results.get('messages', [])
        
        updated_access_token = credentials.token

        if not messages:
            return "SYSTEM: 直近のメッセージはありません。", updated_access_token, credentials.refresh_token

        messages_details = []
        for msg in messages:
            msg_detail = service.users().messages().get(userId='me', id=msg['id'], format='metadata').execute()
            headers = msg_detail.get('payload', {}).get('headers', [])
            
            # 必要な情報をヘッダーから取得
            subject = next((i['value'] for i in headers if i['name'].lower() == 'subject'), "No Subject")
            from_email = next((i['value'] for i in headers if i['name'].lower() == 'from'), "Unknown Sender")
            date_received = next((i['value'] for i in headers if i['name'].lower() == 'date'), "No Date")
            date_parsed = parser.parse(date_received).strftime('%Y-%m-%d %H:%M:%S')
            
            messages_details.append({
                'id': msg['id'],
                'from': from_email,
                'subject': subject,
                'date_received': date_parsed
            })

        messages_str = "\n".join([f"From: {m['from']}, Subject: {m['subject']}, Date: {m['date_received']}" for m in messages_details])
        
        return f"SYSTEM: メール一覧を受信しました。一覧の内容をユーザーに伝えてください。\n{messages_str}", updated_access_token, credentials.refresh_token
    except Exception as e:
        print(f"e: {e}")
        return f"SYSTEM: メール一覧の取得にエラーが発生しました。{e}", gaccount_access_token, gaccount_refresh_token

def get_gmail_content(gaccount_access_token, gaccount_refresh_token, search_query, max_results=5):
    try:
        credentials = create_credentials(
            gaccount_access_token,
            gaccount_refresh_token
        )
        
        if credentials.expired:
            credentials.refresh(Request())
        
        service = build('gmail', 'v1', credentials=credentials)

        # メールを検索するためのクエリを使用
        results = service.users().messages().list(userId='me', q=search_query, maxResults=max_results).execute()
        messages = results.get('messages', [])
        
        updated_access_token = credentials.token

        emails_content = []
        for msg in messages:
            txt = service.users().messages().get(userId='me', id=msg['id'], format='full').execute()
            payload = txt.get('payload', {})
            headers = payload.get('headers', [])

            subject = next((i['value'] for i in headers if i['name'].lower() == 'subject'), "No Subject")
            from_email = next((i['value'] for i in headers if i['name'].lower() == 'from'), "Unknown Sender")
            date_received = next((i['value'] for i in headers if i['name'].lower() == 'date'), "No Date")

            # メール本文の取得
            body = ""
            if 'parts' in payload:
                for part in payload['parts']:
                    if part['mimeType'] == 'text/plain' or part['mimeType'] == 'text/html':
                        body_data = part['body'].get('data', '')
                        body = base64.urlsafe_b64decode(body_data).decode('utf-8')
                        if len(body) > 500:
                            body = body[:500]  # 本文を500文字にカット
                        break
            else:
                body_data = payload.get('body', {}).get('data', '')
                if body_data:
                    body = base64.urlsafe_b64decode(body_data).decode('utf-8')
                    if len(body) > 500:
                        body = body[:500]  # 本文を500文字にカット

            emails_content.append({
                'subject': subject,
                'from': from_email,
                'date_received': date_received,
                'body': body
            })

        # メールの内容を文字列に変換
        emails_content_str = "\n".join([f"Subject: {email['subject']}, From: {email['from']}, Date: {email['date_received']}, Body: {email['body'][:500]}" for email in emails_content])
        
        return "SYSTEM: 検索条件に一致するメールを受信しました。メールの内容をユーザーに伝えてください。\n" + emails_content_str, updated_access_token, credentials.refresh_token
    except Exception as e:
        print(f"e: {e}")
        return f"SYSTEM: メールの検索にエラーが発生しました。{e}", gaccount_access_token, gaccount_refresh_token

def send_gmail_content(gaccount_access_token, gaccount_refresh_token, to_email, subject, body):
    try:
        credentials = create_credentials(
            gaccount_access_token,
            gaccount_refresh_token
        )
        
        if credentials.expired:
            credentials.refresh(Request())
        
        service = build('gmail', 'v1', credentials=credentials)

        # メールのメッセージを作成
        message = email.message.EmailMessage()
        message.set_content(body)
        message['To'] = to_email
        message['From'] = 'me'
        message['Subject'] = subject

        # メッセージをbase64でエンコード
        encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()

        # Gmail APIを使用してメッセージを送信
        send_message = {
            'raw': encoded_message
        }
        send_result = service.users().messages().send(userId='me', body=send_message).execute()

        updated_access_token = credentials.token

        return f"SYSTEM: 次の内容のメールを送信しました。メール送信が完了した旨をユーザーに伝えてください。\nTo: {to_email}\nSubject: {subject}\nBody: {body}", updated_access_token, credentials.refresh_token
    except Exception as e:
        print(f"e: {e}")
        return f"SYSTEM: メール送信にエラーが発生しました。{e}", gaccount_access_token, gaccount_refresh_token

def run_conversation(PUT_GPT_MODEL, messages):
    try:
        response = gpt_client.chat.completions.create(
            model=PUT_GPT_MODEL,
            messages=messages,
        )
        return response  # レスポンス全体を返す
    except Exception as e:
        print(f"An error occurred: {e}")
        return None  # エラー時には None を返す

def run_conversation_f(GPT_MODEL, FUNCTIONS, messages, google_description, custom_description, attempt):
    # ここでfunctionsリストを構成
    functions = []
    #標準ツール
    functions += cf.clock
    #拡張ツール
    if "googlesearch" in FUNCTIONS:
        functions += cf.googlesearch  # extendの代わりに+=を使用
        functions = update_function_descriptions(functions, google_description, "get_googlesearch")
    if "customsearch" in FUNCTIONS:
        functions += cf.customsearch
        functions = update_function_descriptions(functions, custom_description, "get_customsearch1")
    if "wikipedia" in FUNCTIONS:
        functions += cf.wikipedia
    if "scraping" in FUNCTIONS:
        functions += cf.scraping
    if "generateimage" in FUNCTIONS:
        functions += cf.generateimage
    if "googlecalendar" in FUNCTIONS:
        functions += cf.googlecalendar
    if "googlemail" in FUNCTIONS:
        functions += cf.googlemail

    try:
        response = gpt_client.chat.completions.create(
            model=GPT_MODEL,
            messages=messages,
            functions=functions,
            function_call="auto",
        )
        # print(f"functions: {functions}")
        # downdate_function_descriptions(functions, google_description, "get_googlesearch")
        # downdate_function_descriptions(functions, custom_description, "get_customsearch1")
        return response  # レスポンス全体を返す
    except Exception as e:
        # downdate_function_descriptions(functions, google_description, "get_googlesearch")
        # downdate_function_descriptions(functions, custom_description, "get_customsearch1")
        print(f"An error occurred: {e}")
        return None  # エラー時には None を返す

def chatgpt_functions(GPT_MODEL, PUT_GPT_MODEL, FUNCTIONS, messages_for_api, USER_ID, message_id, ERROR_MESSAGE, PAINT_PROMPT, BUCKET_NAME, FILE_AGE, GOOGLE_DESCRIPTION, CUSTOM_DESCRIPTION, gaccount_access_token, gaccount_refresh_token, CORE_IMAGE_TYPE="", VERTEX_IMAGE_MODEL="", max_attempts=5):
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
    get_calendar_called = False
    add_calendar_called = False
    update_calendar_called = False
    delete_calendar_called = False
    get_gmail_list_called = False
    get_gmail_content_called = False
    send_gmail_content_called = False

    while attempt < max_attempts:
        response = run_conversation_f(GPT_MODEL, FUNCTIONS, i_messages_for_api, google_description, custom_description, attempt)
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
                    bot_reply, public_img_url, public_img_url_s = generate_image(CORE_IMAGE_TYPE, VERTEX_IMAGE_MODEL, paint_prompt, arguments["prompt"], user_id, message_id, bucket_name, file_age)
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
                elif function_call.name == "get_calendar" and not get_calendar_called:
                    get_calendar_called = True
                    arguments = json.loads(function_call.arguments)
                    bot_reply, gaccount_access_token, gaccount_refresh_token  = get_calendar(gaccount_access_token, gaccount_refresh_token)
                    i_messages_for_api.append({"role": "assistant", "content": bot_reply})
                    attempt += 1
                elif function_call.name == "add_calendar" and not add_calendar_called:
                    add_calendar_called = True
                    arguments = json.loads(function_call.arguments)
                    bot_reply, gaccount_access_token, gaccount_refresh_token = add_calendar(gaccount_access_token, gaccount_refresh_token, arguments["summary"], arguments["start_time"], arguments["end_time"], arguments["description"], arguments["location"])
                    i_messages_for_api.append({"role": "assistant", "content": bot_reply})
                    attempt += 1
                elif function_call.name == "update_calendar" and not update_calendar_called:
                    update_calendar_called = True
                    arguments = json.loads(function_call.arguments)
                    bot_reply, gaccount_access_token, gaccount_refresh_token = update_calendar(gaccount_access_token, gaccount_refresh_token, arguments["event_id"], arguments["summary"], arguments["start_time"], arguments["end_time"], arguments["description"], arguments["location"])
                    i_messages_for_api.append({"role": "assistant", "content": bot_reply})
                    attempt += 1
                elif function_call.name == "delete_calendar" and not delete_calendar_called:
                    delete_calendar_called = True
                    arguments = json.loads(function_call.arguments)
                    bot_reply, gaccount_access_token, gaccount_refresh_token = delete_calendar(gaccount_access_token, gaccount_refresh_token, arguments["event_id"])
                    i_messages_for_api.append({"role": "assistant", "content": bot_reply})
                    attempt += 1
                elif function_call.name == "get_gmail_list" and not get_gmail_list_called:
                    get_gmail_list_called = True
                    arguments = json.loads(function_call.arguments)
                    bot_reply, gaccount_access_token, gaccount_refresh_token = get_gmail_list(gaccount_access_token, gaccount_refresh_token)
                    i_messages_for_api.append({"role": "assistant", "content": bot_reply})
                    attempt += 1
                elif function_call.name == "get_gmail_content" and not get_gmail_content_called:
                    get_gmail_content_called = True
                    arguments = json.loads(function_call.arguments)
                    bot_reply, gaccount_access_token, gaccount_refresh_token = get_gmail_content(gaccount_access_token, gaccount_refresh_token, arguments["search_query"])
                    i_messages_for_api.append({"role": "assistant", "content": bot_reply})
                    attempt += 1
                elif function_call.name == "send_gmail_content" and not send_gmail_content_called:
                    get_send_content_called = True
                    arguments = json.loads(function_call.arguments)
                    bot_reply, gaccount_access_token, gaccount_refresh_token = send_gmail_content(gaccount_access_token, gaccount_refresh_token, arguments["to_email"], arguments["subject"], arguments["body"])
                    i_messages_for_api.append({"role": "assistant", "content": bot_reply})
                    attempt += 1
                else:
                    response = run_conversation(PUT_GPT_MODEL, i_messages_for_api)
                    if response:
                        bot_reply = response.choices[0].message.content
                    else:
                        bot_reply = "An error occurred while processing the question"
                    return bot_reply, public_img_url, public_img_url_s, gaccount_access_token, gaccount_refresh_token 
            else:
                response = run_conversation(PUT_GPT_MODEL, i_messages_for_api)
                return response.choices[0].message.content, public_img_url, public_img_url_s, gaccount_access_token, gaccount_refresh_token 
        else:
            return ERROR_MESSAGE + " Fail to connect OpenAI.", public_img_url, public_img_url_s, gaccount_access_token, gaccount_refresh_token 
    
    return bot_reply, public_img_url, public_img_url_s, gaccount_access_token, gaccount_refresh_token 
