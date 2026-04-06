import os
import io
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

users = {}

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

@app.route("/")
def home():
    return """
<!DOCTYPE html>
<html lang="fr">
<head>
    <title>Astax</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        * { box-sizing:border-box; margin:0; padding:0; }
        :root {
            --bg:#1a1a1a; --bg2:#212121; --bg3:#2a2a2a;
            --border:rgba(255,255,255,0.08); --border-hover:rgba(255,165,0,0.3);
            --orange:#ff8c00; --orange-light:#ffa500; --orange-dim:rgba(255,140,0,0.12);
            --text:#ececec; --text-dim:rgba(255,255,255,0.45); --text-dimmer:rgba(255,255,255,0.25);
            --radius:12px; --radius-sm:8px;
        }
        body { background:var(--bg); color:var(--text); font-family:'Inter',sans-serif; height:100vh; display:flex; flex-direction:column; overflow:hidden; font-size:14px; }

        .layout { display:flex; flex:1; overflow:hidden; }

        /* SIDEBAR */
        .sidebar { width:240px; background:var(--bg2); border-right:1px solid var(--border); display:flex; flex-direction:column; padding:20px 0; flex-shrink:0; }
        .logo-area { padding:0 16px 20px; border-bottom:1px solid var(--border); margin-bottom:12px; }
        .logo { display:flex; align-items:center; gap:10px; }
        .logo-icon { width:34px; height:34px; background:linear-gradient(135deg,var(--orange),#ff4500); border-radius:10px; display:flex; align-items:center; justify-content:center; font-size:16px; flex-shrink:0; box-shadow:0 4px 12px rgba(255,140,0,0.3); }
        .logo-text { font-weight:700; font-size:1.1em; }
        .logo-sub { font-size:0.68em; color:var(--text-dim); margin-top:1px; }

        .nav-section { padding:0 10px; }
        .nav-label { font-size:0.62em; color:var(--text-dimmer); letter-spacing:1.5px; text-transform:uppercase; padding:0 6px; margin-bottom:5px; margin-top:10px; font-weight:600; }
        .nav-item { display:flex; align-items:center; gap:8px; padding:8px 10px; border-radius:var(--radius-sm); cursor:pointer; color:var(--text-dim); font-size:0.88em; font-weight:500; transition:all 0.2s; margin-bottom:2px; border:1px solid transparent; user-select:none; }
        .nav-item:hover { background:var(--bg3); color:var(--text); }
        .nav-item.active { background:var(--orange-dim); color:var(--orange-light); border-color:rgba(255,140,0,0.15); }

        .nav-divider { height:1px; background:var(--border); margin:10px 6px; }

        .styles-section { padding:0 10px; flex:1; overflow-y:auto; }
        .style-chip { display:flex; align-items:center; gap:8px; padding:7px 10px; border-radius:var(--radius-sm); cursor:pointer; color:var(--text-dim); font-size:0.83em; transition:all 0.2s; margin-bottom:2px; user-select:none; }
        .style-chip:hover { background:var(--bg3); color:var(--text); }
        .style-chip.selected { color:var(--orange-light); background:var(--orange-dim); }

        /* User area */
        .user-area { padding:12px 10px 0; border-top:1px solid var(--border); margin-top:auto; }
        .user-card { display:flex; align-items:center; gap:10px; padding:10px; border-radius:var(--radius-sm); background:var(--bg3); cursor:pointer; transition:all 0.2s; user-select:none; }
        .user-card:hover { background:rgba(255,255,255,0.05); }
        .user-avatar { width:30px; height:30px; background:linear-gradient(135deg,var(--orange),#ff4500); border-radius:50%; display:flex; align-items:center; justify-content:center; font-size:0.82em; font-weight:700; flex-shrink:0; }
        .user-name { font-weight:500; font-size:0.85em; }
        .user-status { font-size:0.7em; color:var(--text-dim); }

        /* MAIN */
        .main { flex:1; display:flex; flex-direction:column; overflow:hidden; }
        .page { display:none; flex:1; flex-direction:column; overflow:hidden; }
        .page.active { display:flex; }

        /* CHAT */
        .chat-area { flex:1; overflow-y:auto; padding:28px; }
        .chat-area::-webkit-scrollbar { width:4px; }
        .chat-area::-webkit-scrollbar-thumb { background:rgba(255,255,255,0.1); border-radius:3px; }

        .chat-welcome { text-align:center; padding:50px 20px 30px; }
        .welcome-icon { width:52px; height:52px; background:linear-gradient(135deg,var(--orange),#ff4500); border-radius:14px; display:flex; align-items:center; justify-content:center; font-size:22px; margin:0 auto 14px; box-shadow:0 8px 24px rgba(255,140,0,0.25); }
        .chat-welcome h2 { font-size:1.3em; font-weight:600; margin-bottom:8px; }
        .chat-welcome p { color:var(--text-dim); font-size:0.88em; line-height:1.6; max-width:380px; margin:0 auto; }

        .messages { display:flex; flex-direction:column; gap:14px; max-width:680px; margin:0 auto; width:100%; }
        .msg-row { display:flex; gap:10px; align-items:flex-start; }
        .msg-row.user { flex-direction:row-reverse; }
        .msg-avatar { width:30px; height:30px; border-radius:50%; display:flex; align-items:center; justify-content:center; font-size:0.78em; font-weight:700; flex-shrink:0; margin-top:2px; }
        .msg-avatar.bot { background:linear-gradient(135deg,var(--orange),#ff4500); }
        .msg-avatar.user { background:var(--bg3); border:1px solid var(--border); }
        .msg-bubble { padding:10px 14px; border-radius:var(--radius); max-width:78%; line-height:1.6; font-size:0.9em; }
        .msg-bubble.bot { background:var(--bg3); border:1px solid var(--border); border-top-left-radius:4px; }
        .msg-bubble.user { background:var(--orange-dim); border:1px solid rgba(255,140,0,0.2); border-top-right-radius:4px; }

        .progress-wrap { display:none; max-width:680px; margin:0 auto; padding:14px; background:var(--bg3); border:1px solid var(--border); border-radius:var(--radius); }
        .progress-label { font-size:0.78em; color:var(--text-dim); margin-bottom:8px; }
        .progress-bar { height:3px; background:rgba(255,255,255,0.06); border-radius:2px; overflow:hidden; }
        .progress-fill { height:100%; background:linear-gradient(90deg,var(--orange),#ff4500); animation:prog 1.8s ease-in-out infinite; }
        @keyframes prog { 0%{width:0%;margin-left:0} 50%{width:70%;margin-left:0} 100%{width:0%;margin-left:100%} }

        .gen-wrap { max-width:680px; margin:0 auto; animation:fadeUp 0.3s ease; }
        @keyframes fadeUp { from{opacity:0;transform:translateY(10px)} to{opacity:1;transform:translateY(0)} }
        .gen-wrap img { max-width:480px; width:100%; border-radius:var(--radius); border:1px solid var(--border); display:block; }
        .gen-actions { display:flex; gap:8px; margin-top:8px; flex-wrap:wrap; }
        .gen-btn { padding:6px 14px; border-radius:var(--radius-sm); font-size:0.78em; font-weight:500; cursor:pointer; transition:all 0.2s; font-family:'Inter',sans-serif; border:1px solid var(--border); background:var(--bg3); color:var(--text-dim); text-decoration:none; display:inline-block; }
        .gen-btn:hover { color:var(--text); border-color:rgba(255,255,255,0.15); }
        .gen-btn.primary { background:var(--orange-dim); border-color:rgba(255,140,0,0.25); color:var(--orange-light); }
        .gen-btn.primary:hover { background:rgba(255,140,0,0.2); }

        /* INPUT */
        .input-area { padding:14px 28px 18px; border-top:1px solid var(--border); background:var(--bg); }
        .input-main { max-width:680px; margin:0 auto; }
        .input-box { display:flex; align-items:flex-end; gap:8px; background:var(--bg2); border:1px solid var(--border); border-radius:var(--radius); padding:10px 12px; transition:border-color 0.2s; }
        .input-box:focus-within { border-color:rgba(255,140,0,0.4); }
        textarea { flex:1; background:transparent; border:none; outline:none; color:var(--text); font-family:'Inter',sans-serif; font-size:0.9em; resize:none; max-height:120px; line-height:1.5; padding:2px 0; }
        textarea::placeholder { color:var(--text-dimmer); }
        .send-btn { width:34px; height:34px; background:var(--orange); border:none; border-radius:var(--radius-sm); color:white; font-size:1.1em; cursor:pointer; transition:all 0.2s; display:flex; align-items:center; justify-content:center; flex-shrink:0; }
        .send-btn:hover { background:var(--orange-light); transform:scale(1.05); }
        .input-meta { display:flex; gap:8px; margin-top:7px; align-items:center; }
        .neg-wrap { flex:1; display:flex; align-items:center; gap:6px; background:var(--bg2); border:1px solid var(--border); border-radius:var(--radius-sm); padding:5px 10px; }
        .neg-label { font-size:0.7em; color:rgba(255,100,100,0.6); white-space:nowrap; font-weight:500; }
        .neg-input { background:transparent; border:none; outline:none; color:var(--text); font-family:'Inter',sans-serif; font-size:0.8em; flex:1; }
        .neg-input::placeholder { color:var(--text-dimmer); }
        .inspire-btn { padding:5px 12px; background:transparent; border:1px solid var(--border); border-radius:var(--radius-sm); color:var(--text-dim); font-size:0.76em; cursor:pointer; transition:all 0.2s; white-space:nowrap; font-family:'Inter',sans-serif; }
        .inspire-btn:hover { border-color:var(--border-hover); color:var(--orange-light); background:var(--orange-dim); }

        /* GALLERY */
        .page-header { padding:20px 28px 14px; border-bottom:1px solid var(--border); display:flex; justify-content:space-between; align-items:center; }
        .page-title { font-size:1.05em; font-weight:600; }
        .page-subtitle { font-size:0.78em; color:var(--text-dim); margin-top:2px; }
        .page-btn { padding:7px 14px; background:var(--orange-dim); border:1px solid rgba(255,140,0,0.2); border-radius:var(--radius-sm); color:var(--orange-light); font-size:0.78em; font-weight:500; cursor:pointer; transition:all 0.2s; font-family:'Inter',sans-serif; }
        .page-btn:hover { background:rgba(255,140,0,0.2); }
        .gallery-content { flex:1; overflow-y:auto; padding:18px 28px; }
        .folders-row { display:flex; flex-wrap:wrap; gap:8px; margin-bottom:20px; }
        .folder-pill { display:flex; align-items:center; gap:6px; padding:6px 14px; border-radius:20px; border:1px solid var(--border); cursor:pointer; font-size:0.8em; color:var(--text-dim); transition:all 0.2s; user-select:none; }
        .folder-pill:hover { border-color:var(--border-hover); color:var(--text); }
        .folder-pill.active { background:var(--orange-dim); border-color:rgba(255,140,0,0.3); color:var(--orange-light); }
        .folder-badge { background:rgba(255,255,255,0.08); border-radius:10px; padding:1px 7px; font-size:0.85em; }
        .images-grid { display:grid; grid-template-columns:repeat(auto-fill,minmax(170px,1fr)); gap:10px; }
        .img-card { border-radius:var(--radius); overflow:hidden; border:1px solid var(--border); background:var(--bg2); transition:all 0.2s; }
        .img-card:hover { border-color:var(--border-hover); transform:translateY(-2px); }
        .img-card img { width:100%; height:150px; object-fit:cover; display:block; }
        .img-card-info { padding:8px; }
        .img-card-prompt { font-size:0.72em; color:var(--text-dim); white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
        .img-card-actions { display:flex; gap:4px; margin-top:6px; }
        .img-action { flex:1; padding:4px; text-align:center; border-radius:5px; border:1px solid var(--border); font-size:0.68em; color:var(--text-dim); cursor:pointer; transition:all 0.2s; background:transparent; font-family:'Inter',sans-serif; text-decoration:none; display:flex; align-items:center; justify-content:center; }
        .img-action:hover { background:var(--bg3); color:var(--text); }

        /* HISTORY */
        .history-content { flex:1; overflow-y:auto; padding:18px 28px; }
        .history-item { display:flex; align-items:center; gap:10px; padding:10px 14px; border-radius:var(--radius); border:1px solid var(--border); background:var(--bg2); margin-bottom:7px; transition:all 0.2s; }
        .history-item:hover { border-color:var(--border-hover); }
        .history-text { flex:1; font-size:0.86em; color:var(--text-dim); }
        .history-reuse { padding:5px 10px; border-radius:var(--radius-sm); border:1px solid var(--border); background:transparent; color:var(--text-dim); font-size:0.72em; cursor:pointer; transition:all 0.2s; font-family:'Inter',sans-serif; flex-shrink:0; }
        .history-reuse:hover { background:var(--orange-dim); border-color:rgba(255,140,0,0.3); color:var(--orange-light); }

        /* MODALS */
        .overlay { display:none; position:fixed; inset:0; background:rgba(0,0,0,0.65); z-index:1000; justify-content:center; align-items:center; }
        .overlay.open { display:flex; }
        .modal-box { background:var(--bg2); border:1px solid rgba(255,255,255,0.12); border-radius:16px; padding:26px; width:360px; max-width:90vw; }
        .modal-head { display:flex; justify-content:space-between; align-items:center; margin-bottom:18px; }
        .modal-title { font-size:0.98em; font-weight:600; }
        .modal-close { background:none; border:none; color:var(--text-dim); font-size:1.1em; cursor:pointer; padding:2px 6px; border-radius:4px; }
        .modal-close:hover { color:var(--text); background:var(--bg3); }
        .field-label { font-size:0.76em; color:var(--text-dim); margin-bottom:5px; font-weight:500; }
        .field-input { width:100%; padding:9px 12px; background:var(--bg3); border:1px solid var(--border); border-radius:var(--radius-sm); color:var(--text); font-family:'Inter',sans-serif; font-size:0.87em; outline:none; margin-bottom:12px; transition:border-color 0.2s; }
        .field-input:focus { border-color:rgba(255,140,0,0.4); }
        .modal-footer { display:flex; gap:8px; margin-top:4px; }
        .btn { flex:1; padding:9px; border-radius:var(--radius-sm); font-family:'Inter',sans-serif; font-size:0.8em; font-weight:500; cursor:pointer; transition:all 0.2s; border:none; }
        .btn-ghost { background:var(--bg3); color:var(--text-dim); border:1px solid var(--border) !important; }
        .btn-ghost:hover { color:var(--text); }
        .btn-orange { background:var(--orange); color:white; }
        .btn-orange:hover { background:var(--orange-light); }
        .auth-switch { text-align:center; margin-top:12px; font-size:0.78em; color:var(--text-dim); }
        .auth-link { color:var(--orange-light); cursor:pointer; }
        .auth-link:hover { text-decoration:underline; }
        .err-msg { font-size:0.76em; color:#ff6b6b; margin-bottom:10px; padding:7px 10px; background:rgba(255,100,100,0.08); border-radius:var(--radius-sm); border:1px solid rgba(255,100,100,0.15); display:none; }
        .save-folders { display:flex; flex-wrap:wrap; gap:7px; margin-bottom:12px; }
        .save-folder-btn { padding:7px 13px; background:var(--bg3); border:1px solid var(--border); border-radius:var(--radius-sm); color:var(--text-dim); font-size:0.8em; cursor:pointer; transition:all 0.2s; font-family:'Inter',sans-serif; }
        .save-folder-btn:hover { border-color:var(--border-hover); color:var(--orange-light); background:var(--orange-dim); }
        .empty-state { text-align:center; padding:50px 20px; color:var(--text-dimmer); }
        .empty-icon { font-size:2.2em; margin-bottom:10px; }
        .empty-state p { font-size:0.85em; line-height:1.6; }
    </style>
</head>
<body>
<div class="layout">
    <!-- SIDEBAR -->
    <aside class="sidebar">
        <div class="logo-area">
            <div class="logo">
                <div class="logo-icon">✦</div>
                <div>
                    <div class="logo-text">Astax</div>
                    <div class="logo-sub">Generative Image AI</div>
                </div>
            </div>
        </div>

        <div class="nav-section">
            <div class="nav-label">Navigation</div>
            <div class="nav-item active" id="nav-chat" onclick="showPage('chat')">
                <span>✦</span> Créer
            </div>
            <div class="nav-item" id="nav-gallery" onclick="showPage('gallery')">
                <span>⊞</span> Galerie
            </div>
            <div class="nav-item" id="nav-history" onclick="showPage('history')">
                <span>↺</span> Historique
            </div>
            <div class="nav-divider"></div>
            <div class="nav-label">Style rapide</div>
        </div>

        <div class="styles-section">
            <div class="style-chip selected" onclick="selectStyle(this,'')">◈ Auto</div>
            <div class="style-chip" onclick="selectStyle(this,'photorealistic, ultra detailed, 8k photography')">📷 Réaliste</div>
            <div class="style-chip" onclick="selectStyle(this,'anime style, manga, vibrant, studio ghibli')">🎌 Anime</div>
            <div class="style-chip" onclick="selectStyle(this,'oil painting, artistic brushstrokes, renaissance')">🎨 Peinture</div>
            <div class="style-chip" onclick="selectStyle(this,'pixel art, 16-bit retro game style')">👾 Pixel Art</div>
            <div class="style-chip" onclick="selectStyle(this,'cyberpunk, neon lights, futuristic dark city')">🌆 Cyberpunk</div>
            <div class="style-chip" onclick="selectStyle(this,'watercolor, soft dreamy artistic illustration')">💧 Aquarelle</div>
            <div class="style-chip" onclick="selectStyle(this,'dark fantasy, dramatic lighting, epic scene')">⚔️ Dark Fantasy</div>
            <div class="style-chip" onclick="selectStyle(this,'minimalist, clean lines, geometric, modern')">◻ Minimaliste</div>
        </div>

        <div class="user-area">
            <div class="user-card" id="userCard" onclick="userCardClick()">
                <div class="user-avatar" id="userAvatar">?</div>
                <div>
                    <div class="user-name" id="userName">Mode invité</div>
                    <div class="user-status" id="userStatus">Cliquer pour se connecter</div>
                </div>
            </div>
        </div>
    </aside>

    <!-- MAIN -->
    <main class="main">
        <!-- PAGE CHAT -->
        <div class="page active" id="page-chat">
            <div class="chat-area" id="chatArea">
                <div class="chat-welcome" id="welcomeMsg">
                    <div class="welcome-icon">✦</div>
                    <h2>Qu'est-ce qu'on crée aujourd'hui ?</h2>
                    <p>Décris ton idée en français — je vais te poser quelques questions pour affiner ta vision et générer l'image parfaite.</p>
                </div>
                <div class="messages" id="messages"></div>
                <div class="progress-wrap" id="progressWrap">
                    <div class="progress-label" id="progressText">Génération en cours...</div>
                    <div class="progress-bar"><div class="progress-fill"></div></div>
                </div>
            </div>
            <div class="input-area">
                <div class="input-main">
                    <div class="input-box">
                        <textarea id="userInput" rows="1" placeholder="Décris ce que tu veux créer..."></textarea>
                        <button class="send-btn" id="sendBtn">↑</button>
                    </div>
                    <div class="input-meta">
                        <div class="neg-wrap">
                            <span class="neg-label">✕ Exclure :</span>
                            <input type="text" class="neg-input" id="negativeInput" placeholder="flou, texte, déformé...">
                        </div>
                        <button class="inspire-btn" id="inspireBtn">✦ Inspire-moi</button>
                    </div>
                </div>
            </div>
        </div>

        <!-- PAGE GALLERY -->
        <div class="page" id="page-gallery">
            <div class="page-header">
                <div>
                    <div class="page-title">Galerie</div>
                    <div class="page-subtitle">Tes créations organisées par projet</div>
                </div>
                <button class="page-btn" id="newFolderBtn">+ Nouveau dossier</button>
            </div>
            <div class="gallery-content">
                <div class="folders-row" id="foldersList"></div>
                <div class="images-grid" id="imagesGrid"></div>
            </div>
        </div>

        <!-- PAGE HISTORY -->
        <div class="page" id="page-history">
            <div class="page-header">
                <div>
                    <div class="page-title">Historique</div>
                    <div class="page-subtitle">Tes derniers prompts utilisés</div>
                </div>
                <button class="page-btn" id="clearHistoryBtn">Effacer tout</button>
            </div>
            <div class="history-content" id="historyList"></div>
        </div>
    </main>
</div>

<!-- Modal Auth -->
<div class="overlay" id="authOverlay">
    <div class="modal-box">
        <div class="modal-head">
            <div class="modal-title" id="authTitle">Connexion</div>
            <button class="modal-close" id="authCloseBtn">✕</button>
        </div>
        <div class="err-msg" id="authError"></div>
        <div class="field-label">Nom d'utilisateur</div>
        <input type="text" class="field-input" id="authUsername" placeholder="ex: johndoe" autocomplete="username">
        <div class="field-label">Mot de passe</div>
        <input type="password" class="field-input" id="authPassword" placeholder="••••••••" autocomplete="current-password">
        <div class="modal-footer">
            <button class="btn btn-ghost" id="authCancelBtn">Annuler</button>
            <button class="btn btn-orange" id="authActionBtn">Se connecter</button>
        </div>
        <div class="auth-switch">
            <span id="authSwitchText">Pas de compte ?</span>
            <span class="auth-link" id="authSwitchLink">S'inscrire</span>
        </div>
    </div>
</div>

<!-- Modal Dossier -->
<div class="overlay" id="folderOverlay">
    <div class="modal-box">
        <div class="modal-head">
            <div class="modal-title">Nouveau dossier</div>
            <button class="modal-close" id="folderCloseBtn">✕</button>
        </div>
        <div class="field-label">Nom du projet</div>
        <input type="text" class="field-input" id="folderNameInput" placeholder="ex: Paysages fantasy">
        <div class="modal-footer">
            <button class="btn btn-ghost" id="folderCancelBtn">Annuler</button>
            <button class="btn btn-orange" id="folderConfirmBtn">Créer</button>
        </div>
    </div>
</div>

<!-- Modal Sauvegarde -->
<div class="overlay" id="saveOverlay">
    <div class="modal-box">
        <div class="modal-head">
            <div class="modal-title">Sauvegarder dans...</div>
            <button class="modal-close" id="saveCloseBtn">✕</button>
        </div>
        <div class="save-folders" id="saveFoldersList"></div>
        <div class="modal-footer">
            <button class="btn btn-ghost" id="saveCancelBtn">Annuler</button>
        </div>
    </div>
</div>

<script>
// ── STATE ──
var conversation = [];
var currentFolder = null;
var selectedStyle = "";
var authMode = "login";
var currentUser = null;
var promptHistory = [];
var pendingSaveUrl = null;
var pendingSavePrompt = null;

var inspireIdeas = [
    "Un astronaute solitaire sur une planète déserte au coucher de soleil",
    "Une bibliothèque magique flottant dans les nuages",
    "Un dragon endormi dans une forêt de cristaux lumineux",
    "Une ville sous-marine habitée par des créatures de lumière",
    "Un chat géant gardant une cité médiévale",
    "Une forêt enchantée où les arbres brillent comme des étoiles",
    "Un robot artiste peignant au milieu du désert",
    "Une île volante avec une cascade qui tombe dans les nuages"
];

// ── INIT ──
window.addEventListener('load', function() {
    try { promptHistory = JSON.parse(localStorage.getItem('astax_history') || '[]'); } catch(e) { promptHistory = []; }

    // Nav
    document.getElementById('nav-chat').addEventListener('click', function() { showPage('chat'); });
    document.getElementById('nav-gallery').addEventListener('click', function() { showPage('gallery'); });
    document.getElementById('nav-history').addEventListener('click', function() { showPage('history'); });

    // Send
    document.getElementById('sendBtn').addEventListener('click', envoyer);
    document.getElementById('userInput').addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); envoyer(); }
    });
    document.getElementById('userInput').addEventListener('input', function() { autoResize(this); });

    // Inspire
    document.getElementById('inspireBtn').addEventListener('click', inspire);

    // Gallery
    document.getElementById('newFolderBtn').addEventListener('click', openCreateFolder);

    // History
    document.getElementById('clearHistoryBtn').addEventListener('click', clearHistory);

    // Auth modal
    document.getElementById('authCloseBtn').addEventListener('click', function() { closeOverlay('authOverlay'); });
    document.getElementById('authCancelBtn').addEventListener('click', function() { closeOverlay('authOverlay'); });
    document.getElementById('authActionBtn').addEventListener('click', authAction);
    document.getElementById('authSwitchLink').addEventListener('click', toggleAuthMode);
    document.getElementById('authPassword').addEventListener('keydown', function(e) { if (e.key === 'Enter') authAction(); });

    // Folder modal
    document.getElementById('folderCloseBtn').addEventListener('click', function() { closeOverlay('folderOverlay'); });
    document.getElementById('folderCancelBtn').addEventListener('click', function() { closeOverlay('folderOverlay'); });
    document.getElementById('folderConfirmBtn').addEventListener('click', createFolder);
    document.getElementById('folderNameInput').addEventListener('keydown', function(e) { if (e.key === 'Enter') createFolder(); });

    // Save modal
    document.getElementById('saveCloseBtn').addEventListener('click', function() { closeOverlay('saveOverlay'); });
    document.getElementById('saveCancelBtn').addEventListener('click', function() { closeOverlay('saveOverlay'); });

    // User card
    document.getElementById('userCard').addEventListener('click', userCardClick);

    // Check session
    fetch('/me').then(function(r) { return r.json(); }).then(function(data) {
        if (data.username) {
            setLoggedIn(data.username);
            if (data.prompt_history && data.prompt_history.length) promptHistory = data.prompt_history;
        }
    });
});

// ── UTILS ──
function autoResize(el) {
    el.style.height = 'auto';
    el.style.height = Math.min(el.scrollHeight, 120) + 'px';
}

function showPage(page) {
    document.querySelectorAll('.page').forEach(function(p) { p.classList.remove('active'); });
    document.querySelectorAll('.nav-item').forEach(function(n) { n.classList.remove('active'); });
    document.getElementById('page-' + page).classList.add('active');
    document.getElementById('nav-' + page).classList.add('active');
    if (page === 'gallery') loadGallery();
    if (page === 'history') loadHistory();
}

function selectStyle(el, style) {
    document.querySelectorAll('.style-chip').forEach(function(c) { c.classList.remove('selected'); });
    el.classList.add('selected');
    selectedStyle = style;
}

function inspire() {
    var idea = inspireIdeas[Math.floor(Math.random() * inspireIdeas.length)];
    var input = document.getElementById('userInput');
    input.value = idea;
    autoResize(input);
}

function addMessage(role, text) {
    var welcome = document.getElementById('welcomeMsg');
    if (welcome) welcome.style.display = 'none';
    var messages = document.getElementById('messages');
    var row = document.createElement('div');
    row.className = 'msg-row ' + role;
    var avatar = document.createElement('div');
    avatar.className = 'msg-avatar ' + role;
    avatar.innerText = role === 'bot' ? '✦' : '✎';
    var bubble = document.createElement('div');
    bubble.className = 'msg-bubble ' + role;
    bubble.innerText = text;
    row.appendChild(avatar);
    row.appendChild(bubble);
    messages.appendChild(row);
    document.getElementById('chatArea').scrollTop = 99999;
}

function addImageToChat(imgUrl, prompt, count, index) {
    var messages = document.getElementById('messages');
    var wrap = document.createElement('div');
    wrap.className = 'gen-wrap';
    var img = document.createElement('img');
    img.src = imgUrl;
    var actions = document.createElement('div');
    actions.className = 'gen-actions';
    var dlBtn = document.createElement('a');
    dlBtn.href = imgUrl;
    dlBtn.download = 'astax-' + Date.now() + '.png';
    dlBtn.className = 'gen-btn';
    dlBtn.innerText = '⬇ Télécharger';
    var saveBtn = document.createElement('button');
    saveBtn.className = 'gen-btn primary';
    saveBtn.innerText = '💾 Sauvegarder';
    var capturedUrl = imgUrl;
    var capturedPrompt = prompt;
    saveBtn.addEventListener('click', function() {
        if (!currentUser) { addMessage('bot', '⚠️ Connecte-toi pour sauvegarder tes images !'); return; }
        pendingSaveUrl = capturedUrl;
        pendingSavePrompt = capturedPrompt;
        openSaveModal();
    });
    if (count > 1) {
        var label = document.createElement('span');
        label.style.cssText = 'font-size:0.76em;color:var(--text-dim);align-self:center;';
        label.innerText = 'Image ' + (index + 1) + '/' + count;
        actions.appendChild(label);
    }
    actions.appendChild(dlBtn);
    actions.appendChild(saveBtn);
    wrap.appendChild(img);
    wrap.appendChild(actions);
    messages.appendChild(wrap);
    document.getElementById('chatArea').scrollTop = 99999;
}

// ── CHAT ──
function envoyer() {
    var input = document.getElementById('userInput');
    var text = input.value.trim();
    if (!text) return;
    addMessage('user', text);
    conversation.push({role: 'user', content: text});
    input.value = '';
    input.style.height = 'auto';

    fetch('/chat', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({messages: conversation, style: selectedStyle})
    }).then(function(r) { return r.json(); }).then(function(data) {
        if (data.type === 'question') {
            addMessage('bot', data.message);
            conversation.push({role: 'assistant', content: data.message});
        } else if (data.type === 'generate') {
            addMessage('bot', data.message);
            conversation.push({role: 'assistant', content: data.message});
            addToHistory(data.prompt);
            var count = data.count || 1;
            var negPrompt = document.getElementById('negativeInput').value.trim();
            var progress = document.getElementById('progressWrap');
            var progressText = document.getElementById('progressText');
            progress.style.display = 'block';
            var i = 0;
            function genNext() {
                if (i >= count) { progress.style.display = 'none'; conversation = []; return; }
                progressText.innerText = count > 1 ? 'Génération ' + (i+1) + ' sur ' + count + '...' : 'Génération en cours...';
                fetch('/generate', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({prompt: data.prompt, negative_prompt: negPrompt, style: selectedStyle})
                }).then(function(r) { return r.blob(); }).then(function(blob) {
                    addImageToChat(URL.createObjectURL(blob), data.prompt, count, i);
                    i++;
                    genNext();
                });
            }
            genNext();
        }
    });
}

// ── HISTORY ──
function addToHistory(prompt) {
    promptHistory = [prompt].concat(promptHistory.filter(function(p) { return p !== prompt; })).slice(0, 20);
    try { localStorage.setItem('astax_history', JSON.stringify(promptHistory)); } catch(e) {}
    if (currentUser) {
        fetch('/save-history', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({history: promptHistory})});
    }
}

function loadHistory() {
    var list = document.getElementById('historyList');
    list.innerHTML = '';
    if (!promptHistory.length) {
        list.innerHTML = '<div class="empty-state"><div class="empty-icon">↺</div><p>Aucun prompt encore.<br>Génère ta première image !</p></div>';
        return;
    }
    promptHistory.forEach(function(p) {
        var item = document.createElement('div');
        item.className = 'history-item';
        var text = document.createElement('span');
        text.className = 'history-text';
        text.innerText = p;
        var btn = document.createElement('button');
        btn.className = 'history-reuse';
        btn.innerText = 'Réutiliser';
        var captured = p;
        btn.addEventListener('click', function() { reusePrompt(captured); });
        item.appendChild(text);
        item.appendChild(btn);
        list.appendChild(item);
    });
}

function clearHistory() {
    promptHistory = [];
    try { localStorage.removeItem('astax_history'); } catch(e) {}
    loadHistory();
}

function reusePrompt(prompt) {
    var input = document.getElementById('userInput');
    input.value = prompt;
    autoResize(input);
    showPage('chat');
}

// ── GALLERY ──
function loadGallery() {
    if (!currentUser) {
        document.getElementById('foldersList').innerHTML = '<div class="empty-state" style="width:100%"><div class="empty-icon">🔒</div><p>Connecte-toi pour accéder à ta galerie</p></div>';
        document.getElementById('imagesGrid').innerHTML = '';
        return;
    }
    fetch('/galleries').then(function(r) { return r.json(); }).then(function(data) {
        var fList = document.getElementById('foldersList');
        var iGrid = document.getElementById('imagesGrid');
        fList.innerHTML = '';
        iGrid.innerHTML = '';
        var keys = Object.keys(data);
        if (!keys.length) {
            fList.innerHTML = '<div class="empty-state" style="width:100%"><div class="empty-icon">⊞</div><p>Aucun dossier encore.<br>Crée ton premier projet !</p></div>';
            return;
        }
        keys.forEach(function(name) {
            var pill = document.createElement('div');
            pill.className = 'folder-pill' + (currentFolder === name ? ' active' : '');
            pill.innerHTML = '📁 ' + name + ' <span class="folder-badge">' + data[name].length + '</span>';
            var captured = name;
            pill.addEventListener('click', function() { currentFolder = captured; loadGallery(); });
            fList.appendChild(pill);
        });
        if (currentFolder && data[currentFolder]) {
            data[currentFolder].forEach(function(img) {
                var card = document.createElement('div');
                card.className = 'img-card';
                var imgEl = document.createElement('img');
                imgEl.src = img.image_b64;
                var info = document.createElement('div');
                info.className = 'img-card-info';
                var promptEl = document.createElement('div');
                promptEl.className = 'img-card-prompt';
                promptEl.innerText = img.prompt;
                var actionsEl = document.createElement('div');
                actionsEl.className = 'img-card-actions';
                var dlA = document.createElement('a');
                dlA.href = img.image_b64;
                dlA.download = 'astax.png';
                dlA.className = 'img-action';
                dlA.innerText = '⬇';
                var delBtn = document.createElement('button');
                delBtn.className = 'img-action';
                delBtn.innerText = '✕';
                var capturedFolder = currentFolder;
                var capturedId = img.id;
                delBtn.addEventListener('click', function() { deleteImage(capturedFolder, capturedId); });
                actionsEl.appendChild(dlA);
                actionsEl.appendChild(delBtn);
                info.appendChild(promptEl);
                info.appendChild(actionsEl);
                card.appendChild(imgEl);
                card.appendChild(info);
                iGrid.appendChild(card);
            });
        }
    });
}

function openCreateFolder() {
    if (!currentUser) { addMessage('bot', '⚠️ Connecte-toi pour créer des dossiers !'); showPage('chat'); return; }
    document.getElementById('folderNameInput').value = '';
    openOverlay('folderOverlay');
    document.getElementById('folderNameInput').focus();
}

function createFolder() {
    var name = document.getElementById('folderNameInput').value.trim();
    if (!name) return;
    fetch('/create-folder', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({name: name})})
    .then(function() { closeOverlay('folderOverlay'); loadGallery(); });
}

function openSaveModal() {
    fetch('/galleries').then(function(r) { return r.json(); }).then(function(data) {
        var list = document.getElementById('saveFoldersList');
        list.innerHTML = '';
        var keys = Object.keys(data);
        if (!keys.length) {
            list.innerHTML = '<span style="font-size:0.82em;color:var(--text-dim)">Aucun dossier — crée-en un dans la galerie !</span>';
        } else {
            keys.forEach(function(name) {
                var btn = document.createElement('button');
                btn.className = 'save-folder-btn';
                btn.innerText = '📁 ' + name;
                var captured = name;
                btn.addEventListener('click', function() { saveImageToFolder(captured); });
                list.appendChild(btn);
            });
        }
        openOverlay('saveOverlay');
    });
}

function saveImageToFolder(folder) {
    fetch(pendingSaveUrl).then(function(r) { return r.blob(); }).then(function(blob) {
        var reader = new FileReader();
        reader.onloadend = function() {
            fetch('/save-image', {
                method:'POST',
                headers:{'Content-Type':'application/json'},
                body: JSON.stringify({folder: folder, image_b64: reader.result, prompt: pendingSavePrompt})
            }).then(function() {
                closeOverlay('saveOverlay');
                addMessage('bot', '✅ Image sauvegardée dans "' + folder + '" !');
            });
        };
        reader.readAsDataURL(blob);
    });
}

function deleteImage(folder, id) {
    fetch('/delete-image', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({folder: folder, id: id})})
    .then(function() { loadGallery(); });
}

// ── MODALS ──
function openOverlay(id) { document.getElementById(id).classList.add('open'); }
function closeOverlay(id) { document.getElementById(id).classList.remove('open'); }

// ── AUTH ──
function userCardClick() {
    if (currentUser) { logout(); } else { openAuthModal(); }
}

function openAuthModal() {
    authMode = 'login';
    document.getElementById('authTitle').innerText = 'Connexion';
    document.getElementById('authActionBtn').innerText = 'Se connecter';
    document.getElementById('authSwitchText').innerText = 'Pas de compte ?';
    document.getElementById('authSwitchLink').innerText = "S'inscrire";
    document.getElementById('authError').style.display = 'none';
    document.getElementById('authUsername').value = '';
    document.getElementById('authPassword').value = '';
    openOverlay('authOverlay');
    document.getElementById('authUsername').focus();
}

function toggleAuthMode() {
    authMode = authMode === 'login' ? 'register' : 'login';
    var isLogin = authMode === 'login';
    document.getElementById('authTitle').innerText = isLogin ? 'Connexion' : 'Inscription';
    document.getElementById('authActionBtn').innerText = isLogin ? 'Se connecter' : "S'inscrire";
    document.getElementById('authSwitchText').innerText = isLogin ? 'Pas de compte ?' : 'Déjà un compte ?';
    document.getElementById('authSwitchLink').innerText = isLogin ? "S'inscrire" : 'Se connecter';
    document.getElementById('authError').style.display = 'none';
}

function authAction() {
    var username = document.getElementById('authUsername').value.trim();
    var password = document.getElementById('authPassword').value;
    if (!username || !password) return;
    var endpoint = authMode === 'login' ? '/login' : '/register';
    fetch(endpoint, {
        method:'POST',
        headers:{'Content-Type':'application/json'},
        body: JSON.stringify({username: username, password: password})
    }).then(function(r) { return r.json(); }).then(function(data) {
        if (data.success) {
            setLoggedIn(username);
            if (data.prompt_history) promptHistory = data.prompt_history;
            closeOverlay('authOverlay');
            addMessage('bot', authMode === 'login' ? '✅ Bon retour ' + username + ' !' : '🎉 Bienvenue ' + username + ' !');
        } else {
            var err = document.getElementById('authError');
            err.innerText = data.error;
            err.style.display = 'block';
        }
    });
}

function setLoggedIn(username) {
    currentUser = username;
    document.getElementById('userAvatar').innerText = username[0].toUpperCase();
    document.getElementById('userName').innerText = username;
    document.getElementById('userStatus').innerText = 'Connecté — cliquer pour déconnecter';
}

function logout() {
    fetch('/logout', {method:'POST'}).then(function() {
        currentUser = null;
        document.getElementById('userAvatar').innerText = '?';
        document.getElementById('userName').innerText = 'Mode invité';
        document.getElementById('userStatus').innerText = 'Cliquer pour se connecter';
        try { promptHistory = JSON.parse(localStorage.getItem('astax_history') || '[]'); } catch(e) { promptHistory = []; }
        addMessage('bot', 'Tu es maintenant déconnecté. À bientôt ! 👋');
    });
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
    style_hint = " Le style visuel choisi : " + style + "." if style else ""

    system = """Tu es un assistant créatif qui aide les utilisateurs à créer des images avec une IA.""" + style_hint + """

