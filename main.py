import os
from flask import Flask, request, abort
from google.cloud import firestore
from googleapiclient.discovery import build
from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
)
from langchain.prompts.chat import (
    ChatPromptTemplate,
    MessagesPlaceholder,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
)
from langchain.chat_models import ChatOpenAI
from langchain.memory import ConversationBufferWindowMemory, ConversationTokenBufferMemory, ConversationSummaryBufferMemory
from langchain.chains import ConversationChain
import tiktoken
import pickle

app = Flask(__name__)

# LINE Messaging APIの準備
line_bot_api = LineBotApi(os.environ["CHANNEL_ACCESS_TOKEN"])
handler = WebhookHandler(os.environ["CHANNEL_SECRET"])
admin_password = os.environ["ADMIN_PASSWORD"])

REQUIRED_ENV_VARS = [
    "BOT_NAME",
    "SYSTEM_PROMPT",
    "GPT_MODEL"
]

DEFAULT_ENV_VARS = {
    'BOT_NAME': '秘書,secretary,秘书,เลขานุการ,sekretaris'
    'SYSTEM_PROMPT': 'あなたは有能な秘書です。',
    'GPT_MODEL': 'gpt-3.5-turbo'
}
def reload_settings():
    global BOT_NAME, SYSTEM_PROMPT
    BOT_NAME = get_setting('BOT_NAME')
    if BOT_NAME:
        BOT_NAME = BOT_NAME.split(',')
    else:
        BOT_NAME = []
    SYSTEM_PROMPT = get_setting('SYSTEM_PROMPT') 
    GPT_MODEL = get_setting('GPT_MODEL')
    
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
    
def get_setting_user(userid, key):
    doc_ref = db.collection(u'users').document(userid) 
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
    max_tokens=256,
    temperature=1,
    streaming=True
)
db = firestore.Client()

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

def get_user_memory(user_id):
    doc_ref = db.collection('memory').document(user_id)
    doc = doc_ref.get()
    if doc.exists:
        memory_state = pickle.loads(doc.to_dict()['memory'])
        return memory_state
    else:
        return None

def save_user_memory(user_id, memory):
    doc_ref = db.collection('memory').document(user_id)
    memory_state = pickle.dumps(memory)
    doc_ref.set({
        'memory': memory_state
    })

    
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

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_id = event.source.user_id
    profile = get_profile(user_id)
    display_name = profile.display_name

    # Get memory state from Firestore
    memory_state = get_user_memory(user_id)
    if memory_state is not None:
        memory.set_state(memory_state)

    response = conversation.predict(input=display_name + ":" + event.message.text)

    # Save memory state to Firestore
    memory_state = memory.get_state()
    save_user_memory(user_id, memory_state)

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=response)
    )
    
def get_profile(user_id):
    profile = line_bot_api.get_profile(user_id)
    return profile

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
