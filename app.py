import os
import io
import json
import uuid
import hashlib
from flask import Flask, request, send_file, jsonify, session
from huggingface_hub import InferenceClient
from groq import Groq

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "astax-secret-2026")

HF_TOKEN = os.environ.get("HF_TOKEN")
GROQ_KEY = os.environ.get("GROQ_API_KEY")

hf_client = InferenceClient(provider="hf-inference", api_key=HF_TOKEN)
groq_client = Groq(api_key=GROQ_KEY)

# Stockage en mémoire
users = {}       # {username: {password_hash, galleries, prompt_history}}
galleries = {}   # Pour les utilisateurs non connectés (session)

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def get_user_data():
    username = session.get("username")
    if username and username in users:
        return users[username]
    return None

@app.route("/")
def home():
    return """
<!DOCTYPE html>
<html>
<head>
    <title>Astax</title>
    <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Rajdhani:wght@300;400;600&display=swap" rel="stylesheet">
    <style>
        * { box-sizing:border-box; margin:0; padding:0; }
        body { background:#050510; color:white; font-family:'Rajdhani',sans-serif; height:100vh; display:flex; flex-direction:column; overflow:hidden; }
        .bg-animation { position:fixed; top:0; left:0; width:100%; height:100%; z-index:0; background:radial-gradient(ellipse at 20% 50%, rgba(120,40,200,0.15) 0%, transparent 50%), radial-gradient(ellipse at 80% 50%, rgba(0,200,255,0.1) 0%, transparent 50%); }
        .grid-bg { position:fixed; top:0; left:0; width:100%; height:100%; z-index:0; background-image:linear-gradient(rgba(0,200,255,0.03) 1px, transparent 1px), linear-gradient(90deg, rgba(0,200,255,0.03) 1px, transparent 1px); background-size:50px 50px; animation:gridMove 20s linear infinite; }
        @keyframes gridMove { 0%{transform:translateY(0)} 100%{transform:translateY(50px)} }

        /* Header */
        .header { position:relative; z-index:10; text-align:center; padding:12px; border-bottom:1px solid rgba(0,200,255,0.2); background:rgba(5,5,16,0.8); backdrop-filter:blur(10px); display:flex; align-items:center; justify-content:space-between; padding:12px 20px; }
        .logo { font-family:'Orbitron',monospace; font-size:1.8em; font-weight:900; background:linear-gradient(135deg,#00c8ff,#a855f7,#ff6b35); -webkit-background-clip:text; -webkit-text-fill-color:transparent; background-clip:text; letter-spacing:8px; animation:logoPulse 3s ease-in-out infinite; }
        @keyframes logoPulse { 0%,100%{filter:brightness(1)} 50%{filter:brightness(1.3)} }
        .logo-sub { font-size:0.5em; color:rgba(0,200,255,0.6); letter-spacing:4px; display:block; }
        .user-area { display:flex; align-items:center; gap:10px; }
        .user-info { font-family:'Orbitron',monospace; font-size:0.65em; color:#00c8ff; letter-spacing:2px; }
        .header-btn { padding:8px 16px; background:transparent; border:1px solid rgba(0,200,255,0.3); border-radius:4px; color:rgba(0,200,255,0.7); font-family:'Orbitron',monospace; font-size:0.6em; letter-spacing:2px; cursor:pointer; transition:all 0.3s; }
        .header-btn:hover { background:rgba(0,200,255,0.1); }

        /* Nav */
        .nav { display:flex; justify-content:center; gap:20px; padding:8px; position:relative; z-index:10; background:rgba(5,5,16,0.6); border-bottom:1px solid rgba(0,200,255,0.1); }
        .nav-btn { padding:7px 18px; background:transparent; border:1px solid rgba(0,200,255,0.2); border-radius:4px; color:rgba(0,200,255,0.6); font-family:'Orbitron',monospace; font-size:0.6em; letter-spacing:2px; cursor:pointer; transition:all 0.3s; }
        .nav-btn.active, .nav-btn:hover { border-color:rgba(0,200,255,0.6); color:#00c8ff; background:rgba(0,200,255,0.05); box-shadow:0 0 10px rgba(0,200,255,0.2); }

        /* Pages */
        .page { display:none; flex:1; overflow:hidden; flex-direction:column; position:relative; z-index:10; }
        .page.active { display:flex; }

        /* Chat */
        .chat-container { flex:1; overflow-y:auto; padding:20px; max-width:800px; margin:0 auto; width:100%; }
        .chat-container::-webkit-scrollbar { width:4px; }
        .chat-container::-webkit-scrollbar-thumb { background:rgba(0,200,255,0.3); border-radius:2px; }
        .messages { display:flex; flex-direction:column; gap:12px; }
        .message { padding:12px 18px; border-radius:4px; max-width:80%; line-height:1.6; font-size:1em; animation:fadeIn 0.3s ease; }
        @keyframes fadeIn { from{opacity:0;transform:translateY(10px)} to{opacity:1;transform:translateY(0)} }
        .bot { background:rgba(0,200,255,0.05); border:1px solid rgba(0,200,255,0.2); border-left:3px solid #00c8ff; color:#e0f7ff; align-self:flex-start; border-radius:0 8px 8px 0; }
        .user { background:rgba(168,85,247,0.1); border:1px solid rgba(168,85,247,0.3); border-right:3px solid #a855f7; color:#f0e0ff; align-self:flex-end; border-radius:8px 0 0 8px; }

        /* Styles rapides */
        .styles-bar { display:flex; gap:8px; flex-wrap:wrap; padding:10px 20px; max-width:800px; margin:0 auto; width:100%; }
        .style-btn { padding:6px 14px; background:transparent; border:1px solid rgba(255,255,255,0.1); border-radius:20px; color:rgba(255,255,255,0.5); font-size:0.8em; cursor:pointer; transition:all 0.3s; }
        .style-btn:hover, .style-btn.selected { border-color:#a855f7; color:#a855f7; background:rgba(168,85,247,0.1); }

        /* Progress */
        .progress-container { display:none; margin:20px 0; text-align:center; }
        .progress-text { font-family:'Orbitron',monospace; font-size:0.8em; color:#00c8ff; letter-spacing:3px; margin-bottom:10px; animation:blink 1s ease-in-out infinite; }
        @keyframes blink { 0%,100%{opacity:1} 50%{opacity:0.4} }
        .progress-bar { width:100%; height:4px; background:rgba(0,200,255,0.1); border-radius:2px; overflow:hidden; }
        .progress-fill { height:100%; background:linear-gradient(90deg,#00c8ff,#a855f7,#ff6b35); animation:progressAnim 2s ease-in-out infinite; }
        @keyframes progressAnim { 0%{width:0%;margin-left:0} 50%{width:100%;margin-left:0} 100%{width:0%;margin-left:100%} }

        /* Input area */
        .input-area { padding:12px 15px; background:rgba(5,5,16,0.9); border-top:1px solid rgba(0,200,255,0.15); backdrop-filter:blur(10px); }
        .input-row { display:flex; gap:10px; max-width:800px; margin:0 auto 8px; }
        .negative-row { display:flex; gap:10px; max-width:800px; margin:0 auto; }
        input[type=text], input[type=password] { flex:1; padding:11px 16px; font-size:0.95em; font-family:'Rajdhani',sans-serif; border-radius:4px; border:1px solid rgba(0,200,255,0.2); background:rgba(0,200,255,0.03); color:white; outline:none; transition:all 0.3s; letter-spacing:1px; }
        input[type=text]:focus, input[type=password]:focus { border-color:rgba(0,200,255,0.6); box-shadow:0 0 15px rgba(0,200,255,0.1); }
        input[type=text]::placeholder, input[type=password]::placeholder { color:rgba(255,255,255,0.2); font-size:0.9em; }
        .negative-input { border-color:rgba(255,100,100,0.2) !important; }
        .negative-input:focus { border-color:rgba(255,100,100,0.5) !important; box-shadow:0 0 15px rgba(255,100,100,0.1) !important; }
        .send-btn { padding:11px 22px; background:linear-gradient(135deg,rgba(0,200,255,0.15),rgba(168,85,247,0.15)); border:1px solid rgba(0,200,255,0.4); border-radius:4px; color:#00c8ff; font-family:'Orbitron',monospace; font-size:0.7em; letter-spacing:2px; cursor:pointer; transition:all 0.3s; }
        .send-btn:hover { background:linear-gradient(135deg,rgba(0,200,255,0.25),rgba(168,85,247,0.25)); box-shadow:0 0 20px rgba(0,200,255,0.3); transform:translateY(-1px); }

        /* Galerie */
        .gallery-page { padding:20px; overflow-y:auto; flex:1; }
        .gallery-header { display:flex; justify-content:space-between; align-items:center; margin-bottom:20px; max-width:1000px; margin:0 auto 20px; }
        .gallery-title { font-family:'Orbitron',monospace; color:#00c8ff; letter-spacing:3px; }
        .create-folder-btn { padding:8px 18px; background:transparent; border:1px solid rgba(168,85,247,0.4); border-radius:4px; color:#a855f7; font-family:'Orbitron',monospace; font-size:0.6em; letter-spacing:2px; cursor:pointer; transition:all 0.3s; }
        .create-folder-btn:hover { background:rgba(168,85,247,0.1); }
        .folders-list { display:flex; flex-wrap:wrap; gap:12px; max-width:1000px; margin:0 auto 25px; }
        .folder-card { padding:12px 18px; background:rgba(0,200,255,0.03); border:1px solid rgba(0,200,255,0.15); border-radius:8px; cursor:pointer; transition:all 0.3s; min-width:130px; text-align:center; }
        .folder-card:hover { border-color:rgba(0,200,255,0.4); background:rgba(0,200,255,0.07); }
        .folder-card.active { border-color:#00c8ff; background:rgba(0,200,255,0.1); }
        .folder-icon { font-size:1.8em; margin-bottom:4px; }
        .folder-name { font-family:'Orbitron',monospace; font-size:0.65em; letter-spacing:2px; color:#00c8ff; }
        .folder-count { font-size:0.75em; color:rgba(255,255,255,0.4); margin-top:2px; }
        .images-grid { display:grid; grid-template-columns:repeat(auto-fill, minmax(200px, 1fr)); gap:15px; max-width:1000px; margin:0 auto; }
        .image-card { border:1px solid rgba(0,200,255,0.15); border-radius:8px; overflow:hidden; transition:all 0.3s; }
        .image-card:hover { border-color:rgba(0,200,255,0.4); box-shadow:0 0 20px rgba(0,200,255,0.1); }
        .image-card img { width:100%; height:180px; object-fit:cover; display:block; }
        .image-card-info { padding:8px; background:rgba(0,0,0,0.3); }
        .image-prompt { font-size:0.72em; color:rgba(255,255,255,0.5); overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
        .image-actions { display:flex; gap:5px; margin-top:6px; }
        .img-btn { flex:1; padding:5px; background:transparent; border:1px solid rgba(0,200,255,0.2); border-radius:3px; color:rgba(0,200,255,0.6); font-size:0.6em; cursor:pointer; transition:all 0.3s; font-family:'Orbitron',monospace; letter-spacing:1px; text-decoration:none; text-align:center; }
        .img-btn:hover { background:rgba(0,200,255,0.1); }
        .empty-gallery { text-align:center; color:rgba(255,255,255,0.3); padding:50px; font-family:'Orbitron',monospace; letter-spacing:3px; font-size:0.8em; }

        /* Historique */
        .history-page { padding:20px; overflow-y:auto; flex:1; }
        .history-item { padding:12px 16px; background:rgba(0,200,255,0.03); border:1px solid rgba(0,200,255,0.1); border-radius:6px; margin-bottom:10px; max-width:800px; margin:0 auto 10px; display:flex; justify-content:space-between; align-items:center; cursor:pointer; transition:all 0.3s; }
        .history-item:hover { border-color:rgba(0,200,255,0.3); background:rgba(0,200,255,0.06); }
        .history-prompt { font-size:0.9em; color:rgba(255,255,255,0.7); flex:1; }
        .history-reuse { padding:6px 12px; background:transparent; border:1px solid rgba(168,85,247,0.3); border-radius:3px; color:#a855f7; font-family:'Orbitron',monospace; font-size:0.6em; cursor:pointer; }

        /* Modals */
        .modal { display:none; position:fixed; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,0.85); z-index:200; justify-content:center; align-items:center; }
        .modal.active { display:flex; }
        .modal-content { background:#0a0a1a; border:1px solid rgba(0,200,255,0.3); border-radius:12px; padding:30px; width:400px; max-width:90vw; }
        .modal-title { font-family:'Orbitron',monospace; color:#00c8ff; letter-spacing:3px; margin-bottom:20px; font-size:1em; }
        .modal-input { width:100%; padding:12px; background:rgba(0,200,255,0.03); border:1px solid rgba(0,200,255,0.2); border-radius:4px; color:white; font-family:'Rajdhani',sans-serif; font-size:1em; outline:none; margin-bottom:12px; }
        .modal-input:focus { border-color:rgba(0,200,255,0.6); }
        .modal-buttons { display:flex; gap:10px; margin-top:5px; }
        .modal-btn { flex:1; padding:12px; border-radius:4px; font-family:'Orbitron',monospace; font-size:0.65em; letter-spacing:2px; cursor:pointer; transition:all 0.3s; border:none; }
        .modal-btn-confirm { background:rgba(0,200,255,0.1); border:1px solid rgba(0,200,255,0.4) !important; color:#00c8ff; }
        .modal-btn-cancel { background:transparent; border:1px solid rgba(255,255,255,0.1) !important; color:rgba(255,255,255,0.4); }
        .modal-btn-confirm:hover { background:rgba(0,200,255,0.2); }
        .modal-separator { text-align:center; color:rgba(255,255,255,0.3); margin:15px 0; font-size:0.85em; }
        .modal-link { color:#a855f7; cursor:pointer; text-decoration:underline; font-size:0.85em; display:block; text-align:center; margin-top:10px; }
        .error-msg { color:#ff6b6b; font-size:0.8em; margin-bottom:10px; display:none; }
    </style>
</head>
<body>
    <div class="bg-animation"></div>
    <div class="grid-bg"></div>

    <div class="header">
        <div>
            <div class="logo">⬡ ASTAX</div>
            <span class="logo-sub">GENERATIVE IMAGE AI</span>
        </div>
        <div class="user-area">
            <div class="user-info" id="userInfo">MODE INVITÉ</div>
            <button class="header-btn" id="authBtn" onclick="openAuthModal()">SE CONNECTER</button>
        </div>
    </div>

    <div class="nav">
        <button class="nav-btn active" onclick="showPage('chat', this)">⬡ CRÉER</button>
        <button class="nav-btn" onclick="showPage('gallery', this)">⬡ GALERIE</button>
        <button class="nav-btn" onclick="showPage('history', this)">⬡ HISTORIQUE</button>
    </div>

    <!-- PAGE CHAT -->
    <div class="page active" id="page-chat">
        <div class="chat-container">
            <div class="messages" id="messages"></div>
            <div class="progress-container" id="progressContainer">
                <div class="progress-text" id="progressText">⬡ GÉNÉRATION EN COURS</div>
                <div class="progress-bar"><div class="progress-fill"></div></div>
            </div>
        </div>
        <div class="styles-bar" id="stylesBar">
            <span style="color:rgba(255,255,255,0.3);font-size:0.8em;align-self:center;">Style :</span>
            <button class="style-btn" onclick="selectStyle(this, '')">Auto</button>
            <button class="style-btn" onclick="selectStyle(this, 'photorealistic, ultra detailed, 8k')">📷 Réaliste</button>
            <button class="style-btn" onclick="selectStyle(this, 'anime style, manga, vibrant colors, studio ghibli')">🎌 Anime</button>
            <button class="style-btn" onclick="selectStyle(this, 'oil painting, artistic, brushstrokes, renaissance')">🎨 Peinture</button>
            <button class="style-btn" onclick="selectStyle(this, 'pixel art, 16-bit, retro game style')">👾 Pixel Art</button>
            <button class="style-btn" onclick="selectStyle(this, 'cyberpunk, neon lights, futuristic, dark atmosphere')">🌆 Cyberpunk</button>
            <button class="style-btn" onclick="selectStyle(this, 'watercolor, soft colors, artistic, dreamy')">💧 Aquarelle</button>
        </div>
        <div class="input-area">
            <div class="input-row">
                <input type="text" id="userInput" placeholder="Décris ce que tu veux créer..." onkeypress="if(event.key==='Enter') envoyer()">
                <button class="send-btn" onclick="envoyer()">ENVOYER</button>
            </div>
            <div class="negative-row">
                <input type="text" id="negativeInput" class="negative-input" placeholder="❌ Prompt négatif : ce que tu ne veux PAS (ex: flou, texte, déformé...)">
            </div>
        </div>
    </div>

    <!-- PAGE GALERIE -->
    <div class="page" id="page-gallery">
        <div class="gallery-page">
            <div class="gallery-header">
                <div class="gallery-title">⬡ MES PROJETS</div>
                <button class="create-folder-btn" onclick="openCreateFolder()">+ NOUVEAU DOSSIER</button>
            </div>
            <div class="folders-list" id="foldersList"></div>
            <div class="images-grid" id="imagesGrid"></div>
        </div>
    </div>

    <!-- PAGE HISTORIQUE -->
    <div class="page" id="page-history">
        <div class="history-page">
            <div style="max-width:800px;margin:0 auto 20px;">
                <div style="font-family:'Orbitron',monospace;color:#00c8ff;letter-spacing:3px;margin-bottom:15px;">⬡ HISTORIQUE DES PROMPTS</div>
            </div>
            <div id="historyList"></div>
        </div>
    </div>

    <!-- Modal Auth -->
    <div class="modal" id="authModal">
        <div class="modal-content">
            <div class="modal-title" id="authTitle">⬡ CONNEXION</div>
            <div class="error-msg" id="authError"></div>
            <input type="text" class="modal-input" id="authUsername" placeholder="Nom d'utilisateur">
            <input type="password" class="modal-input" id="authPassword" placeholder="Mot de passe">
            <div class="modal-buttons">
                <button class="modal-btn modal-btn-cancel" onclick="closeAuthModal()">ANNULER</button>
                <button class="modal-btn modal-btn-confirm" id="authConfirmBtn" onclick="login()">CONNEXION</button>
            </div>
            <span class="modal-link" id="authSwitchLink" onclick="switchAuthMode()">Pas de compte ? S'inscrire</span>
        </div>
    </div>

    <!-- Modal Dossier -->
    <div class="modal" id="folderModal">
        <div class="modal-content">
            <div class="modal-title">⬡ NOUVEAU DOSSIER</div>
            <input type="text" class="modal-input" id="folderNameInput" placeholder="Nom du dossier...">
            <div class="modal-buttons">
                <button class="modal-btn modal-btn-cancel" onclick="closeModal('folderModal')">ANNULER</button>
                <button class="modal-btn modal-btn-confirm" onclick="createFolder()">CRÉER</button>
            </div>
        </div>
    </div>

    <!-- Modal Sauvegarde -->
    <div class="modal" id="saveModal">
        <div class="modal-content">
            <div class="modal-title">⬡ SAUVEGARDER</div>
            <div style="color:rgba(255,255,255,0.5);font-size:0.85em;margin-bottom:15px;">Choisir un dossier :</div>
            <div id="saveFoldersList" style="display:flex;flex-wrap:wrap;gap:10px;margin-bottom:15px;"></div>
            <div class="modal-buttons">
                <button class="modal-btn modal-btn-cancel" onclick="closeModal('saveModal')">ANNULER</button>
            </div>
        </div>
    </div>

    <script>
    let conversation = [];
    let currentFolder = null;
    let selectedStyle = "";
    let authMode = "login";
    let currentUser = null;
    let promptHistory = JSON.parse(localStorage.getItem('astax_history') || '[]');
    let pendingSaveImage = null;
    let pendingSavePrompt = null;

    // Init
    window.onload = async function() {
        ajouterMessage("bot", "Bonjour ! 👋 Je suis ton assistant créatif Astax. Dis-moi ce que tu veux créer comme image, et je vais te poser quelques questions pour obtenir le meilleur résultat possible !");
        const res = await fetch("/me");
        const data = await res.json();
        if (data.username) {
            currentUser = data.username;
            document.getElementById("userInfo").innerText = "👤 " + data.username.toUpperCase();
            document.getElementById("authBtn").innerText = "DÉCONNEXION";
            document.getElementById("authBtn").onclick = logout;
            promptHistory = data.prompt_history || [];
        }
    }

    // Navigation
    function showPage(page, btn) {
        document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
        document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
        document.getElementById('page-' + page).classList.add('active');
        if (btn) btn.classList.add('active');
        if (page === 'gallery') loadGallery();
        if (page === 'history') loadHistory();
    }

    // Styles
    function selectStyle(btn, style) {
        document.querySelectorAll('.style-btn').forEach(b => b.classList.remove('selected'));
        btn.classList.add('selected');
        selectedStyle = style;
    }

    // Chat
    function ajouterMessage(role, text) {
        const messages = document.getElementById("messages");
        const div = document.createElement("div");
        div.className = "message " + role;
        div.innerText = text;
        messages.appendChild(div);
        messages.scrollTop = messages.scrollHeight;
        return div;
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
            body: JSON.stringify({messages: conversation, style: selectedStyle})
        });
        const data = await response.json();

        if (data.type === "question") {
            ajouterMessage("bot", data.message);
            conversation.push({"role": "assistant", "content": data.message});
        } else if (data.type === "generate") {
            ajouterMessage("bot", data.message);
            conversation.push({"role": "assistant", "content": data.message});

            const count = data.count || 1;
            const negativePrompt = document.getElementById("negativeInput").value.trim();

            // Sauvegarder dans l'historique
            addToHistory(data.prompt);

            document.getElementById("progressContainer").style.display = "block";

            for (let i = 0; i < count; i++) {
                document.getElementById("progressText").innerText = `⬡ GÉNÉRATION ${i+1}/${count} EN COURS`;

                const imgResponse = await fetch("/generate", {
                    method: "POST",
                    headers: {"Content-Type": "application/json"},
                    body: JSON.stringify({
                        prompt: data.prompt,
                        negative_prompt: negativePrompt,
                        style: selectedStyle
                    })
                });

                if (imgResponse.ok) {
                    const blob = await imgResponse.blob();
                    const imgUrl = URL.createObjectURL(blob);

                    const imgDiv = document.createElement("div");
                    imgDiv.style = "margin:10px 0;animation:fadeIn 0.3s ease;";
                    const img = document.createElement("img");
                    img.src = imgUrl;
                    img.style = "max-width:100%;border-radius:8px;border:1px solid rgba(0,200,255,0.3);box-shadow:0 0 20px rgba(0,200,255,0.1);";

                    const btns = document.createElement("div");
                    btns.style = "display:flex;gap:10px;margin-top:8px;";

                    const dlBtn = document.createElement("a");
                    dlBtn.href = imgUrl;
                    dlBtn.download = `astax-${Date.now()}.png`;
                    dlBtn.innerText = "⬇ TÉLÉCHARGER";
                    dlBtn.style = "padding:8px 16px;background:transparent;border:1px solid rgba(0,200,255,0.3);color:#00c8ff;border-radius:4px;text-decoration:none;font-family:'Orbitron',monospace;font-size:0.6em;letter-spacing:1px;";

                    const saveBtn = document.createElement("button");
                    saveBtn.innerText = "💾 SAUVEGARDER";
                    saveBtn.style = "padding:8px 16px;background:transparent;border:1px solid rgba(168,85,247,0.3);color:#a855f7;border-radius:4px;font-family:'Orbitron',monospace;font-size:0.6em;letter-spacing:1px;cursor:pointer;";
                    const capturedUrl = imgUrl;
                    const capturedPrompt = data.prompt;
                    saveBtn.onclick = () => {
                        if (!currentUser) {
                            ajouterMessage("bot", "⚠️ Tu dois être connecté pour sauvegarder des images. Clique sur 'SE CONNECTER' en haut !");
                            return;
                        }
                        openSaveModal(capturedUrl, capturedPrompt);
                    };

                    btns.appendChild(dlBtn);
                    btns.appendChild(saveBtn);
                    imgDiv.appendChild(img);
                    imgDiv.appendChild(btns);
                    document.getElementById("messages").appendChild(imgDiv);
                    document.getElementById("messages").scrollTop = document.getElementById("messages").scrollHeight;
                }
            }

            document.getElementById("progressContainer").style.display = "none";
            conversation = [];
        }
    }

    // Historique
    function addToHistory(prompt) {
        promptHistory = promptHistory.filter(p => p !== prompt);
        promptHistory.unshift(prompt);
        if (promptHistory.length > 20) promptHistory = promptHistory.slice(0, 20);
        localStorage.setItem('astax_history', JSON.stringify(promptHistory));
        if (currentUser) {
            fetch("/save-history", {
                method: "POST",
                headers: {"Content-Type": "application/json"},
                body: JSON.stringify({history: promptHistory})
            });
        }
    }

    function loadHistory() {
        const list = document.getElementById("historyList");
        list.innerHTML = "";
        if (promptHistory.length === 0) {
            list.innerHTML = '<div class="empty-gallery">AUCUN HISTORIQUE</div>';
            return;
        }
        promptHistory.forEach(prompt => {
            const div = document.createElement("div");
            div.className = "history-item";
            div.innerHTML = `
                <div class="history-prompt">${prompt}</div>
                <button class="history-reuse" onclick="reusePrompt('${prompt.replace(/'/g, "\\'")}')">↺ RÉUTILISER</button>`;
            list.appendChild(div);
        });
    }

    function reusePrompt(prompt) {
        document.getElementById("userInput").value = prompt;
        showPage('chat', document.querySelector('.nav-btn'));
        document.querySelectorAll('.nav-btn')[0].classList.add('active');
    }

    // Galerie
    async function loadGallery() {
        const response = await fetch("/galleries");
        const data = await response.json();

        const foldersList = document.getElementById("foldersList");
        foldersList.innerHTML = "";

        if (!currentUser) {
            foldersList.innerHTML = '<div class="empty-gallery">CONNECTE-TOI POUR ACCÉDER À TES DOSSIERS</div>';
            document.getElementById("imagesGrid").innerHTML = "";
            return;
        }

        if (Object.keys(data).length === 0) {
            foldersList.innerHTML = '<div class="empty-gallery">AUCUN DOSSIER — CRÉE TON PREMIER PROJET !</div>';
            document.getElementById("imagesGrid").innerHTML = "";
            return;
        }

        Object.keys(data).forEach(name => {
            const card = document.createElement("div");
            card.className = "folder-card" + (currentFolder === name ? " active" : "");
            card.innerHTML = `<div class="folder-icon">📁</div><div class="folder-name">${name}</div><div class="folder-count">${data[name].length} image(s)</div>`;
            card.onclick = () => { currentFolder = name; loadGallery(); };
            foldersList.appendChild(card);
        });

        if (currentFolder && data[currentFolder]) {
            const grid = document.getElementById("imagesGrid");
            grid.innerHTML = "";
            data[currentFolder].forEach(img => {
                const card = document.createElement("div");
                card.className = "image-card";
                card.innerHTML = `
                    <img src="${img.image_b64}" alt="image">
                    <div class="image-card-info">
                        <div class="image-prompt">${img.prompt}</div>
                        <div class="image-actions">
                            <a href="${img.image_b64}" download="astax.png" class="img-btn">⬇ DL</a>
                            <button class="img-btn" onclick="deleteImage('${currentFolder}', '${img.id}')">✕ SUP</button>
                        </div>
                    </div>`;
                grid.appendChild(card);
            });
        }
    }

    function openCreateFolder() {
        if (!currentUser) {
            alert("Tu dois être connecté pour créer des dossiers !");
            return;
        }
        document.getElementById("folderModal").classList.add("active");
        document.getElementById("folderNameInput").focus();
    }

    function closeModal(id) {
        document.getElementById(id).classList.remove("active");
    }

    async function createFolder() {
        const name = document.getElementById("folderNameInput").value.trim();
        if (!name) return;
        await fetch("/create-folder", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({name: name})
        });
        document.getElementById("folderNameInput").value = "";
        closeModal("folderModal");
        loadGallery();
    }

    function openSaveModal(imgUrl, prompt) {
        pendingSaveImage = imgUrl;
        pendingSavePrompt = prompt;
        fetch("/galleries").then(r => r.json()).then(data => {
            const list = document.getElementById("saveFoldersList");
            list.innerHTML = "";
            if (Object.keys(data).length === 0) {
                list.innerHTML = '<div style="color:rgba(255,255,255,0.4);font-size:0.85em;">Aucun dossier — crée-en un dans la galerie !</div>';
            } else {
                Object.keys(data).forEach(name => {
                    const btn = document.createElement("button");
                    btn.innerText = "📁 " + name;
                    btn.style = "padding:10px 15px;background:rgba(0,200,255,0.05);border:1px solid rgba(0,200,255,0.2);border-radius:4px;color:#00c8ff;cursor:pointer;font-family:'Rajdhani',sans-serif;font-size:0.9em;";
                    btn.onclick = () => saveImage(name);
                    list.appendChild(btn);
                });
            }
            document.getElementById("saveModal").classList.add("active");
        });
    }

    async function saveImage(folderName) {
        const response = await fetch(pendingSaveImage);
        const blob = await response.blob();
        const reader = new FileReader();
        reader.readAsDataURL(blob);
        reader.onloadend = async function() {
            await fetch("/save-image", {
                method: "POST",
                headers: {"Content-Type": "application/json"},
                body: JSON.stringify({folder: folderName, image_b64: reader.result, prompt: pendingSavePrompt})
            });
            closeModal("saveModal");
            ajouterMessage("bot", `✅ Image sauvegardée dans "${folderName}" !`);
        }
    }

    async function deleteImage(folder, imageId) {
        await fetch("/delete-image", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({folder: folder, id: imageId})
        });
        loadGallery();
    }

    // Auth
    function openAuthModal() {
        authMode = "login";
        document.getElementById("authTitle").innerText = "⬡ CONNEXION";
        document.getElementById("authConfirmBtn").innerText = "CONNEXION";
        document.getElementById("authConfirmBtn").onclick = login;
        document.getElementById("authSwitchLink").innerText = "Pas de compte ? S'inscrire";
        document.getElementById("authError").style.display = "none";
        document.getElementById("authModal").classList.add("active");
    }

    function closeAuthModal() {
        document.getElementById("authModal").classList.remove("active");
        document.getElementById("authUsername").value = "";
        document.getElementById("authPassword").value = "";
    }

    function switchAuthMode() {
        if (authMode === "login") {
            authMode = "register";
            document.getElementById("authTitle").innerText = "⬡ INSCRIPTION";
            document.getElementById("authConfirmBtn").innerText = "S'INSCRIRE";
            document.getElementById("authConfirmBtn").onclick = register;
            document.getElementById("authSwitchLink").innerText = "Déjà un compte ? Se connecter";
        } else {
            authMode = "login";
            document.getElementById("authTitle").innerText = "⬡ CONNEXION";
            document.getElementById("authConfirmBtn").innerText = "CONNEXION";
            document.getElementById("authConfirmBtn").onclick = login;
            document.getElementById("authSwitchLink").innerText = "Pas de compte ? S'inscrire";
        }
        document.getElementById("authError").style.display = "none";
    }

    async function login() {
        const username = document.getElementById("authUsername").value.trim();
        const password = document.getElementById("authPassword").value;
        if (!username || !password) return;
        const res = await fetch("/login", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({username, password})
        });
        const data = await res.json();
        if (data.success) {
            currentUser = username;
            document.getElementById("userInfo").innerText = "👤 " + username.toUpperCase();
            document.getElementById("authBtn").innerText = "DÉCONNEXION";
            document.getElementById("authBtn").onclick = logout;
            promptHistory = data.prompt_history || [];
            closeAuthModal();
            ajouterMessage("bot", `✅ Bienvenue ${username} ! Tes données sont maintenant sauvegardées.`);
        } else {
            document.getElementById("authError").innerText = data.error;
            document.getElementById("authError").style.display = "block";
        }
    }

    async function register() {
        const username = document.getElementById("authUsername").value.trim();
        const password = document.getElementById("authPassword").value;
        if (!username || !password) return;
        if (password.length < 6) {
            document.getElementById("authError").innerText = "Le mot de passe doit faire au moins 6 caractères.";
            document.getElementById("authError").style.display = "block";
            return;
        }
        const res = await fetch("/register", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({username, password})
        });
        const data = await res.json();
        if (data.success) {
            currentUser = username;
            document.getElementById("userInfo").innerText = "👤 " + username.toUpperCase();
            document.getElementById("authBtn").innerText = "DÉCONNEXION";
            document.getElementById("authBtn").onclick = logout;
            closeAuthModal();
            ajouterMessage("bot", `🎉 Compte créé ! Bienvenue ${username} !`);
        } else {
            document.getElementById("authError").innerText = data.error;
            document.getElementById("authError").style.display = "block";
        }
    }

    async function logout() {
        await fetch("/logout", {method: "POST"});
        currentUser = null;
        document.getElementById("userInfo").innerText = "MODE INVITÉ";
        document.getElementById("authBtn").innerText = "SE CONNECTER";
        document.getElementById("authBtn").onclick = openAuthModal;
        promptHistory = JSON.parse(localStorage.getItem('astax_history') || '[]');
        ajouterMessage("bot", "Tu es maintenant déconnecté. À bientôt ! 👋");
    }
    </script>
</body>
</html>
    """