Pose des questions précises en français, puis génère un prompt détaillé en anglais.

Règles :
- UNE seule question à la fois
- Maximum 3-4 questions
- Avant de générer, demande : "Combien d'images souhaitez-vous ? (1 à 5)"
- Quand tu as tout, réponds EXACTEMENT ainsi (sur des lignes séparées) :
  GENERATE: [prompt anglais très détaillé]
  COUNT: [nombre 1-5]
  MESSAGE: [courte annonce en français]"""

    response = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        max_tokens=500,
        messages=[{"role": "system", "content": system}] + messages
    )
    text = response.choices[0].message.content

    if "GENERATE:" in text:
        lines = text.split("\n")
        prompt, count, message = "", 1, "Génération en cours ✨"
        for line in lines:
            if line.startswith("GENERATE:"):
                prompt = line.replace("GENERATE:", "").strip()
            elif line.startswith("COUNT:"):
                try: count = max(1, min(5, int(line.replace("COUNT:", "").strip())))
                except: count = 1
            elif line.startswith("MESSAGE:"):
                message = line.replace("MESSAGE:", "").strip()
        return jsonify({"type": "generate", "prompt": prompt, "count": count, "message": message})
    return jsonify({"type": "question", "message": text})

@app.route("/generate", methods=["POST"])
def generate():
    data = request.json
    prompt = data.get("prompt", "a beautiful landscape")
    negative_prompt = data.get("negative_prompt", "")
    style = data.get("style", "")
    full_prompt = prompt + ", " + style if style else prompt
    result = hf_client.text_to_image(
        full_prompt,
        model="stabilityai/stable-diffusion-xl-base-1.0",
        negative_prompt=negative_prompt or None
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
    if len(password) < 6:
        return jsonify({"success": False, "error": "Mot de passe trop court (6 caractères min)."})
    if username in users:
        return jsonify({"success": False, "error": "Nom d'utilisateur déjà pris."})
    users[username] = {"password_hash": hash_password(password), "galleries": {}, "prompt_history": []}
    session["username"] = username
    return jsonify({"success": True})

@app.route("/login", methods=["POST"])
def login():
    data = request.json
    username = data.get("username", "").strip()
    password = data.get("password", "")
    if username not in users:
        return jsonify({"success": False, "error": "Utilisateur introuvable."})
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
    if not username:
        return jsonify({"success": False})
    name = request.json.get("name", "").strip()
    if name and name not in users[username]["galleries"]:
        users[username]["galleries"][name] = []
    return jsonify({"success": True})

@app.route("/save-image", methods=["POST"])
def save_image():
    username = session.get("username")
    if not username:
        return jsonify({"success": False})
    data = request.json
    folder = data.get("folder")
    if folder in users[username]["galleries"]:
        users[username]["galleries"][folder].append({
            "id": str(uuid.uuid4()),
            "image_b64": data.get("image_b64"),
            "prompt": data.get("prompt", "")
        })
    return jsonify({"success": True})

@app.route("/delete-image", methods=["POST"])
def delete_image():
    username = session.get("username")
    if not username:
        return jsonify({"success": False})
    data = request.json
    folder = data.get("folder")
    image_id = data.get("id")
    if folder in users[username]["galleries"]:
        users[username]["galleries"][folder] = [
            i for i in users[username]["galleries"][folder]
            if str(i["id"]) != str(image_id)
        ]
    return jsonify({"success": True})

@app.route("/save-history", methods=["POST"])
def save_history():
    username = session.get("username")
    if username and username in users:
        users[username]["prompt_history"] = request.json.get("history", [])
    return jsonify({"success": True})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=7860)
