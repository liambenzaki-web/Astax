import os
import io
from flask import Flask, request, send_file, jsonify
from huggingface_hub import InferenceClient
from groq import Groq

app = Flask(__name__)

HF_TOKEN = os.environ.get("HF_TOKEN")
GROQ_KEY = os.environ.get("GROQ_API_KEY")

hf_client = InferenceClient(
    provider="hf-inference",
    api_key=HF_TOKEN
)
groq_client = Groq(api_key=GROQ_KEY)

@app.route("/")
def home():
    return """
    <html>
    <head>
        <title>Astax</title>
        <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Rajdhani:wght@300;400;600&display=swap" rel="stylesheet">
        <style>
            * { box-sizing: border-box; margin: 0; padding: 0; }
            
            body {
                background: #050510;
                color: white;
                font-family: 'Rajdhani', sans-serif;
                height: 100vh;
                display: flex;
                flex-direction: column;
                overflow: hidden;
            }

            /* Fond animé avec particules */
            .bg-animation {
                position: fixed;
                top: 0; left: 0;
                width: 100%; height: 100%;
                z-index: 0;
                background: 
                    radial-gradient(ellipse at 20% 50%, rgba(120, 40, 200, 0.15) 0%, transparent 50%),
                    radial-gradient(ellipse at 80% 50%, rgba(0, 200, 255, 0.1) 0%, transparent 50%);
            }

            .grid-bg {
                position: fixed;
                top: 0; left: 0;
                width: 100%; height: 100%;
                z-index: 0;
                background-image: 
                    linear-gradient(rgba(0, 200, 255, 0.03) 1px, transparent 1px),
                    linear-gradient(90deg, rgba(0, 200, 255, 0.03) 1px, transparent 1px);
                background-size: 50px 50px;
                animation: gridMove 20s linear infinite;
            }

            @keyframes gridMove {
                0% { transform: translateY(0); }
                100% { transform: translateY(50px); }
            }

            /* Header */
            .header {
                position: relative;
                z-index: 10;
                text-align: center;
                padding: 20px;
                border-bottom: 1px solid rgba(0, 200, 255, 0.2);
                background: rgba(5, 5, 16, 0.8);
                backdrop-filter: blur(10px);
            }

            .logo {
                font-family: 'Orbitron', monospace;
                font-size: 2.5em;
                font-weight: 900;
                background: linear-gradient(135deg, #00c8ff, #a855f7, #ff6b35);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
                letter-spacing: 8px;
                text-shadow: none;
                animation: logoPulse 3s ease-in-out infinite;
            }

            @keyframes logoPulse {
                0%, 100% { filter: brightness(1); }
                50% { filter: brightness(1.3); }
            }

            .tagline {
                font-family: 'Rajdhani', sans-serif;
                color: rgba(0, 200, 255, 0.6);
                font-size: 0.85em;
                letter-spacing: 4px;
                margin-top: 5px;
            }

            /* Chat container */
            .chat-container {
                position: relative;
                z-index: 10;
                flex: 1;
                overflow-y: auto;
                padding: 20px;
                max-width: 800px;
                margin: 0 auto;
                width: 100%;
            }

            .chat-container::-webkit-scrollbar { width: 4px; }
            .chat-container::-webkit-scrollbar-track { background: transparent; }
            .chat-container::-webkit-scrollbar-thumb { background: rgba(0, 200, 255, 0.3); border-radius: 2px; }

            .messages { display: flex; flex-direction: column; gap: 12px; }

            .message {
                padding: 12px 18px;
                border-radius: 4px;
                max-width: 80%;
                line-height: 1.6;
                font-size: 1em;
                animation: fadeIn 0.3s ease;
            }

            @keyframes fadeIn {
                from { opacity: 0; transform: translateY(10px); }
                to { opacity: 1; transform: translateY(0); }
            }

            .bot {
                background: rgba(0, 200, 255, 0.05);
                border: 1px solid rgba(0, 200, 255, 0.2);
                border-left: 3px solid #00c8ff;
                color: #e0f7ff;
                align-self: flex-start;
                border-radius: 0 8px 8px 0;
            }

            .user {
                background: rgba(168, 85, 247, 0.1);
                border: 1px solid rgba(168, 85, 247, 0.3);
                border-right: 3px solid #a855f7;
                color: #f0e0ff;
                align-self: flex-end;
                border-radius: 8px 0 0 8px;
            }

            /* Barre de progression */
            .progress-container {
                display: none;
                margin: 20px 0;
                text-align: center;
            }

            .progress-text {
                font-family: 'Orbitron', monospace;
                font-size: 0.8em;
                color: #00c8ff;
                letter-spacing: 3px;
                margin-bottom: 10px;
                animation: blink 1s ease-in-out infinite;
            }

            @keyframes blink {
                0%, 100% { opacity: 1; }
                50% { opacity: 0.4; }
            }

            .progress-bar {
                width: 100%;
                height: 4px;
                background: rgba(0, 200, 255, 0.1);
                border-radius: 2px;
                overflow: hidden;
            }

            .progress-fill {
                height: 100%;
                background: linear-gradient(90deg, #00c8ff, #a855f7, #ff6b35);
                border-radius: 2px;
                animation: progressAnim 2s ease-in-out infinite;
            }

            @keyframes progressAnim {
                0% { width: 0%; margin-left: 0; }
                50% { width: 100%; margin-left: 0; }
                100% { width: 0%; margin-left: 100%; }
            }

            /* Image générée */
            #generatedImage {
                max-width: 100%;
                border-radius: 8px;
                margin: 20px auto;
                display: none;
                border: 1px solid rgba(0, 200, 255, 0.3);
                box-shadow: 0 0 30px rgba(0, 200, 255, 0.1);
            }

            /* Bouton téléchargement */
            .download-btn {
                display: block;
                margin: 10px auto;
                padding: 10px 24px;
                background: transparent;
                border: 1px solid rgba(0, 200, 255, 0.4);
                color: #00c8ff;
                border-radius: 4px;
                text-decoration: none;
                font-family: 'Orbitron', monospace;
                font-size: 0.75em;
                letter-spacing: 2px;
                width: fit-content;
                transition: all 0.3s ease;
            }

            .download-btn:hover {
                background: rgba(0, 200, 255, 0.1);
                box-shadow: 0 0 15px rgba(0, 200, 255, 0.3);
            }

            /* Zone de saisie */
            .input-area {
                position: relative;
                z-index: 10;
                padding: 20px;
                background: rgba(5, 5, 16, 0.9);
                border-top: 1px solid rgba(0, 200, 255, 0.15);
                backdrop-filter: blur(10px);
            }

            .input-row {
                display: flex;
                gap: 12px;
                max-width: 800px;
                margin: 0 auto;
            }

            input[type=text] {
                flex: 1;
                padding: 14px 18px;
                font-size: 1em;
                font-family: 'Rajdhani', sans-serif;
                border-radius: 4px;
                border: 1px solid rgba(0, 200, 255, 0.2);
                background: rgba(0, 200, 255, 0.03);
                color: white;
                outline: none;
                transition: all 0.3s ease;
                letter-spacing: 1px;
            }

            input[type=text]:focus {
                border-color: rgba(0, 200, 255, 0.6);
                box-shadow: 0 0 15px rgba(0, 200, 255, 0.1);
                background: rgba(0, 200, 255, 0.05);
            }

            input[type=text]::placeholder { color: rgba(255,255,255,0.25); }

            /* Bouton envoyer */
            .send-btn {
                padding: 14px 28px;
                background: linear-gradient(135deg, rgba(0, 200, 255, 0.15), rgba(168, 85, 247, 0.15));
                border: 1px solid rgba(0, 200, 255, 0.4);
                border-radius: 4px;
                color: #00c8ff;
                font-family: 'Orbitron', monospace;
                font-size: 0.8em;
                letter-spacing: 2px;
                cursor: pointer;
                transition: all 0.3s ease;
                position: relative;
                overflow: hidden;
            }

            .send-btn:hover {
                background: linear-gradient(135deg, rgba(0, 200, 255, 0.25), rgba(168, 85, 247, 0.25));
                box-shadow: 0 0 20px rgba(0, 200, 255, 0.3);
                transform: translateY(-1px);
            }

            .send-btn:active {
                transform: translateY(1px);
            }

            .send-btn::after {
                content: '';
                position: absolute;
                top: 50%; left: 50%;
                width: 0; height: 0;
                background: rgba(0, 200, 255, 0.3);
                border-radius: 50%;
                transform: translate(-50%, -50%);
                transition: width 0.6s, height 0.6s, opacity 0.6s;
                opacity: 0;
            }

            .send-btn:active::after {
                width: 200px; height: 200px;
                opacity: 0;
            }
        </style>
    </head>
    <body>
        <div class="bg-animation"></div>
        <div class="grid-bg"></div>

        <div class="header">
            <div class="logo">⬡ ASTAX</div>
            <div class="tagline">GENERATIVE IMAGE AI</div>
        </div>
        
        <div class="chat-container">
            <div class="messages" id="messages"></div>
            <div class="progress-container" id="progressContainer">
                <div class="progress-text">⬡ GÉNÉRATION EN COURS</div>
                <div class="progress-bar"><div class="progress-fill"></div></div>
            </div>
            <img id="generatedImage">
        </div>
        
        <div class="input-area">
            <div class="input-row">
                <input type="text" id="userInput" placeholder="Décris ce que tu veux créer..." onkeypress="if(event.key==='Enter') envoyer()">
                <button class="send-btn" onclick="envoyer()">ENVOYER</button>
            </div>
        </div>
        
        <script>
        let conversation = [];
        
        window.onload = function() {
            ajouterMessage("bot", "Bonjour ! 👋 Je suis ton assistant créatif Astax. Dis-moi ce que tu veux créer comme image, et je vais te poser quelques questions pour obtenir le meilleur résultat possible !");
        }
        
        function ajouterMessage(role, text) {
            const messages = document.getElementById("messages");
            const div = document.createElement("div");
            div.className = "message " + role;
            div.innerText = text;
            messages.appendChild(div);
            messages.scrollTop = messages.scrollHeight;
        }
        
        async function envoyer() {
            const input = document.getElementById("userInput");
            const text = input.value.trim();
            if (!text) return;
            
            ajouterMessage("user", text);
            conversation.push({"role": "user", "content": text});
            input.value = "";
            
            const response = await fetch("/chat", {
                method: "POST",
                headers: {"Content-Type": "application/json"},
                body: JSON.stringify({messages: conversation})
            });
            
            const data = await response.json();
            
            if (data.type === "question") {
                ajouterMessage("bot", data.message);
                conversation.push({"role": "assistant", "content": data.message});
            } else if (data.type === "generate") {
                ajouterMessage("bot", data.message);
                conversation.push({"role": "assistant", "content": data.message});
                
                document.getElementById("progressContainer").style.display = "block";
                document.getElementById("generatedImage").style.display = "none";
                
                const imgResponse = await fetch("/generate", {
                    method: "POST",
                    headers: {"Content-Type": "application/json"},
                    body: JSON.stringify({prompt: data.prompt})
                });
                
                if (imgResponse.ok) {
                    const blob = await imgResponse.blob();
                    const imgUrl = URL.createObjectURL(blob);
                    document.getElementById("generatedImage").src = imgUrl;
                    document.getElementById("generatedImage").style.display = "block";

                    const oldBtn = document.getElementById("downloadBtn");
                    if (oldBtn) oldBtn.remove();
                    const downloadBtn = document.createElement("a");
                    downloadBtn.id = "downloadBtn";
                    downloadBtn.href = imgUrl;
                    downloadBtn.download = "astax-image.png";
                    downloadBtn.innerText = "⬇ TÉLÉCHARGER L'IMAGE";
                    downloadBtn.className = "download-btn";
                    document.getElementById("messages").appendChild(downloadBtn);
                }
                document.getElementById("progressContainer").style.display = "none";
                conversation = [];
            }
        }
        </script>
    </body>
    </html>
    """

