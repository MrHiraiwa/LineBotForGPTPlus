from flask import session
from google_auth_oauthlib.flow import Flow
import os
import google.auth.transport.requests

# 環境変数からOAuth 2.0クライアントの設定を読み込む
google_client_id = os.getenv("GOOGLE_CLIENT_ID")
google_client_secret = os.getenv("GOOGLE_CLIENT_SECRET")

def create_oauth_session(line_user_id, GACCOUNT_AUTH_URL):
    try:
        # クライアント設定
        client_config = {
            "web": {
                "client_id": google_client_id,
                "client_secret": google_client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            }
        }
        GACCOUNT_AUTH_URL = GACCOUNT_AUTH_URL
        # OAuth 2.0 クライアントフローを設定
        flow = Flow.from_client_config(
            client_config=client_config,
            scopes=['openid', 'https://www.googleapis.com/auth/userinfo.email', 'https://www.googleapis.com/auth/userinfo.profile'])
        flow.redirect_uri = GACCOUNT_AUTH_URL

        authorization_url, state = flow.authorization_url(prompt='consent')

        # 状態をセッションに保存
        session['state'] = state
        session['line_user_id'] = line_user_id
            
        print(f"line_user_id: {line_user_id}")

        return authorization_url
    except Exception as e:
        # エラーを標準出力に記録
        print(f"Error creating oauth session for user {line_user_id}: {e}")

        # エラーが発生した場合には None を返す
        return None
