import openai

openai_api_key = os.getenv('LOCALLLM_API_KEY')
openai.api_version = "2023-05-15"

def run_conversation(api_base, messages):
    openai.api_base = api_base
    try:
        response = openai.chat.completions.create(
            messages=messages,
        )
        return response  # レスポンス全体を返す
    except Exception as e:
        print(f"An error occurred: {e}")
        return None  # エラー時には None を返す

def localllm_functions(LOCALLLM_BASE_URL, messages_for_api):
    public_img_url = None
    public_img_url_s = None

    i_messages_for_api = messages_for_api.copy()

    response = run_conversation(api_base, i_messages_for_api)
    if response:
        bot_reply = response.choices[0].message.content
    else:
        bot_reply = "An error occurred while processing the question"
    return bot_reply, public_img_url, public_img_url_s
    
