from flask import Blueprint, request, jsonify
import requests
import json
import os
from linebot import LineBotApi
from linebot.models import TextSendMessage, FlexSendMessage
from linebot.exceptions import LineBotApiError

maps = Blueprint('maps', __name__)

GOOGLE_API_KEY = os.environ.get('GOOGLE_API_KEY')
CHANNEL_ACCESS_TOKEN = os.getenv('CHANNEL_ACCESS_TOKEN')

def find_place_by_geo_info(latitude, longitude, keyword):
    places_api_url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
    parameters = {
        'keyword': keyword,
        'types': 'food',
        'language': 'ja',
        'location': f'{latitude},{longitude}',
        'radius': 1000,
        'key': GOOGLE_API_KEY
    }

    response = requests.get(places_api_url, params=parameters)
    data = response.json()
    return data

line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)  # ご自身のアクセストークンに置き換えてください

def maps_search(latitude, longitude, keyword, push_flex=False, user_id=None):
    data = find_place_by_geo_info(latitude, longitude, keyword)
    shop_info_texts = []
    map_urls = []
    flex_contents = []  # Flexメッセージの内容を格納するリスト

    for i, result in enumerate(data['results']):
        if i >= 4:
            break
        place_name = result['name']
        types = result['types']
        like = result.get('rating', 'N/A')
        user_ratings_total = result.get('user_ratings_total', 'N/A')
        price_level = result.get('price_level', 'N/A')
        vicinity = result['vicinity']
        map_url = f"https://www.google.com/maps/search/?api=1&query={result['geometry']['location']['lat']},{result['geometry']['location']['lng']}&query_place_id={result['place_id']}"
        shop_info_text = f"場所名: {place_name}\nタイプ: {types}\n評価: {like}\nレビュー数: {user_ratings_total}\n価格レベル: {price_level}\n住所: {vicinity}\nURL: {map_url} "
        shop_info_texts.append(shop_info_text)

        if push_flex and i < 10:
            flex_contents.append({
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": shop_info_text,
                        "wrap": True,
                        "weight": "bold",
                        "size": "lg"
                    },
                    {
                        "type": "button",
                        "style": "link",
                        "height": "sm",
                        "action": {
                            "type": "uri",
                            "label": "Google Mapで開く",
                            "uri": map_url
                        }
                    }
                ]
            })

        if i < 3:
            map_urls.append(map_url)

    user_message = f"下記の一覧は場所とキーワード「{keyword}」を条件に場所を検索を行って返ってきた情報です。おすすめの場所を教えて。\n" + '\n'.join(shop_info_texts)
    links = "\n❗参考\n" + '\n'.join(map_urls)

    if push_flex and user_id:
        flex_message = FlexSendMessage(
            alt_text="検索結果",
            contents={
                "type": "carousel",
                "contents": flex_contents
            }
        )
        try:
            line_bot_api.push_message(user_id, flex_message)
        except LineBotApiError as e:
            print(f"Error occurred: {e}")

    return {'message': user_message, 'links': links}
