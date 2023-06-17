from flask import Blueprint, request, redirect, jsonify
import requests
import base64
import os

vision = Blueprint('vision', __name__)

GOOGLE_API_KEY = os.environ.get('GOOGLE_API_KEY')  # API key should be stored in environment variables

def analyze_image(image_bytes):
    api_url = "https://vision.googleapis.com/v1/images:annotate?key=" + GOOGLE_API_KEY
    base64_image = base64.b64encode(image_bytes).decode("utf-8")

    request_body = {
        "requests": [
            {
                "image": {
                    "content": base64_image
                },
                "features": [
                    { "type": "LABEL_DETECTION" },
                    { "type": "TEXT_DETECTION" },
                    { "type": "LANDMARK_DETECTION" },
                    { "type": "FACE_DETECTION" },
                    { "type": "OBJECT_LOCALIZATION" },
                    { "type": "DOCUMENT_TEXT_DETECTION" }
                ]
            }
        ]
    }

    response = requests.post(api_url, json=request_body)
    return response.json()

def vision_results_to_string(vision_results):
    result_string = ""
    result = vision_results['responses'][0]
    label_annotations = result.get('labelAnnotations', [])
    text_annotations = result.get('textAnnotations', [])
    landmark_annotations = result.get('landmarkAnnotations', [])
    face_annotations = result.get('faceAnnotations', [])
    object_annotations = result.get('localizedObjectAnnotations', [])  
    result_string += "Labels: " + ', '.join([ann['description'] for ann in label_annotations]) if label_annotations else "None"
    result_string += "\nText: " + ', '.join([ann['description'] for ann in text_annotations]) if text_annotations else "None"
    result_string += "\nLandmarks: " + ', '.join([ann['description'] for ann in landmark_annotations]) if landmark_annotations else "None"
    result_string += "\nFaces: " + str(len(face_annotations))
    result_string += "\nObjects: " + ', '.join([ann['name'] for ann in object_annotations]) if object_annotations else "None"
    return result_string

import requests

def get_image(image_url, line_access_token):
    headers = {
        "Content-Type": "application/json; charset=UTF-8",
        "Authorization": f"Bearer {line_access_token}",
    }
    response = requests.get(image_url, headers=headers)
    return response.content
