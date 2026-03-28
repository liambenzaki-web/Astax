import gradio as gr
import requests
import os
from PIL import Image
import io
import time
import json

API_TOKEN = os.environ.get("HF_TOKEN")
API_URL = "https://api-inference.huggingface.co/models/stabilityai/sdxl-turbo"

headers = {"Authorization": f"Bearer {API_TOKEN}"}

def generer_image(prompt, guidance_scale):
    payload = {
        "inputs": prompt,
        "parameters": {
            "guidance_scale": guidance_scale
        }
    }
    
    for i in range(5):
        response = requests.post(API_URL, headers=headers, json=payload)
        
        # Vérifie si c'est une image
        if response.headers.get("content-type", "").startswith("image"):
            image = Image.open(io.BytesIO(response.content))
            return image
        
        # Sinon on affiche l'erreur et on attend
        try:
            error = response.json()
            print(f"Tentative {i+1}: {error}")
            if "estimated_time" in error:
                wait_time = min(error["estimated_time"], 30)
                time.sleep(wait_time)
            else:
                time.sleep(10)
        except:
            time.sleep(10)
    
    raise gr.Error("Le modèle n'est pas disponible, réessaie dans quelques minutes.")

with gr.Blocks(title="Astax") as app:
    
    gr.Markdown("# 🎨 Astax — IA Générative d'Images")
    gr.Markdown("Décris une image en anglais et laisse l'IA créer !")
    
    with gr.Row():
        with gr.Column():
            prompt = gr.Textbox(
                label="Ton prompt",
                placeholder="a dragon flying over a medieval castle...",
                lines=3
            )
            guidance = gr.Slider(
                minimum=1, maximum=20, value=7.5, step=0.5,
                label="Créativité (7-8 recommandé)"
            )
            bouton = gr.Button("✨ Générer", variant="primary")
        
        with gr.Column():
            image_sortie = gr.Image(label="Image générée")
    
    bouton.click(
        fn=generer_image,
        inputs=[prompt, guidance],
        outputs=image_sortie
    )

app.launch(server_name="0.0.0.0", server_port=7860)
