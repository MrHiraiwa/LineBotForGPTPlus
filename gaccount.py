from google_auth_oauthlib.flow import Flow
import os
import google.auth.transport.requests

def create_oauth_session(GACCOUNT_CALLBACK_URL):
    # OAuth 2.0 クライアントフローを設定
    flow = Flow.from_client_secrets_file(
        'path/to/client_secrets.json',
        scopes=['openid', 'https://www.googleapis.com/auth/userinfo.email', 'https://www.googleapis.com/auth/userinfo.profile'],
        redirect_uri=GACCOUNT_CALLBACK_URL)

    authorization_url, state = flow.authorization_url(prompt='consent')

    # 状態をセッションに保存
    session['state'] = state

    return authorization_url
