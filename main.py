import os
import pytz
from datetime import datetime, time, timedelta
from flask import Flask, request, render_template, session, redirect, url_for, jsonify, abort
from google.cloud import firestore
from googleapiclient.discovery import build
from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.models import QuickReply, QuickReplyButton, MessageAction, LocationAction, URIAction
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, AudioMessage, TextSendMessage, AudioSendMessage,
    QuickReply, QuickReplyButton, MessageAction, LocationAction, URIAction,
)
from langchain.prompts.chat import (
    ChatPromptTemplate,
    MessagesPlaceholder,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
)
from langchain.chat_models import ChatOpenAI
from langchain.memory import (
    ConversationBufferWindowMemory,
    ConversationTokenBufferMemory,
    ConversationSummaryBufferMemory,
)
from langchain.chains import ConversationChain
import tiktoken
import pickle

from whisper import get_audio
from voice import put_audio

# LINE Messaging APIの準備
line_bot_api = LineBotApi(os.environ["CHANNEL_ACCESS_TOKEN"])
handler = WebhookHandler(os.environ["CHANNEL_SECRET"])
admin_password = os.environ["ADMIN_PASSWORD"]
jst = pytz.timezone('Asia/Tokyo')
nowDate = datetime.now(jst) 
nowDateStr = nowDate.strftime('%Y/%m/%d %H:%M:%S %Z') + "\n"
REQUIRED_ENV_VARS = [
    "BOT_NAME",
    "SYSTEM_PROMPT",
    "GPT_MODEL",
    "FORGET_KEYWORDS",
    "FORGET_GUIDE_MESSAGE",
    "FORGET_MESSAGE",
    "FORGET_QUICK_REPLY",
    "ERROR_MESSAGE",
    "LINE_REPLY",
    "VOICE_GENDER",
    "BACKET_NAME",
    "FILE_AGE",
]

DEFAULT_ENV_VARS = {
    'BOT_NAME': '秘書,secretary,秘书,เลขานุการ,sekretaris',
    'SYSTEM_PROMPT': 'あなたは有能な秘書です。',
    'GPT_MODEL': 'gpt-3.5-turbo',
    'FORGET_KEYWORDS': '忘れて,わすれて',
    'FORGET_GUIDE_MESSAGE': 'ユーザーからあなたの記憶の削除が命令されました。別れの挨拶をしてください。',
    'FORGET_MESSAGE': '記憶を消去しました。',
    'FORGET_QUICK_REPLY': '😱記憶を消去',
    'ERROR_MESSAGE': '現在アクセスが集中しているため、しばらくしてからもう一度お試しください。',
    'LINE_REPLY': 'Text',
    'VOICE_GENDER': 'female',
    'BACKET_NAME': 'あなたがCloud Strageに作成したバケット名を入れてください。',
    'FILE_AGE': '7'
}

db = firestore.Client()

def reload_settings():
    global BOT_NAME, SYSTEM_PROMPT, GPT_MODEL
    global FORGET_KEYWORDS, FORGET_GUIDE_MESSAGE, FORGET_MESSAGE, ERROR_MESSAGE, FORGET_QUICK_REPLY
    global LINE_REPLY, VOICE_GENDER, BACKET_NAME, FILE_AGE
    BOT_NAME = get_setting('BOT_NAME')
    if BOT_NAME:
        BOT_NAME = BOT_NAME.split(',')
    else:
        BOT_NAME = []
    SYSTEM_PROMPT = get_setting('SYSTEM_PROMPT') 
    GPT_MODEL = get_setting('GPT_MODEL')
    FORGET_KEYWORDS = get_setting('FORGET_KEYWORDS')
    if FORGET_KEYWORDS:
        FORGET_KEYWORDS = FORGET_KEYWORDS.split(',')
    else:
        FORGET_KEYWORDS = []
    FORGET_GUIDE_MESSAGE = get_setting('FORGET_GUIDE_MESSAGE')
    FORGET_MESSAGE = get_setting('FORGET_MESSAGE')
    FORGET_QUICK_REPLY = get_setting('FORGET_QUICK_REPLY')
    ERROR_MESSAGE = get_setting('ERROR_MESSAGE')
    LINE_REPLY = get_setting('LINE_REPLY')
    VOICE_GENDER = get_setting('VOICE_GENDER')
    BACKET_NAME = get_setting('BACKET_NAME')
    FILE_AGE = get_setting('FILE_AGE')
    
def get_setting(key):
    doc_ref = db.collection(u'settings').document('app_settings')
    doc = doc_ref.get()

    if doc.exists:
        doc_dict = doc.to_dict()
        if key not in doc_dict:
            # If the key does not exist in the document, use the default value
            default_value = DEFAULT_ENV_VARS.get(key, "")
            doc_ref.set({key: default_value}, merge=True)  # Add the new setting to the database
            return default_value
        else:
            return doc_dict.get(key)
    else:
        # If the document does not exist, create it using the default settings
        save_default_settings()
        return DEFAULT_ENV_VARS.get(key, "")
    
