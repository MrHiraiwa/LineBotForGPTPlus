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
# 設定プロンプト
character_setting = "私は有能な秘書です。"
# チャットプロンプトテンプレート
prompt = ChatPromptTemplate.from_messages([
    SystemMessagePromptTemplate.from_template(character_setting),
    MessagesPlaceholder(variable_name="history"),
    HumanMessagePromptTemplate.from_template("{input}")
])
# チャットモデル
llm = ChatOpenAI(
    model_name="gpt-3.5-turbo",
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
conversation = ConversationChain(memory=memory, prompt=prompt, llm=llm, verbose=True)

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

    # Get memory state from Firestore
    memory_state = get_user_memory(user_id)
    if memory_state is not None:
        memory.set_state(memory_state)

    response = conversation.predict(input=event.message.text)

    # Save memory state to Firestore
    memory_state = memory.get_state()
    save_user_memory(user_id, memory_state)

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=response)
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
