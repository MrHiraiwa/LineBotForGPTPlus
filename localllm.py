import os
import requests

LOCALLLM_API_KEY = os.getenv('LOCALLLM_API_KEY')

def run_conversation(api_base, messages):
    try:
        response = requests.post(
            api_base,
            headers={'Authorization': f'Bearer {LOCALLLM_API_KEY}', 'Content-Type': 'application/json'},
            json={'messages': messages, 'mode': 'chat', 'character': 'Example'},
            timeout=50
        )
        response.raise_for_status()  # 追加: ステータスコードがHTTPエラーの場合、例外を発生させる
        return response.json()  # JSONレスポンスを返す
    except requests.exceptions.Timeout:
        print("OpenAI API timed out")
        return "OpenAI API timed out."
    except requests.exceptions.RequestException as e:
        # その他のリクエスト関連の例外を捕捉
        print(f"Request failed: {e}")
        return "Request failed."

def localllm_functions(LOCALLLM_BASE_URL, messages_for_api):
    public_img_url = None
    public_img_url_s = None

    response = run_conversation(LOCALLLM_BASE_URL, messages_for_api)
    if response and 'choices' in response and len(response['choices']) > 0:
        bot_reply = response['choices'][0]['message']['content']
    else:
        bot_reply = "An error occurred while processing the question"
    return bot_reply, public_img_url, public_img_url_s
