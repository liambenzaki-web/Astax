import os
import io
import base64
from flask import Flask, request, send_file, jsonify
from huggingface_hub import InferenceClient
from PIL import Image

app = Flask(__name__)

API_TOKEN = os.environ.get("HF_TOKEN")
client = InferenceClient(
    provider="hf-inference",
    api_key=API_TOKEN
)

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
            label.upload-label { cursor:pointer; color:#aaa; }
            #preview { max-width:300px; border-radius:8px; margin:10px auto; display:none; }
            .slider-container { margin:15px 0; text-align:left; padding:0 5%; }
            input[type=range] { width:100%; }
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
                <label class="upload-label">
                    🖼️ Clique ici pour ajouter une image de référence (optionnel)
                </label>
                <input type="file" id="fileInput" accept="image/*" onchange="previewImage(event)">
                <img id="preview">
            </div>
            
            <div class="slider-container">
                <label>Force de référence : <span id="strengthValue">50</span>%</label>
                <input type="range" id="strength" min="0" max="100" value="50" 
                       oninput="document.getElementById('strengthValue').innerText=this.value">
            </div>
            
            <button onclick="generer()">✨ Générer</button>
            
            <div id="status"></div>
            <img id="result">
        </div>
        
        <script>
        function previewImage(event) {
            const file = event.target.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = function(e) {
                    const preview = document.getElementById('preview');
                    preview.src = e.target.result;
                    preview.style.display = 'block';
                }
                reader.readAsDataURL(file);
            }
        }
        
        async function generer() {
            const prompt = document.getElementById("prompt").value;
            const fileInput = document.getElementById("fileInput");
            const strength = document.getElementById("strength").value / 100;
            
            document.getElementById("status").innerText = "⏳ Génération en cours... (30-60 sec)";
            document.getElementById("result").style.display = "none";
            
            const formData = new FormData();
            formData.append("prompt", prompt);
            formData.append("strength", strength);
            
            if (fileInput.files[0]) {
                formData.append("image", fileInput.files[0]);
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
    strength = float(request.form.get("strength", 0.5))
    image_file = request.files.get("image")
    
    if image_file:
        # Mode img2img — avec image de référence
        image = Image.open(image_file).convert("RGB").resize((1024, 1024))
        img_bytes = io.BytesIO()
        image.save(img_bytes, format="PNG")
        img_bytes.seek(0)
        
        result = client.image_to_image(
           image=img_bytes.read(),
            prompt=prompt,
            strength=strength,
            model="stabilityai/stable-diffusion-xl-base-1.0"
        )
    else:
        # Mode text-to-image — sans image de référence
        result = client.text_to_image(
            prompt,
            model="stabilityai/stable-diffusion-xl-base-1.0"
        )
    
    img_io = io.BytesIO()
    result.save(img_io, format="PNG")
    img_io.seek(0)
    return send_file(img_io, mimetype="image/png")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=7860)
