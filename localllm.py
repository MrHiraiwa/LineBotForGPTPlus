import openai

openai_api_key = os.getenv('LOCALLLM_API_KEY')
gpt_client = OpenAI(api_key=openai_api_key)


openai.api_key = "..."
openai.api_base = "http://127.0.0.1:5000/v1"
openai.api_version = "2023-05-15"

def run_conversation(messages):
    try:
        response = gpt_client.chat.completions.create(
            messages=messages,
        )
        return response  # レスポンス全体を返す
    except Exception as e:
        print(f"An error occurred: {e}")
        return None  # エラー時には None を返す
