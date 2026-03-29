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
            <h1>🎨 Astax — IA Générative</h1>
            
            <input type="text" id="prompt" placeholder="Décris ton image en anglais...">
            
            <div class="upload-box" onclick="document.getElementById('fileInput').click()">
                🖼️ Clique ici pour ajouter une image de référence (optionnel)
                <input type="file" id="fileInput" accept="image/*" onchange="previewImage(event)">
                <img id="preview">
            </div>
            
            <div id="description"></div>
            
            <button onclick="generer()">✨ Générer</button>
            
            <div id="status"></div>
            <img id="result">
        </div>
        
        <script>
        let imageBase64 = null;
        
        function previewImage(event) {
            const file = event.target.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = function(e) {
                    document.getElementById('preview').src = e.target.result;
                    document.getElementById('preview').style.display = 'block';
                    imageBase64 = e.target.result.split(',')[1];
                }
                reader.readAsDataURL(file);
            }
        }
        
        async function generer() {
            const prompt = document.getElementById("prompt").value;
            
            document.getElementById("status").innerText = "⏳ Génération en cours... (30-60 sec)";
            document.getElementById("result").style.display = "none";
            document.getElementById("description").style.display = "none";
            
            const formData = new FormData();
            formData.append("prompt", prompt);
            if (imageBase64) {
                formData.append("image_base64", imageBase64);
            }
            
            const response = await fetch("/generate", {
                method: "POST",
                body: formData
            });
            
            if (response.ok) {
                const blob = await response.blob();
                document.getElementById("result").src = URL.createObjectURL(blob);
                document.getElementById("result").style.display = "block";
                document.getElementById("status").innerText = "✅ Image générée !";
            } else {
                document.getElementById("status").innerText = "❌ Erreur, réessaie !";
            }
        }
        </script>
    </body>
    </html>
    """

@app.route("/generate", methods=["POST"])
def generate():
    prompt = request.form.get("prompt", "a beautiful landscape")
    image_base64 = request.form.get("image_base64")
    
    final_prompt = prompt
    
    if image_base64:
        # Analyse l'image et génère une description
        image_bytes = base64.b64decode(image_base64)
        description = analyser_image(image_bytes)
        # Combine la description avec le prompt
        final_prompt = f"{prompt}, inspired by: {description}"
        print(f"Description générée: {description}")
        print(f"Prompt final: {final_prompt}")
    
    result = client.text_to_image(
        final_prompt,
        model="stabilityai/stable-diffusion-xl-base-1.0"
    )
    
    img_io = io.BytesIO()
    result.save(img_io, format="PNG")
    img_io.seek(0)
    return send_file(img_io, mimetype="image/png")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=7860)
