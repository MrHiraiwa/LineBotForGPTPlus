from google_auth_oauthlib.flow import Flow
import os
import google.auth.transport.requests

def create_oauth_session(line_user_id, GACCOUNT_CALLBACK_URL):
    try:
        # OAuth 2.0 クライアントフローを設定
        flow = Flow.from_client_secrets_file(
            'path/to/client_secrets.json',
            scopes=['openid', 'https://www.googleapis.com/auth/userinfo.email', 'https://www.googleapis.com/auth/userinfo.profile'],
            redirect_uri=GACCOUNT_CALLBACK_URL)

        authorization_url, state = flow.authorization_url(prompt='consent')

        # 状態をセッションに保存
        session['state'] = state

        return authorization_url
        
    except Exception as e:
        # エラーを標準出力に記録
        print(f"Error creating oauth session for user {line_user_id}: {e}")

        # エラーが発生した場合には None を返す
        return None
