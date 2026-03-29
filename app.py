import os
import io
import base64
from flask import Flask, request, send_file
from huggingface_hub import InferenceClient
from PIL import Image

app = Flask(__name__)

API_TOKEN = os.environ.get("HF_TOKEN")
client = InferenceClient(
    provider="hf-inference",
    api_key=API_TOKEN
)

def analyser_image(image_bytes):
    """Analyse l'image et retourne une description textuelle"""
    result = client.image_to_text(
        image=image_bytes,
        model="Salesforce/blip-image-captioning-large"
    )
    return result

@app.route("/")
def home():
    return """
    <html>
    <head>
        <title>Astax</title>
        <style>
            body { background:#111; color:white; font-family:sans-serif; text-align:center; padding:50px; margin:0; }
            h1 { font-size:2em; margin-bottom:10px; }
            .container { max-width:700px; margin:0 auto; }
            input[type=text] { width:90%; padding:12px; font-size:16px; border-radius:8px; border:none; margin-bottom:15px; }
            .upload-box { border:2px dashed #555; border-radius:12px; padding:20px; margin-bottom:15px; cursor:pointer; }
            .upload-box:hover { border-color:orange; }
            input[type=file] { display:none; }
            #preview { max-width:300px; border-radius:8px; margin:10px auto; display:none; }
            #description { color:#aaa; font-style:italic; margin:10px 0; display:none; }
            button { padding:12px 40px; background:orange; border:none; border-radius:8px; font-size:16px; cursor:pointer; font-weight:bold; }
            button:hover { background:#ff9900; }
            #status { margin:15px 0; font-size:16px; }
            #result { max-width:600px; border-radius:12px; display:none; margin:20px auto; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🎨 Astax —