@app.route("/chat", methods=["POST"])
def chat():
    data = request.json
    messages = data.get("messages", [])
    style = data.get("style", "")

    style_hint = f" Le style choisi est : {style}." if style else ""

    system = f"""Tu es un assistant créatif qui aide les utilisateurs à créer des images avec une IA.{style_hint}

Ton rôle est de poser des questions précises pour affiner leur idée, puis générer un prompt en anglais pour l'IA.

Règles :
- Pose UNE seule question à la fois en français
- Maximum 3-4 questions avant de générer
- Avant de générer, demande : "Combien d'images voulez-vous générer ? (entre 1 et 5)"
- Quand tu as toutes les informations, réponds avec ce format exact:
  GENERATE: [prompt en anglais très détaillé, inclus le style si précisé]
  COUNT: [nombre entre 1 et 5]
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
        count = 1
        message = "Parfait, je génère tes images ! ✨"
        for line in lines:
            if line.startswith("GENERATE:"):
                prompt = line.replace("GENERATE:", "").strip()
            elif line.startswith("COUNT:"):
                try:
                    count = max(1, min(5, int(line.replace("COUNT:", "").strip())))
                except:
                    count = 1
            elif line.startswith("MESSAGE:"):
                message = line.replace("MESSAGE:", "").strip()
        return jsonify({"type": "generate", "prompt": prompt, "count": count, "message": message})
    else:
        return jsonify({"type": "question", "message": text})

@app.route("/generate", methods=["POST"])
def generate():
    data = request.json
    prompt = data.get("prompt", "a beautiful landscape")
    negative_prompt = data.get("negative_prompt", "")
    style = data.get("style", "")

    full_prompt = prompt
    if style:
        full_prompt = f"{prompt}, {style}"

    result = hf_client.text_to_image(
        full_prompt,
        model="stabilityai/stable-diffusion-xl-base-1.0",
        negative_prompt=negative_prompt if negative_prompt else None
    )

    img_io = io.BytesIO()
    result.save(img_io, format="PNG")
    img_io.seek(0)
    return send_file(img_io, mimetype="image/png")

@app.route("/me")
def me():
    username = session.get("username")
    if username and username in users:
        return jsonify({"username": username, "prompt_history": users[username].get("prompt_history", [])})
    return jsonify({"username": None})

@app.route("/register", methods=["POST"])
def register():
    data = request.json
    username = data.get("username", "").strip()
    password = data.get("password", "")
    if not username or not password:
        return jsonify({"success": False, "error": "Remplis tous les champs."})
    if username in users:
        return jsonify({"success": False, "error": "Ce nom d'utilisateur est déjà pris."})
    users[username] = {
        "password_hash": hash_password(password),
        "galleries": {},
        "prompt_history": []
    }
    session["username"] = username
    return jsonify({"success": True})

@app.route("/login", methods=["POST"])
def login():
    data = request.json
    username = data.get("username", "").strip()
    password = data.get("password", "")
    if username not in users:
        return jsonify({"success": False, "error": "Nom d'utilisateur introuvable."})
    if users[username]["password_hash"] != hash_password(password):
        return jsonify({"success": False, "error": "Mot de passe incorrect."})
    session["username"] = username
    return jsonify({"success": True, "prompt_history": users[username].get("prompt_history", [])})

@app.route("/logout", methods=["POST"])
def logout():
    session.pop("username", None)
    return jsonify({"success": True})

@app.route("/galleries")
def get_galleries():
    username = session.get("username")
    if username and username in users:
        return jsonify(users[username]["galleries"])
    return jsonify({})

@app.route("/create-folder", methods=["POST"])
def create_folder():
    username = session.get("username")
    if not username or username not in users:
        return jsonify({"success": False})
    data = request.json
    name = data.get("name", "").strip()
    if name and name not in users[username]["galleries"]:
        users[username]["galleries"][name] = []
    return jsonify({"success": True})

@app.route("/save-image", methods=["POST"])
def save_image():
    username = session.get("username")
    if not username or username not in users:
        return jsonify({"success": False})
    data = request.json
    folder = data.get("folder")
    image_b64 = data.get("image_b64")
    prompt = data.get("prompt", "")
    if folder in users[username]["galleries"]:
        users[username]["galleries"][folder].append({
            "id": str(uuid.uuid4()),
            "image_b64": image_b64,
            "prompt": prompt
        })
    return jsonify({"success": True})

@app.route("/delete-image", methods=["POST"])
def delete_image():
    username = session.get("username")
    if not username or username not in users:
        return jsonify({"success": False})
    data = request.json
    folder = data.get("folder")
    image_id = data.get("id")
    if folder in users[username]["galleries"]:
        users[username]["galleries"][folder] = [
            img for img in users[username]["galleries"][folder]
            if str(img["id"]) != str(image_id)
        ]
    return jsonify({"success": True})

@app.route("/save-history", methods=["POST"])
def save_history():
    username = session.get("username")
    if username and username in users:
        data = request.json
        users[username]["prompt_history"] = data.get("history", [])
    return jsonify({"success": True})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=7860)
