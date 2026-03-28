import gradio as gr
import requests
import os
from PIL import Image
import io
import time

API_TOKEN = os.environ.get("HF_TOKEN")
API_URL = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0"

headers = {"Authorization": f"Bearer {API_TOKEN}"}

def generer_image(prompt, guidance_scale):
    payload = {
        "inputs": prompt,
        "parameters": {
            "guidance_scale": guidance_scale
        }
    }
    
    # On réessaie jusqu'à 3 fois si le modèle est en chargement
    for i in range(3):
        response = requests.post(API_URL, headers=headers, json=payload)
        
        # Si la réponse est une image valide
        try:
            image = Image.open(io.BytesIO(response.content))
            return image
        except:
            # Le modèle est en train de se charger, on attend
            if i < 2:
                time.sleep(20)
            else:
                return None

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
