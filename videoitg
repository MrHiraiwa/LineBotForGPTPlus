import requests
import base64
import os

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
    }

    response = requests.post(api_url, json=request_body)
    return response.json()

def video_results_to_string(video_results):
    result_string = ""
    annotations = video_results.get('annotationResults', [{}])[0]
    segment_labels = annotations.get('segmentLabelAnnotations', [])
    for label in segment_labels:
        result_string += f"Label: {label['entity']['description']}, Confidence: {label['confidence']}\n"
    return result_string

def process_video_from_file(file_path):
    with open(file_path, 'rb') as video_file:
        video_bytes = video_file.read()
    analysis_results = analyze_video(video_bytes)
    return video_results_to_string(analysis_results)

# 例: 他のスクリプトからこの関数を呼び出す
# results = process_video_from_file('path_to_your_video_file.mp4')
# print(results)