@app.route("/chat", methods=["POST"])
def chat():
    data = request.json
    messages = data.get("messages", [])
    
    system = """Tu es un assistant créatif qui aide les utilisateurs à créer des images avec une IA.

Ton rôle est de poser des questions précises pour affiner leur idée, puis générer un prompt en anglais pour l'IA.

Règles :
- Pose UNE seule question à la fois en français
- Maximum 3-4 questions avant de générer
- Quand tu as assez d'informations, réponds avec ce format exact sur deux lignes séparées:
  GENERATE: [prompt en anglais très détaillé]
  MESSAGE: [message sympa en français pour annoncer la génération]"""

    response = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        max_tokens=500,
        messages=[{"role": "system", "content": system}] + messages
    )
    
    text = response.choices[0].message.content
    
    if "GENERATE:" in text:
        lines = text.split("\n")
        prompt = ""
        message = "Parfait, je génère ton image ! ✨"
        for line in lines:
            if line.startswith("GENERATE:"):
                prompt = line.replace("GENERATE:", "").strip()
            elif line.startswith("MESSAGE:"):
                message = line.replace("MESSAGE:", "").strip()
        return jsonify({"type": "generate", "prompt": prompt, "message": message})
    else:
        return jsonify({"type": "question", "message": text})

@app.route("/generate", methods=["POST"])
def generate():
    data = request.json
    prompt = data.get("prompt", "a beautiful landscape")
    
    result = hf_client.text_to_image(
        prompt,
        model="stabilityai/stable-diffusion-xl-base-1.0"
    )
    
    img_io = io.BytesIO()
    result.save(img_io, format="PNG")
    img_io.seek(0)
    return send_file(img_io, mimetype="image/png")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=7860)
