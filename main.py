import os
from flask import Flask, request, abort
from google.cloud import firestore
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
from langchain.memory import ConversationBufferWindowMemory, ConversationTokenBufferMemory
from langchain.chains import ConversationChain
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from langchain.agents import load_tools
import tiktoken

app = Flask(__name__)

# Firestoreの準備
db = firestore.Client()

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

tools = load_tools(["google-search"], llm=llm)

# メモリ
memory = ConversationTokenBufferMemory(llm=llm, max_token_limit=2000, return_messages=True)

# 会話チェーン
conversation = ConversationChain(memory=memory, prompt=prompt, llm=llm, verbose=True)

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

    # ユーザーIDを基にFirestoreからドキュメントを取得
    doc_ref = db.collection('users').document(user_id)
    doc = doc_ref.get()

    # ドキュメントが存在すれば、会話の履歴をメモリに読み込む
    if doc.exists:
        memory.set_memory(doc.to_dict()["history"])
    else:
        # ドキュメントが存在しなければ、新たに作成する
        doc_ref.set({"history": []})

    # メッセージを処理して応答を生成
    response = conversation.predict(input=event.message.text)

    # メモリの内容をFirestoreに保存
    doc_ref.update({"history": memory.get_memory()})

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=response)
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
