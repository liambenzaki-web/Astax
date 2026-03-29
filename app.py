import os
import io
import json
import uuid
import base64
from flask import Flask, request, send_file, jsonify
from huggingface_hub import InferenceClient
from groq import Groq
from PIL import Image

app = Flask(__name__)

HF_TOKEN = os.environ.get("HF_TOKEN")
GROQ_KEY = os.environ.get("GROQ_API_KEY")

hf_client = InferenceClient(provider="hf-inference", api_key=HF_TOKEN)
groq_client = Groq(api_key=GROQ_KEY)

# Stockage en mémoire (sessions)
galleries = {}  # {folder_name: [{"id": ..., "image_b64": ..., "prompt": ...}]}

@app.route("/")
def home():
    return """
    <html>
    <head>
        <title>Astax</title>
        <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Rajdhani:wght@300;400;600&display=swap" rel="stylesheet">
        <style>
            * { box-sizing: border-box; margin: 0; padding: 0; }
            body { background:#050510; color:white; font-family:'Rajdhani',sans-serif; height:100vh; display:flex; flex-direction:column; overflow:hidden; }
            .bg-animation { position:fixed; top:0; left:0; width:100%; height:100%; z-index:0; background: radial-gradient(ellipse at 20% 50%, rgba(120,40,200,0.15) 0%, transparent 50%), radial-gradient(ellipse at 80% 50%, rgba(0,200,255,0.1) 0%, transparent 50%); }
            .grid-bg { position:fixed; top:0; left:0; width:100%; height:100%; z-index:0; background-image: linear-gradient(rgba(0,200,255,0.03) 1px, transparent 1px), linear-gradient(90deg, rgba(0,200,255,0.03) 1px, transparent 1px); background-size:50px 50px; animation:gridMove 20s linear infinite; }
            @keyframes gridMove { 0%{transform:translateY(0)} 100%{transform:translateY(50px)} }
            .header { position:relative; z-index:10; text-align:center; padding:15px; border-bottom:1px solid rgba(0,200,255,0.2); background:rgba(5,5,16,0.8); backdrop-filter:blur(10px); }
            .logo { font-family:'Orbitron',monospace; font-size:2em; font-weight:900; background:linear-gradient(135deg,#00c8ff,#a855f7,#ff6b35); -webkit-background-clip:text; -webkit-text-fill-color:transparent; background-clip:text; letter-spacing:8px; animation:logoPulse 3s ease-in-out infinite; }
            @keyframes logoPulse { 0%,100%{filter:brightness(1)} 50%{filter:brightness(1.3)} }
            .tagline { color:rgba(0,200,255,0.6); font-size:0.75em; letter-spacing:4px; margin-top:3px; }
            
            /* Navigation */
            .nav { display:flex; justify-content:center; gap:20px; padding:10px; position:relative; z-index:10; background:rgba(5,5,16,0.6); border-bottom:1px solid rgba(0,200,255,0.1); }
            .nav-btn { padding:8px 20px; background:transparent; border:1px solid rgba(0,200,255,0.2); border-radius:4px; color:rgba(0,200,255,0.6); font-family:'Orbitron',monospace; font-size:0.65em; letter-spacing:2px; cursor:pointer; transition:all 0.3s; }
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
            .progress-container { display:none; margin:20px 0; text-align:center; }
            .progress-text { font-family:'Orbitron',monospace; font-size:0.8em; color:#00c8ff; letter-spacing:3px; margin-bottom:10px; animation:blink 1s ease-in-out infinite; }
            @keyframes blink { 0%,100%{opacity:1} 50%{opacity:0.4} }
            .progress-bar { width:100%; height:4px; background:rgba(0,200,255,0.1); border-radius:2px; overflow:hidden; }
            .progress-fill { height:100%; background:linear-gradient(90deg,#00c8ff,#a855f7,#ff6b35); animation:progressAnim 2s ease-in-out infinite; }
            @keyframes progressAnim { 0%{width:0%;margin-left:0} 50%{width:100%;margin-left:0} 100%{width:0%;margin-left:100%} }
            .generated-images { display:flex; flex-wrap:wrap; gap:10px; margin:10px 0; }
            .generated-images img { width:200px; height:200px; object-fit:cover; border-radius:8px; border:1px solid rgba(0,200,255,0.3); cursor:pointer; }
            .input-area { padding:15px; background:rgba(5,5,16,0.9); border-top:1px solid rgba(0,200,255,0.15); backdrop-filter:blur(10px); }
            .input-row { display:flex; gap:12px; max-width:800px; margin:0 auto; }
            input[type=text] { flex:1; padding:12px 18px; font-size:1em; font-family:'Rajdhani',sans-serif; border-radius:4px; border:1px solid rgba(0,200,255,0.2); background:rgba(0,200,255,0.03); color:white; outline:none; transition:all 0.3s; letter-spacing:1px; }
            input[type=text]:focus { border-color:rgba(0,200,255,0.6); box-shadow:0 0 15px rgba(0,200,255,0.1); }
            input[type=text]::placeholder { color:rgba(255,255,255,0.25); }
            .send-btn { padding:12px 24px; background:linear-gradient(135deg,rgba(0,200,255,0.15),rgba(168,85,247,0.15)); border:1px solid rgba(0,200,255,0.4); border-radius:4px; color:#00c8ff; font-family:'Orbitron',monospace; font-size:0.75em; letter-spacing:2px; cursor:pointer; transition:all 0.3s; }
            .send-btn:hover { background:linear-gradient(135deg,rgba(0,200,255,0.25),rgba(168,85,247,0.25)); box-shadow:0 0 20px rgba(0,200,255,0.3); transform:translateY(-1px); }

            /* Galerie */
            .gallery-page { padding:20px; overflow-y:auto; }
            .gallery-header { display:flex; justify-content:space-between; align-items:center; margin-bottom:20px; max-width:1000px; margin:0 auto 20px; }
            .gallery-title { font-family:'Orbitron',monospace; color:#00c8ff; letter-spacing:3px; }
            .create-folder-btn { padding:10px 20px; background:transparent; border:1px solid rgba(168,85,247,0.4); border-radius:4px; color:#a855f7; font-family:'Orbitron',monospace; font-size:0.65em; letter-spacing:2px; cursor:pointer; transition:all 0.3s; }
            .create-folder-btn:hover { background:rgba(168,85,247,0.1); box-shadow:0 0 15px rgba(168,85,247,0.2); }
            .folders-list { display:flex; flex-wrap:wrap; gap:15px; max-width:1000px; margin:0 auto 30px; }
            .folder-card { padding:15px 20px; background:rgba(0,200,255,0.03); border:1px solid rgba(0,200,255,0.15); border-radius:8px; cursor:pointer; transition:all 0.3s; min-width:150px; text-align:center; }
            .folder-card:hover { border-color:rgba(0,200,255,0.4); background:rgba(0,200,255,0.07); }
            .folder-card.active { border-color:#00c8ff; background:rgba(0,200,255,0.1); }
            .folder-icon { font-size:2em; margin-bottom:5px; }
            .folder-name { font-family:'Orbitron',monospace; font-size:0.7em; letter-spacing:2px; color:#00c8ff; }
            .folder-count { font-size:0.75em; color:rgba(255,255,255,0.4); margin-top:3px; }
            .images-grid { display:grid; grid-template-columns:repeat(auto-fill, minmax(200px, 1fr)); gap:15px; max-width:1000px; margin:0 auto; }
            .image-card { border:1px solid rgba(0,200,255,0.15); border-radius:8px; overflow:hidden; transition:all 0.3s; }
            .image-card:hover { border-color:rgba(0,200,255,0.4); box-shadow:0 0 20px rgba(0,200,255,0.1); }
            .image-card img { width:100%; height:200px; object-fit:cover; display:block; }
            .image-card-info { padding:10px; background:rgba(0,0,0,0.3); }
            .image-prompt { font-size:0.75em; color:rgba(255,255,255,0.5); overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
            .image-actions { display:flex; gap:5px; margin-top:8px; }
            .img-btn { flex:1; padding:5px; background:transparent; border:1px solid rgba(0,200,255,0.2); border-radius:3px; color:rgba(0,200,255,0.6); font-size:0.65em; cursor:pointer; transition:all 0.3s; font-family:'Orbitron',monospace; letter-spacing:1px; }
            .img-btn:hover { background:rgba(0,200,255,0.1); }
            .empty-gallery { text-align:center; color:rgba(255,255,255,0.3); padding:50px; font-family:'Orbitron',monospace; letter-spacing:3px; }

            /* Modal */
            .modal { display:none; position:fixed; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,0.8); z-index:100; justify-content:center; align-items:center; }
            .modal.active { display:flex; }
            .modal-content { background:#0a0a1a; border:1px solid rgba(0,200,255,0.3); border-radius:12px; padding:30px; width:400px; }
            .modal-title { font-family:'Orbitron',monospace; color:#00c8ff; letter-spacing:3px; margin-bottom:20px; }
            .modal-input { width:100%; padding:12px; background:rgba(0,200,255,0.03); border:1px solid rgba(0,200,255,0.2); border-radius:4px; color:white; font-family:'Rajdhani',sans-serif; font-size:1em; outline:none; margin-bottom:15px; }
            .modal-input:focus { border-color:rgba(0,200,255,0.6); }
            .modal-buttons { display:flex; gap:10px; }
            .modal-btn { flex:1; padding:12px; border-radius:4px; font-family:'Orbitron',monospace; font-size:0.7em; letter-spacing:2px; cursor:pointer; transition:all 0.3s; }
            .modal-btn-confirm { background:rgba(0,200,255,0.1); border:1px solid rgba(0,200,255,0.4); color:#00c8ff; }
            .modal-btn-cancel { background:transparent; border:1px solid rgba(255,255,255,0.1); color:rgba(255,255,255,0.4); }

            /* Save modal */
            .save-modal { display:none; position:fixed; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,0.8); z-index:100; justify-content:center; align-items:center; }
            .save-modal.active { display:flex; }
        </style>
    </head>
    <body>
        <div class="bg-animation"></div>
        <div class="grid-bg"></div>

        <div class="header">
            <div class="logo">⬡ ASTAX</div>
            <div class="tagline">GENERATIVE IMAGE AI</div>
        </div>

        <div class="nav">
            <button class="nav-btn active" onclick="showPage('chat')">⬡ CRÉER</button>
            <button class="nav-btn" onclick="showPage('gallery')">⬡ GALERIE</button>
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
            <div class="input-area">
                <div class="input-row">
                    <input type="text" id="userInput" placeholder="Décris ce que tu veux créer..." onkeypress="if(event.key==='Enter') envoyer()">
                    <button class="send-btn" onclick="envoyer()">ENVOYER</button>
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

        <!-- Modal création dossier -->
        <div class="modal" id="folderModal">
            <div class="modal-content">
                <div class="modal-title">⬡ NOUVEAU DOSSIER</div>
                <input type="text" class="modal-input" id="folderNameInput" placeholder="Nom du dossier...">
                <div class="modal-buttons">
                    <button class="modal-btn modal-btn-cancel" onclick="closeModal()">ANNULER</button>
                    <button class="modal-btn modal-btn-confirm" onclick="createFolder()">CRÉER</button>
                </div>
            </div>
        </div>

        <!-- Modal sauvegarde image -->
        <div class="save-modal" id="saveModal">
            <div class="modal-content">
                <div class="modal-title">⬡ SAUVEGARDER</div>
                <div style="color:rgba(255,255,255,0.5);font-size:0.85em;margin-bottom:15px;">Choisir un dossier :</div>
                <div id="saveFoldersList" style="display:flex;flex-wrap:wrap;gap:10px;margin-bottom:15px;"></div>
                <div class="modal-buttons">
                    <button class="modal-btn modal-btn-cancel" onclick="closeSaveModal()">ANNULER</button>
                </div>
            </div>
        </div>

        <script>
        let conversation = [];
        let currentFolder = null;
        let pendingImages = [];

        // Navigation
        function showPage(page) {
            document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
            document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
            document.getElementById('page-' + page).classList.add('active');
            event.target.classList.add('active');
            if (page === 'gallery') loadGallery();
        }

        // Chat
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
                body: JSON.stringify({messages: conversation})
            });
            const data = await response.json();

            if (data.type === "question") {
                ajouterMessage("bot", data.message);
                conversation.push({"role": "assistant", "content": data.message});
            } else if (data.type === "generate") {
                ajouterMessage("bot", data.message);
                conversation.push({"role": "assistant", "content": data.message});

                const count = data.count || 1;
                document.getElementById("progressContainer").style.display = "block";
                
                pendingImages = [];
                
                for (let i = 0; i < count; i++) {
                    document.getElementById("progressText").innerText = `⬡ GÉNÉRATION ${i+1}/${count} EN COURS`;
                    
                    const imgResponse = await fetch("/generate", {
                        method: "POST",
                        headers: {"Content-Type": "application/json"},
                        body: JSON.stringify({prompt: data.prompt, seed: Math.floor(Math.random() * 1000000)})
                    });

                    if (imgResponse.ok) {
                        const blob = await imgResponse.blob();
                        const imgUrl = URL.createObjectURL(blob);
                        
                        // Convertir en base64 pour stockage
                        const reader = new FileReader();
                        reader.readAsDataURL(blob);
                        reader.onloadend = function() {
                            pendingImages.push({
                                id: Date.now() + Math.random(),
                                image_b64: reader.result,
                                prompt: data.prompt
                            });
                        }
                        
                        // Afficher l'image
                        const imgDiv = document.createElement("div");
                        imgDiv.style = "margin:10px 0;";
                        const img = document.createElement("img");
                        img.src = imgUrl;
                        img.style = "max-width:100%;border-radius:8px;border:1px solid rgba(0,200,255,0.3);";
                        
                        // Boutons
                        const btns = document.createElement("div");
                        btns.style = "display:flex;gap:10px;margin-top:8px;";
                        
                        const dlBtn = document.createElement("a");
                        dlBtn.href = imgUrl;
                        dlBtn.download = `astax-${i+1}.png`;
                        dlBtn.innerText = "⬇ TÉLÉCHARGER";
                        dlBtn.style = "padding:8px 16px;background:transparent;border:1px solid rgba(0,200,255,0.3);color:#00c8ff;border-radius:4px;text-decoration:none;font-family:'Orbitron',monospace;font-size:0.65em;letter-spacing:1px;";
                        
                        const saveBtn = document.createElement("button");
                        saveBtn.innerText = "💾 SAUVEGARDER";
                        saveBtn.style = "padding:8px 16px;background:transparent;border:1px solid rgba(168,85,247,0.3);color:#a855f7;border-radius:4px;font-family:'Orbitron',monospace;font-size:0.65em;letter-spacing:1px;cursor:pointer;";
                        const capturedUrl = imgUrl;
                        const capturedPrompt = data.prompt;
                        saveBtn.onclick = () => openSaveModal(capturedUrl, capturedPrompt);
                        
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

        // Galerie
        async function loadGallery() {
            const response = await fetch("/galleries");
            const data = await response.json();
            
            const foldersList = document.getElementById("foldersList");
            foldersList.innerHTML = "";
            
            if (Object.keys(data).length === 0) {
                foldersList.innerHTML = '<div class="empty-gallery">AUCUN DOSSIER — CRÉE TON PREMIER PROJET !</div>';
                document.getElementById("imagesGrid").innerHTML = "";
                return;
            }
            
            Object.keys(data).forEach(name => {
                const card = document.createElement("div");
                card.className = "folder-card" + (currentFolder === name ? " active" : "");
                card.innerHTML = `<div class="folder-icon">📁</div><div class="folder-name">${name}</div><div class="folder-count">${data[name].length} image(s)</div>`;
                card.onclick = () => selectFolder(name);
                foldersList.appendChild(card);
            });
            
            if (currentFolder && data[currentFolder]) {
                showFolderImages(data[currentFolder]);
            }
        }

        function selectFolder(name) {
            currentFolder = name;
            loadGallery();
        }

        function showFolderImages(images) {
            const grid = document.getElementById("imagesGrid");
            grid.innerHTML = "";
            
            if (images.length === 0) {
                grid.innerHTML = '<div class="empty-gallery">DOSSIER VIDE</div>';
                return;
            }
            
            images.forEach(img => {
                const card = document.createElement("div");
                card.className = "image-card";
                card.innerHTML = `
                    <img src="${img.image_b64}" alt="Generated image">
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

        // Dossiers
        function openCreateFolder() {
            document.getElementById("folderModal").classList.add("active");
            document.getElementById("folderNameInput").focus();
        }

        function closeModal() {
            document.getElementById("folderModal").classList.remove("active");
            document.getElementById("folderNameInput").value = "";
        }

        async function createFolder() {
            const name = document.getElementById("folderNameInput").value.trim();
            if (!name) return;
            await fetch("/create-folder", {
                method: "POST",
                headers: {"Content-Type": "application/json"},
                body: JSON.stringify({name: name})
            });
            closeModal();
            loadGallery();
        }

        // Sauvegarde
        function openSaveModal(imgUrl, prompt) {
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
                        btn.onclick = () => saveImage(name, imgUrl, prompt);
                        list.appendChild(btn);
                    });
                }
                
                document.getElementById("saveModal").classList.add("active");
            });
        }

        function closeSaveModal() {
            document.getElementById("saveModal").classList.remove("active");
        }

        async function saveImage(folderName, imgUrl, prompt) {
            const response = await fetch(imgUrl);
            const blob = await response.blob();
            const reader = new FileReader();
            reader.readAsDataURL(blob);
            reader.onloadend = async function() {
                await fetch("/save-image", {
                    method: "POST",
                    headers: {"Content-Type": "application/json"},
                    body: JSON.stringify({folder: folderName, image_b64: reader.result, prompt: prompt})
                });
                closeSaveModal();
                ajouterMessage("bot", `✅ Image sauvegardée dans le dossier "${folderName}" !`);
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
- Avant de générer, demande toujours : "Combien d'images voulez-vous générer ? (entre 1 et 5)"
- Quand tu as toutes les informations including le nombre d'images, réponds avec ce format exact:
  GENERATE: [prompt en anglais très détaillé]
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
                    count = int(line.replace("COUNT:", "").strip())
                    count = max(1, min(5, count))
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
    
    result = hf_client.text_to_image(
        prompt,
        model="stabilityai/stable-diffusion-xl-base-1.0"
    )
    
    img_io = io.BytesIO()
    result.save(img_io, format="PNG")
    img_io.seek(0)
    return send_file(img_io, mimetype="image/png")

@app.route("/galleries", methods=["GET"])
def get_galleries():
    return jsonify(galleries)

@app.route("/create-folder", methods=["POST"])
def create_folder():
    data = request.json
    name = data.get("name", "").strip()
    if name and name not in galleries:
        galleries[name] = []
    return jsonify({"success": True})

@app.route("/save-image", methods=["POST"])
def save_image():
    data = request.json
    folder = data.get("folder")
    image_b64 = data.get("image_b64")
    prompt = data.get("prompt", "")
    if folder in galleries:
        galleries[folder].append({
            "id": str(uuid.uuid4()),
            "image_b64": image_b64,
            "prompt": prompt
        })
    return jsonify({"success": True})

@app.route("/delete-image", methods=["POST"])
def delete_image():
    data = request.json
    folder = data.get("folder")
    image_id = data.get("id")
    if folder in galleries:
        galleries[folder] = [img for img in galleries[folder] if str(img["id"]) != str(image_id)]
    return jsonify({"success": True})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=7860)
