import requests

LOCALLLM_API_KEY = os.getenv('LOCALLLM_API_KEY')
openai.api_version = "2023-05-15"

def run_conversation(api_base, messages):
    try:
        response = requests.post(
            api_base,
            headers={'Authorization': f'Bearer {LOCALLLM_API_KEY}'},
            json={'messages': [systemRole()] + temp_messages_final},
            "mode": "chat","character": "Example"
            timeout=50
        )
            except requests.exceptions.Timeout:
                print("OpenAI API timed out")
                callLineApi(ERROR_MESSAGE, replyToken, {'items': quick_reply})
                return 'OK'

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
    
