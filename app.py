import gradio as gr
import requests
import os
from PIL import Image
import io

API_TOKEN = os.environ.get("HF_TOKEN")
API_URL = "https://api-inference.huggingface.co/models/runwayml/stable-diffusion-v1-5"
headers = {"Authorization": f"Bearer {API_TOKEN}"}

def generer_image(prompt):
    response = requests.post(API_URL, headers=headers, json={"inputs": prompt})
    return Image.open(io.BytesIO(response.content))

app = gr.Interface(
    fn=generer_image,
    inputs=gr.Textbox(placeholder="a dragon flying over a castle..."),
    outputs=gr.Image(),
    title="🎨 Astax",
)

app.launch(server_name="0.0.0.0", server_port=7860)
