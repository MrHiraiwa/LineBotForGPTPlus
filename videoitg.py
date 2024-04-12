from flask import Blueprint
import requests
import base64
import os

from linebot import LineBotApi

video = Blueprint('video', __name__)

GOOGLE_API_KEY = os.environ.get('GOOGLE_API_KEY')  # API key should be stored in environment variables

def analyze_video(video_bytes):
    api_url = f"https://videointelligence.googleapis.com/v1/videos:annotate?key={GOOGLE_API_KEY}"
    base64_video = base64.b64encode(video_bytes).decode("utf-8")

    request_body = {
        "inputContent": base64_video,
        "features": [
            "LABEL_DETECTION",
            "SHOT_CHANGE_DETECTION",
            "OBJECT_TRACKING"
        ],
        # Additional configuration can be added here if necessary
    }

    response = requests.post(api_url, json=request_body)
    return response.json()

def video_results_to_string(video_results):
    result_string = ""
    # Extract and format results
    # Customize this function based on the specific features enabled and the structure of the API response
    annotations = video_results.get('annotationResults', [{}])[0]
    segment_labels = annotations.get('segmentLabelAnnotations', [])
    for label in segment_labels:
        result_string += f"Label: {label['entity']['description']}, Confidence: {label['confidence']}\n"
        # Include additional details such as segments, frames, etc.

    return result_string

def video_api(message_id, CHANNEL_ACCESS_TOKEN):
    line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)
    message_content = line_bot_api.get_message_content(message_id)
    
    video = message_content.content
    video_results = analyze_video(video)
    video_results = video_results_to_string(video_results)

    return video_results