def get_setting_user(user_id, key):
    doc_ref = db.collection(u'users').document(user_id) 
    doc = doc_ref.get()

    if doc.exists:
        doc_dict = doc.to_dict()
        if key not in doc_dict:
            if key == 'start_free_day':
                start_free_day = datetime.now(jst)
                doc_ref.set({'start_free_day': start_free_day}, merge=True)
            return ''
        else:
            return doc_dict.get(key)
    else:
        return ''
    
def save_default_settings():
    doc_ref = db.collection(u'settings').document('app_settings')
    doc_ref.set(DEFAULT_ENV_VARS, merge=True)


def update_setting(key, value):
    doc_ref = db.collection(u'settings').document('app_settings')
    doc_ref.update({key: value})
    
reload_settings()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', default='YOUR-DEFAULT-SECRET-KEY')


@app.route('/reset_logs', methods=['POST'])
def reset_logs():
    if 'is_admin' not in session or not session['is_admin']:
        return redirect(url_for('login'))
    else:
        try:
            users_ref = db.collection(u'users')
            users = users_ref.stream()
            for user in users:
                user_ref = users_ref.document(user.id)
                user_ref.delete()
            return 'All user data reset successfully', 200
        except Exception as e:
            print(f"Error resetting user data: {e}")
            return 'Error resetting user data', 500

@app.route('/login', methods=['GET', 'POST'])
def login():
    attempts_doc_ref = db.collection(u'settings').document('admin_attempts')
    attempts_doc = attempts_doc_ref.get()
    attempts_info = attempts_doc.to_dict() if attempts_doc.exists else {}

    attempts = attempts_info.get('attempts', 0)
    lockout_time = attempts_info.get('lockout_time', None)

    # ロックアウト状態をチェック
    if lockout_time:
        if datetime.now(jst) < lockout_time:
            return render_template('login.html', message='Too many failed attempts. Please try again later.')
        else:
            # ロックアウト時間が過ぎたらリセット
            attempts = 0
            lockout_time = None

    if request.method == 'POST':
        password = request.form.get('password')

        if password == admin_password:
            session['is_admin'] = True
            # ログイン成功したら試行回数とロックアウト時間をリセット
            attempts_doc_ref.set({'attempts': 0, 'lockout_time': None})
            return redirect(url_for('settings'))
        else:
            attempts += 1
            lockout_time = datetime.now(jst) + timedelta(minutes=10) if attempts >= 5 else None
            attempts_doc_ref.set({'attempts': attempts, 'lockout_time': lockout_time})
            return render_template('login.html', message='Incorrect password. Please try again.')

    return render_template('login.html')


@app.route('/settings', methods=['GET', 'POST'])
def settings():
    if 'is_admin' not in session or not session['is_admin']:
        return redirect(url_for('login'))
    
    current_settings = {key: get_setting(key) or DEFAULT_ENV_VARS.get(key, '') for key in REQUIRED_ENV_VARS}

    if request.method == 'POST':
        for key in REQUIRED_ENV_VARS:
            value = request.form.get(key)
            if value:
                update_setting(key, value)
        return redirect(url_for('settings'))
    return render_template(
    'settings.html', 
    settings=current_settings, 
    default_settings=DEFAULT_ENV_VARS, 
    required_env_vars=REQUIRED_ENV_VARS
    )

# 設定プロンプト
character_setting = SYSTEM_PROMPT
# チャットプロンプトテンプレート
prompt = ChatPromptTemplate.from_messages([
    SystemMessagePromptTemplate.from_template(character_setting),
    MessagesPlaceholder(variable_name="history"),
    HumanMessagePromptTemplate.from_template("{input}")
])
# チャットモデル
llm = ChatOpenAI(
    model_name=GPT_MODEL,
    temperature=1,
    streaming=True
)

class CustomConversationSummaryBufferMemory(ConversationSummaryBufferMemory):
    def get_state(self):
        return self.__dict__

    def set_state(self, state):
        self.__dict__.update(state)

# メモリ
#memory = ConversationBufferWindowMemory(k=3, return_messages=True)
# memory = ConversationSummaryBufferMemory(llm=llm, max_token_limit=2000, return_messages=True)
memory = CustomConversationSummaryBufferMemory(llm=llm, max_token_limit=2000, return_messages=True)

# 会話チェーン
conversation = ConversationChain(memory=memory, prompt=prompt, llm=llm, verbose=False)
    
@app.route("/", methods=["POST"])
def callback():
    # get X-Line-Signature header value
    signature = request.headers["X-Line-Signature"]
    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)
    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        print("Invalid signature. Please check your channel access token/channel secret.")
        abort(400)
    return "OK"

