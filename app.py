import os
import io
from flask import Flask, request, send_file, jsonify
from huggingface_hub import InferenceClient
import anthropic

app = Flask(__name__)

HF_TOKEN = os.environ.get("HF_TOKEN")
ANTHROPIC_KEY = os.environ.get("ANTHROPIC_KEY")

hf_client = InferenceClient(
    provider="hf-inference",
    api_key=HF_TOKEN
)
anthropic_client = anthropic.Anthropic(api_key=ANTHROPIC_KEY)

@app.route("/")
def home():
    return """
    <html>
    <head>
        <title>Astax</title>
        <style>
            * { box-sizing: border-box; margin: 0; padding: 0; }
            body { background:#111; color:white; font-family:sans-serif; height:100vh; display:flex; flex-direction:column; }
            h1 { text-align:center; padding:20px; font-size:1.8em; }
            .chat-container { flex:1; overflow-y:auto; padding:20px; max-width:800px; margin:0 auto; width:100%; }
            .message { margin:10px 0; padding:12px 16px; border-radius:12px; max-width:80%; line-height:1.5; }
            .bot { background:#222; align-self:flex-start; border-radius:12px 12px 12px 0; }
            .user { background:orange; color:black; align-self:flex-end; margin-left:auto; border-radius:12px 12px 0 12px; }
            .messages { display:flex; flex-direction:column; }
            .input-area { padding:20px; background:#1a1a1a; border-top:1px solid #333; }
            .input-row { display:flex; gap:10px; max-width:800px; margin:0 auto; }
            input[type=text] { flex:1; padding:12px; font-size:16px; border-radius:8px; border:none; background:#333; color:white; }
            button { padding:12px 24px; background:orange; border:none; border-radius:8px; font-size:16px; cursor:pointer; font-weight:bold; }
            button:hover { background:#ff9900; }
            .generating { text-align:center; padding:20px; color:#aaa; display:none; }
            #generatedImage { max-width:100%; border-radius:12px; margin:20px auto; display:none; }
        </style>
    </head>
    <body>
        <h1>🎨 Astax — IA Générative</h1>
        
        <div class="chat-container">
            <div class="messages" id="messages"></div>
            <div class="generating" id="generating">⏳ Génération de l'image en cours...</div>
            <img id="generatedImage">
        </div>
        
        <div class="input-area">
            <div class="input-row">
                <input type="text" id="userInput" placeholder="Décris ce que tu veux créer..." onkeypress="if(event.key==='Enter') envoyer()">
                <button onclick="envoyer()">Envoyer</button>
            </div>
        </div>
        
        <script>
        let conversation = [];
        
        // Message de bienvenue
        window.onload = function() {
            ajouterMessage("bot", "Bonjour ! 👋 Je suis ton assistant créatif. Dis-moi ce que tu veux créer comme image, et je vais te poser quelques questions pour obtenir le meilleur résultat possible !");
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
                
                document.getElementById("generating").style.display = "block";
                document.getElementById("generatedImage").style.display = "none";
                
                const imgResponse = await fetch("/generate", {
                    method: "POST",
                    headers: {"Content-Type": "application/json"},
                    body: JSON.stringify({prompt: data.prompt})
                });
                
                if (imgResponse.ok) {
                    const blob = await imgResponse.blob();
                    document.getElementById("generatedImage").src = URL.createObjectURL(blob);
                    document.getElementById("generatedImage").style.display = "block";
                }
                document.getElementById("generating").style.display = "none";
                
                // Reset conversation pour une nouvelle image
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
- Pose UNE seule question à la fois
- Maximum 3-4 questions avant de générer
- Quand tu as assez d'informations, réponds avec ce format exact:
  GENERATE: [prompt en anglais très détaillé]
  MESSAGE: [message sympa en français pour annoncer la génération]

Exemples de questions à poser:
- Quel style ? (réaliste, anime, peinture, cyberpunk...)
- Quelle ambiance ? (jour, nuit, sombre, joyeux...)
- Des personnages ? Des détails particuliers ?
- Quelle époque ? (futuriste, médiéval, moderne...)"""

    response = anthropic_client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=500,
        system=system,
        messages=messages
    )
    
    text = response.content[0].text
    
    if "GENERATE:" in text:
        lines = text.split("\n")
        prompt = ""
        message = ""
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

