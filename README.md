# LineBotForGPTPlus

このリポジトリは、LINE上で動作するPythonベースのチャットボットです。このボットはChatGPT APIを使用して、ユーザからのメッセージに対してレスポンスを生成します。
このボットプログラムの機能や設置方法についての詳細は以下のページを確認してください。手順書は有料記事なので無料で利用したい人はココの記載を見て頑張ってください。
[https://note.com/modern_echium586](https://note.com/modern_echium586/n/n3c3fdf2149e5)

## 機能
以下の機能を持っています。：

- Web設定: パラメーターをWeb画面で設定可能です。コードを変更する必要はありません。
- ボット会話: 設定したキャラクター性でChatGPTと会話できます。グループチャットにも対応します。
- Web検索+: Google Custom Search APIを用いてWeb検索が行えます。
- 地図検索: Geocoding APIとGoogle Custom Search APIを用いて地図検索が行なえます。
- カレンダー連携: Googleカレンダーと連携してスケジュールの追加や削除が行えます。
- Gmail連携: Gmailと連携してメールの確認が行えます
- 画像認識: Cloud Visionを用いて画像認識が行なえます。
- 画像生成: OpenAI DALL-E 3を用いて画像生成が行なえます。
- 音声認識: OpenAI Whisperを用いて音声認識が行えます。
- 音声生成: Google text-to-SpeechまたはVOICEVOXを用いて音声会話が行えます。
- 英語と中国語の訛の切り替え:Google text-to-Speech利用時のみユーザー操作で中国語音声の北京語と広東語の切り替えが行えます。英語も切り替えられます。
- 音声速度:Google text-to-Speech利用時のみユーザー操作で音声速度の変更が行えます。
- 翻訳モード:Google text-to-Speech利用時のみ入力した文字を翻訳します。
- 支払い機能:Stripeと連携して利用料の支払いが行えます。

## セットアップ
以下のステップに従ってセットアップしてください：
1. Google Cloud Runでデプロイします：Google Cloud Consoleでプロジェクトを作成しCloud Run APIを有効にし、本レポジトリを指定してデプロイします。 デプロイの際は以下の環境変数を設定する必要があります。
2. 同じプロジェクト内でFirestoreを有効にします：左側のナビゲーションメニューで「Firestore」を選択し、Firestoreをプロジェクトで有効にします。
3. データベースを作成します：Firestoreダッシュボードに移動し、「データベースの作成」をクリックします。「ネイティブ」モードを選択しデータベース名を付けてDBを作成します。
5. Custom Search、Cloud Vision、Geocoding API、Text-To-Speech、Google Calender、Gmail APIのAPIを有効にします。
6. Oauth認証を設定します。
7. Cloud Strageのバケットをインターネット公開で設定します。
8. Cloud RunのURLに「/login」を付与して管理画面にログインし、各パラメータを設定します
9. LINE Developerにログインします：https://account.line.biz/login
10. チャネルを作成し、webhookの宛先にCloud RunのサービスURLを指定します。
11. VOICEVOXを利用する場合はサーバを別途用意してください。

## 環境変数
- CHANNEL_ACCESS_TOKEN:LINEで発行したチャネルアクセストークンを設定してください。
- CHANNEL_SECRET:LINEで発行したチャンネルシークレットキーを設定してください。
- OPENAI_API_KEY: OpenAIのAPIキーを入力してください。
- GOOGLE_API_KEY:Google Cloud Pratformに発行したAPIキーを入力してください。
- GOOGLE_CSE_ID:Google Cloud PratformのCustom Search設定時に発行した検索エンジンIDを設定してください。
- SECRET_KEY: DBに保存するメッセージの暗号化と復号化に使用される秘密鍵です。適当な文字列を入れてください。
- ADMIN_PASSWORD:WEBの管理画面のログインに使用する管理者パスワードです。このシステムはインターネットから誰でも触れるので、必ず複雑なパスワードを設定してください。
- DATABASE_NAME:FireStoreのデータベース名を指定してください。
- GOOGLE_CLIENT_ID: GCPの[鍵と認証情報]でOauthを設定して入手したClientIDを指定してください。
- GOOGLE_CLIENT_SECRET:GCPの[鍵と認証情報]でOauthを設定して入手したClientSecretを指定してください。

## 注意
Google Cloud run上以外では動作確認しておりません。

## ライセンス
このプロジェクトはMITライセンスの下でライセンスされています。
