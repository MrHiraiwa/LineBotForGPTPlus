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
import re
import time

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

i_prompt = ""
user_id = []
message_id = []
bucket_name = []
file_age = []

public_img_url = ""
public_img_url_s = ""
gaccount_access_token = ""
gaccount_refresh_token = ""


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
        global public_img_url, public_img_url_s
        filename = str(uuid.uuid4())
        blob_path = f'{user_id}/{message_id}.png'
        preview_blob_path = f'{user_id}/{message_id}_s.png'
        client = OpenAI(api_key=openai_api_key)
        prompt = " ".join(sentence) + "\n" + i_prompt
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
            
            time.sleep(2)
        
            return f"SYSTEM:{prompt}のキーワードで画像を生成し、表示しました。画像が生成された旨をメッセージで伝えてください。"
        except Exception as e:
            print(f"generate_image error: {e}" )
            return f"SYSTEM: 画像生成にエラーが発生しました。{e}"

def create_credentials(gaccount_access_token, gaccount_refresh_token):
    return Credentials(
        token=gaccount_access_token,
        refresh_token=gaccount_refresh_token,
        client_id=google_client_id,
        client_secret=google_client_secret,
        token_uri='https://oauth2.googleapis.com/token'
    )
    
class Getcalendar(BaseTool):
    def use_tool(self, max_chars=1000):
        global gaccount_access_token, gaccount_refresh_token
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
                gaccount_access_token = credentials.token
                gaccount_refresh_token = credentials.refresh_token
                return "直近のイベントはありません。"

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

            gaccount_access_token = credentials.token
            gaccount_refresh_token = credentials.refresh_token

            return "SYSTEM:カレンダーのイベントを取得しました。イベント内容を要約してください。" + events_str[:max_chars]
        
        except Exception as e:
            print(f"Error during calendar event retrieval: {e}")
            return f"SYSTEM: カレンダーのイベント取得にエラーが発生しました。{e}"

class Addcalendar(BaseTool):
    def use_tool(self, summary, start_time, end_time, description=None, location=None):
        global gaccount_access_token, gaccount_refresh_token
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
    
            # 成功した場合、イベントの詳細を含むメッセージを返す
            gaccount_access_token = credentials.token
            gaccount_refresh_token = credentials.refresh_token
            return f"次のイベントが追加されました: summary={summary}, start_time={start_time},  end_time={end_time}, description={description}, location={location}"
    
        except Exception as e:
            return f"イベント追加に失敗しました: {e}"

class Updatecalendar(BaseTool):
    def use_tool(self, event_id, summary=None, start_time=None, end_time=None, description=None, location=None):
        global gaccount_access_token, gaccount_refresh_token
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

            gaccount_access_token = credentials.token
            gaccount_refresh_token = credentials.refresh_token

            return f"イベントが更新されました: {updated_event_result['summary']}"
        except Exception as e:
            return f"イベント更新に失敗しました: {e}"

class Deletecalendar(BaseTool):
    def use_tool(self, event_id):
        global gaccount_access_token, gaccount_refresh_token
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

            gaccount_access_token = credentials.token
            gaccount_refresh_token = credentials.refresh_token

            return f"イベント「{event_summary}」が削除されました"
        except Exception as e:
            return f"イベント削除に失敗しました: {e}"



def run_conversation(CLAUDE_MODEL, SYSTEM_PROMPT, messages):
    try:
        response = claude_client.messages.create(
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            messages=messages,
            model=CLAUDE_MODEL,
        )
        return response  # レスポンス全体を返す
    except Exception as e:
        print(f"An error occurred: {e}")
        return None  # エラー時には None を返す

