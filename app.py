import os
import io
import requests
from flask import Flask, request, jsonify, send_file
from PIL import Image

app = Flask(__name__)

API_TOKEN = os.environ.get("HF_TOKEN")
API_URL = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-2"
headers = {"Authorization": f"Bearer {API_TOKEN}"}

@app.route("/")
def home():
    return """
    <html>
    <head><title>Astax</title></head>
    <body style="background:#111;color:white;font-family:sans-serif;text-align:center;padding:50px">
        <h1>🎨 Astax — IA Générative</h1>
        <input id="prompt" placeholder="Décris ton image en anglais..." 
               style="width:400px;padding:10px;font-size:16px;border-radius:8px;border:none">
        <br><br>
        <button onclick="generer()" 
                style="padding:12px 30px;background:orange;border:none;border-radius:8px;font-size:16px;cursor:pointer">
            ✨ Générer
        </button>
        <br><br>
        <div id="status"></div>
        <br>
        <img id="result" style="max-width:600px;border-radius:12px;display:none">
        <script>
        async function generer() {
            const prompt = document.getElementById("prompt").value;
            document.getElementById("status").innerText = "⏳ Génération en cours...";
            document.getElementById("result").style.display = "none";
            const response = await fetch("/generate?prompt=" + encodeURIComponent(prompt));
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

@app.route("/generate")
def generate():
    prompt = request.args.get("prompt", "a beautiful landscape")
    response = requests.post(API_URL, headers=headers, json={"inputs": prompt})
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text[:500]}")
    if response.status_code == 200:
        return send_file(io.BytesIO(response.content), mimetype="image/png")
    return jsonify({"error": response.text}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=7860)