@handler.add(MessageEvent, message=(TextMessage, AudioMessage))
def handle_message(event):
    reload_settings()
    try:
        user_id = event.source.user_id
        profile = get_profile(user_id)
        display_name = profile.display_name
        user_message = []
        reply_token = event.reply_token
        message_type = event.message.type
        message_id = event.message.id
        exec_audio = False
        exec_functions = False
        quick_reply_items = []
        head_message = ""
        if message_type == 'text':
            user_message = event.message.text
        elif message_type == 'audio':
            exec_audio = True
            user_message = get_audio(message_id)
            
        db = firestore.Client()
        doc_ref = db.collection(u'users').document(user_id)
        
        @firestore.transactional
        def update_in_transaction(transaction, doc_ref):
            doc = doc_ref.get(transaction=transaction)
            if doc.exists:
                user = doc.to_dict()
                memory_state = user['memory']
            
            if memory_state is not None:
                memory.set_state(memory_state)
        
            if user_message.strip() == FORGET_QUICK_REPLY:
                line_reply(reply_token, FORGET_MESSAGE, 'text')
                memory_state = []
        
            if any(word in user_message for word in FORGET_KEYWORDS) and exec_functions == False:
                    quick_reply_items.append(['message', FORGET_QUICK_REPLY, FORGET_QUICK_REPLY])
                    head_message = head_message + FORGET_GUIDE_MESSAGE                
                
            response = conversation.predict(input=nowDateStr + " " + head_message + "\n" + display_name + ":" + user_message)
        
            success = []
            public_url = []
            local_path = []
            duration = []
            send_message_type = 'text'
            if  LINE_REPLY == "Both" or (LINE_REPLY == "Audio" and len(quick_reply_items) == 0 and exec_functions == False):
                public_url, local_path, duration = put_audio(user_id, message_id, response, BACKET_NAME, FILE_AGE)
                if  LINE_REPLY == "Both":
                    success = line_push(user_id, public_url, 'audio', None, duration)
                    send_message_type = 'text'
                elif (LINE_REPLY == "Audio" and len(quick_reply_items) == 0) or (LINE_REPLY == "Audio" and exec_functions == False):
                    response = public_url
                    send_message_type = 'audio'
                    
            line_reply(reply_token, response, send_message_type, quick_reply_items, duration)
        
            if success:
                delete_local_file(local_path) 
            
            # Save memory state to Firestore
             memory_state = pickle.dumps(memory.get_state())
            transaction.update(doc_ref, {'memory': memory_state})
        return update_in_transaction(db.transaction(), doc_ref)
    except KeyError:
        return 'Not a valid JSON', 200 
    except Exception as e:
        print(f"Error in lineBot: {e}")
        line_reply(reply_token, ERROR_MESSAGE, 'text')
        raise
    finally:
        return 'OK'


#呼び出しサンプル
#line_reply(reply_token, 'Please reply', 'Text', [['message', 'Yes', 'Yes'], ['message', 'No', 'No'], ['uri', 'Visit website', 'https://example.com']])

def line_reply(reply_token, response, send_message_type, quick_reply_items=None, audio_duration=None):
    if send_message_type == 'text':
        if quick_reply_items:
            # Create QuickReplyButton list from quick_reply_items
            quick_reply_button_list = []
            for item in quick_reply_items:
                action_type, label, action_data = item
                if action_type == 'message':
                    action = MessageAction(label=label, text=action_data)
                elif action_type == 'location':
                    action = LocationAction(label=label)
                elif action_type == 'uri':
                    action = URIAction(label=label, uri=action_data)
                else:
                    print(f"Unknown action type: {action_type}")
                    continue
                quick_reply_button_list.append(QuickReplyButton(action=action))

            # Create QuickReply
            quick_reply = QuickReply(items=quick_reply_button_list)

            # Add QuickReply to TextSendMessage
            message = TextSendMessage(text=response, quick_reply=quick_reply)
        else:
            message = TextSendMessage(text=response)
    elif send_message_type == 'audio':
        message = AudioSendMessage(original_content_url=response, duration=audio_duration)
    else:
        print(f"Unknown REPLY type: {send_message_type}")
        return

    line_bot_api.reply_message(
        reply_token,
        message
    )


def line_push(user_id, response, send_message_type, quick_reply_items=None, audio_duration=None):
    if send_message_type == 'text':
        if quick_reply_items:
            # Create QuickReplyButton list from quick_reply_items
            quick_reply_button_list = []
            for item in quick_reply_items:
                action_type, label, action_data = item
                if action_type == 'message':
                    action = MessageAction(label=label, text=action_data)
                elif action_type == 'location':
                    action = LocationAction(label=label)
                elif action_type == 'uri':
                    action = URIAction(label=label, uri=action_data)
                else:
                    print(f"Unknown action type: {action_type}")
                    continue
                quick_reply_button_list.append(QuickReplyButton(action=action))

            # Create QuickReply
            quick_reply = QuickReply(items=quick_reply_button_list)

            # Add QuickReply to TextSendMessage
            message = TextSendMessage(text=response, quick_reply=quick_reply)
        else:
            message = TextSendMessage(text=response)
    elif send_message_type == 'audio':
        message = AudioSendMessage(original_content_url=response, duration=audio_duration)
    else:
        print(f"Unknown REPLY type: {send_message_type}")
        return

    line_bot_api.push_message(user_id, message)

    
def get_profile(user_id):
    profile = line_bot_api.get_profile(user_id)
    return profile

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