def run_conversation_f(CLAUDE_MODEL, FUNCTIONS, messages, GOOGLE_DESCRIPTION, CUSTOM_DESCRIPTION):
    try:
        clock_tool_name = "perform_clock"
        clock_tool_description = "useful for when you need to know what time it is."
        clock_tool_parameters = [
        ]

        googlesearch_tool_name = "perform_googlesearch"
        googlesearch_tool_description = GOOGLE_DESCRIPTION
        googlesearch_tool_parameters = [
            {"name": "words", "type": "str", "description": "a search key word"}
        ]

        customsearch1_tool_name = "perform_customsearch1"
        customsearch1_tool_description = CUSTOM_DESCRIPTION
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
        generateimage_tool_description = "useful for when you need to  generate an image by the sentence."
        generateimage_tool_parameters = [
            {"name": "sentence", "type": "str", "description": "a text for image generation"}
        ]

        getcalendar_tool_name = "perform_getcalendar"
        getcalendar_tool_description = "You can add schedules."
        getcalendar_tool_parameters = [
        ]

        addcalendar_tool_name = "perform_addcalendar"
        addcalendar_tool_description = "You can add schedules."
        addcalendar_tool_parameters = [
            {"name": "summary", "type": "str", "description": "スケジュールのサマリー(必須)"},
            {"name": "start_time", "type": "str", "description": "スケジュールの開始時間をRFC3339フォーマットの日本時間で指定(必須)"},
            {"name": "end_time", "type": "str", "description": "スケジュールの終了時間をRFC3339フォーマットの日本時間で指定(必須)"},
            {"name": "description", "type": "str", "description": "スケジュールした内容の詳細な説明(必須)"},
            {"name": "location", "type": "str", "description": "スケジュールの内容を実施する場所(必須)"}
        ]

        updatecalendar_tool_name = "perform_updatecalendar"
        updatecalendar_tool_description = "You can update schedules by the event ID of the schedule."
        updatecalendar_tool_parameters = [
            {"name": "event_id", "type": "str", "description": "スケジュールのイベントID(必須)"},
            {"name": "summary", "type": "str", "description": "更新後のスケジュールのサマリー(必須)"},
            {"name": "start_time", "type": "str", "description": "更新後のスケジュールの開始時間をRFC3339フォーマットの日本時間で指定(必須)"},
            {"name": "end_time", "type": "str", "description": "更新後のスケジュールの終了時間をRFC3339フォーマットの日本時間で指定(必須)"},
            {"name": "description", "type": "str", "description": "更新後のスケジュールした内容の詳細な説明(必須)"},
            {"name": "location", "type": "str", "description": "更新後のスケジュールの内容を実施する場所(必須)"},
            
        ]
        
        deletecalendar_tool_name = "perform_deletecalendar"
        deletecalendar_tool_description = "You can delete schedules by the event ID of the schedule."
        deletecalendar_tool_parameters = [
            {"name": "event_id", "type": "str", "description": "削除対象のスケジュールのイベントID(必須)"}
        ]


        clock_tool = Clock(clock_tool_name, clock_tool_description, clock_tool_parameters)
        googlesearch_tool = Googlesearch(googlesearch_tool_name, googlesearch_tool_description, googlesearch_tool_parameters)
        customsearch1_tool = Customsearch1(customsearch1_tool_name, customsearch1_tool_description, customsearch1_tool_parameters)
        wikipediasearch_tool = Wikipediasearch(wikipediasearch_tool_name, wikipediasearch_tool_description, wikipediasearch_tool_parameters)
        scraping_tool = Scraping(scraping_tool_name, scraping_tool_description, scraping_tool_parameters)
        generateimage_tool = Generateimage(generateimage_tool_name, generateimage_tool_description, generateimage_tool_parameters)
        getcalendar_tool = Getcalendar(getcalendar_tool_name, getcalendar_tool_description, getcalendar_tool_parameters)
        addcalendar_tool = Addcalendar(addcalendar_tool_name, addcalendar_tool_description, addcalendar_tool_parameters)
        updatecalendar_tool = Updatecalendar(updatecalendar_tool_name, updatecalendar_tool_description, updatecalendar_tool_parameters)
        deletecalendar_tool = Deletecalendar(deletecalendar_tool_name, deletecalendar_tool_description, deletecalendar_tool_parameters)

        functions = []
        functions.append(clock_tool)

        if "googlesearch" in FUNCTIONS:
            functions.append(googlesearch_tool)
        if "customsearch" in FUNCTIONS:
            functions.append(customsearch1_tool)
        if "wikipedia" in FUNCTIONS:
            functions.append(wikipediasearch_tool)
        if "scraping" in FUNCTIONS:
            functions.append(scraping_tool)
        if "generateimage" in FUNCTIONS:
            functions.append(generateimage_tool)
        if "googlecalender" in FUNCTIONS:
            functions.append(getcalendar_tool)
            functions.append(addcalendar_tool)
            functions.append(updatecalendar_tool)
            functions.append(deletecalendar_tool)
        
        all_tool_user = ToolUser(functions, CLAUDE_MODEL)
        response = all_tool_user.use_tools(messages, execution_mode='automatic')

        # re.DOTALLフラグを使って、改行を含むテキストもマッチさせる
        result_match = re.search(r'<result>(.*?)</result>', response, re.DOTALL)
        if result_match:
            result_content = result_match.group(1)  # タグ内の文字列を取得
            return result_content.strip()  # 先頭と末尾の空白文字を削除
        else:
            return response
    except Exception as e:
        print(f"An error occurred: {e}")
        return None  # エラー時には None を返す

def claude_functions(CLAUDE_MODEL, FUNCTIONS, SYSTEM_PROMPT ,messages_for_api, USER_ID, MESSAGE_ID, ERROR_MESSAGE, PAINT_PROMPT, BUCKET_NAME, FILE_AGE, GOOGLE_DESCRIPTION, CUSTOM_DESCRIPTION, i_gaccount_access_token="", i_gaccount_refresh_token="", max_attempts=5):
    global i_prompt, user_id, message_id, bucket_name, file_age
    global public_img_url, public_img_url_s
    global gaccount_access_token, gaccount_refresh_token
    gaccount_access_token = i_gaccount_access_token
    gaccount_refresh_token = i_gaccount_refresh_token
    public_img_url = None
    public_img_url_s = None
    i_prompt = PAINT_PROMPT
    user_id = USER_ID
    message_id = MESSAGE_ID
    bucket_name = BUCKET_NAME
    file_age = FILE_AGE
    i_messages_for_api = messages_for_api.copy()
    last_messages_for_api = i_messages_for_api[-1]
    head_messages_for_api= [{'role': 'user', 'content': SYSTEM_PROMPT}] 
    head_messages_for_api.extend(i_messages_for_api)
    response = run_conversation_f(CLAUDE_MODEL, FUNCTIONS, head_messages_for_api, GOOGLE_DESCRIPTION, CUSTOM_DESCRIPTION)
    bot_reply = response

    return bot_reply, public_img_url, public_img_url_s, gaccount_access_token, gaccount_refresh_token
