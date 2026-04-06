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

users = {}

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

@app.route("/")
def home():
    return """
<!DOCTYPE html>
<html lang="fr">
<head>
    <title>Astax — Generative AI</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        * { box-sizing:border-box; margin:0; padding:0; }

        :root {
            --bg: #1a1a1a;
            --bg2: #212121;
            --bg3: #2a2a2a;
            --border: rgba(255,255,255,0.08);
            --border-hover: rgba(255,165,0,0.3);
            --orange: #ff8c00;
            --orange-light: #ffa500;
            --orange-dim: rgba(255,140,0,0.12);
            --text: #ececec;
            --text-dim: rgba(255,255,255,0.45);
            --text-dimmer: rgba(255,255,255,0.25);
            --radius: 12px;
            --radius-sm: 8px;
        }

        body {
            background: var(--bg);
            color: var(--text);
            font-family: 'Inter', sans-serif;
            height: 100vh;
            display: flex;
            flex-direction: column;
            overflow: hidden;
            font-size: 14px;
        }

        /* ─── SIDEBAR ─── */
        .layout { display:flex; flex:1; overflow:hidden; }

        .sidebar {
            width: 260px;
            background: var(--bg2);
            border-right: 1px solid var(--border);
            display: flex;
            flex-direction: column;
            padding: 20px 0;
            flex-shrink: 0;
        }

        .logo-area { padding: 0 20px 24px; border-bottom: 1px solid var(--border); margin-bottom: 16px; }

        .logo {
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .logo-icon {
            width: 36px;
            height: 36px;
            background: linear-gradient(135deg, var(--orange), #ff4500);
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 18px;
            flex-shrink: 0;
            box-shadow: 0 4px 12px rgba(255,140,0,0.3);
        }

        .logo-text { font-weight: 700; font-size: 1.15em; letter-spacing: 0.5px; }
        .logo-sub { font-size: 0.7em; color: var(--text-dim); font-weight: 400; margin-top: 1px; }

        .nav-section { padding: 0 12px; flex:1; }
        .nav-label { font-size: 0.65em; color: var(--text-dimmer); letter-spacing: 1.5px; text-transform: uppercase; padding: 0 8px; margin-bottom: 6px; font-weight: 600; }

        .nav-item {
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 9px 10px;
            border-radius: var(--radius-sm);
            cursor: pointer;
            color: var(--text-dim);
            font-size: 0.9em;
            font-weight: 500;
            transition: all 0.2s;
            margin-bottom: 2px;
            border: 1px solid transparent;
        }

        .nav-item:hover { background: var(--bg3); color: var(--text); }
        .nav-item.active { background: var(--orange-dim); color: var(--orange-light); border-color: rgba(255,140,0,0.15); }
        .nav-item .icon { font-size: 1em; width: 20px; text-align: center; }

        .nav-divider { height: 1px; background: var(--border); margin: 12px 8px; }

        /* Styles rapides dans sidebar */
        .styles-section { padding: 0 12px; margin-top: 8px; }
        .style-chip {
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 7px 10px;
            border-radius: var(--radius-sm);
            cursor: pointer;
            color: var(--text-dim);
            font-size: 0.85em;
            transition: all 0.2s;
            margin-bottom: 2px;
        }
        .style-chip:hover { background: var(--bg3); color: var(--text); }
        .style-chip.selected { color: var(--orange-light); background: var(--orange-dim); }

        /* User area */
        .user-area {
            padding: 16px 12px 0;
            border-top: 1px solid var(--border);
            margin-top: auto;
        }

        .user-card {
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 10px;
            border-radius: var(--radius-sm);
            background: var(--bg3);
            cursor: pointer;
            transition: all 0.2s;
        }
        .user-card:hover { background: rgba(255,255,255,0.05); }
        .user-avatar {
            width: 32px; height: 32px;
            background: linear-gradient(135deg, var(--orange), #ff4500);
            border-radius: 50%;
            display: flex; align-items: center; justify-content: center;
            font-size: 0.85em; font-weight: 700; flex-shrink: 0;
        }
        .user-name { font-weight: 500; font-size: 0.88em; }
        .user-status { font-size: 0.72em; color: var(--text-dim); }

        /* ─── MAIN CONTENT ─── */
        .main { flex:1; display:flex; flex-direction:column; overflow:hidden; }

        /* Pages */
        .page { display:none; flex:1; flex-direction:column; overflow:hidden; }
        .page.active { display:flex; }

        /* ─── CHAT PAGE ─── */
        .chat-area { flex:1; overflow-y:auto; padding:32px; }
        .chat-area::-webkit-scrollbar { width:5px; }
        .chat-area::-webkit-scrollbar-thumb { background:rgba(255,255,255,0.1); border-radius:3px; }

        .chat-welcome {
            text-align: center;
            padding: 60px 20px 40px;
        }
        .chat-welcome .welcome-icon {
            width: 56px; height: 56px;
            background: linear-gradient(135deg, var(--orange), #ff4500);
            border-radius: 16px;
            display: flex; align-items: center; justify-content: center;
            font-size: 24px;
            margin: 0 auto 16px;
            box-shadow: 0 8px 24px rgba(255,140,0,0.25);
        }
        .chat-welcome h2 { font-size: 1.4em; font-weight: 600; margin-bottom: 8px; }
        .chat-welcome p { color: var(--text-dim); font-size: 0.9em; line-height: 1.6; max-width: 400px; margin: 0 auto; }

        .messages { display:flex; flex-direction:column; gap:16px; max-width:720px; margin:0 auto; width:100%; }

        .msg-row { display:flex; gap:12px; align-items:flex-start; }
        .msg-row.user { flex-direction:row-reverse; }

        .msg-avatar {
            width: 32px; height: 32px; border-radius: 50%;
            display: flex; align-items: center; justify-content: center;
            font-size: 0.8em; font-weight: 700; flex-shrink: 0; margin-top: 2px;
        }
        .msg-avatar.bot { background: linear-gradient(135deg, var(--orange), #ff4500); }
        .msg-avatar.user { background: var(--bg3); border: 1px solid var(--border); }

        .msg-bubble {
            padding: 12px 16px;
            border-radius: var(--radius);
            max-width: 75%;
            line-height: 1.6;
            font-size: 0.92em;
        }
        .msg-bubble.bot { background: var(--bg3); border: 1px solid var(--border); color: var(--text); border-top-left-radius: 4px; }
        .msg-bubble.user { background: var(--orange-dim); border: 1px solid rgba(255,140,0,0.2); color: var(--text); border-top-right-radius: 4px; }

        /* Progress */
        .progress-wrap {
            display: none;
            max-width: 720px; margin: 0 auto;
            padding: 16px;
            background: var(--bg3);
            border: 1px solid var(--border);
            border-radius: var(--radius);
        }
        .progress-label { font-size: 0.8em; color: var(--text-dim); margin-bottom: 10px; display:flex; justify-content:space-between; }
        .progress-bar { height: 3px; background: rgba(255,255,255,0.06); border-radius: 2px; overflow:hidden; }
        .progress-fill { height:100%; background: linear-gradient(90deg, var(--orange), #ff4500); animation: prog 1.8s ease-in-out infinite; }
        @keyframes prog { 0%{width:0%;margin-left:0} 50%{width:70%;margin-left:0} 100%{width:0%;margin-left:100%} }

        /* Generated image */
        .gen-image-wrap {
            max-width: 720px; margin: 0 auto;
            animation: fadeUp 0.4s ease;
        }
        @keyframes fadeUp { from{opacity:0;transform:translateY(12px)} to{opacity:1;transform:translateY(0)} }

        .gen-image-wrap img {
            width: 100%;
            max-width: 512px;
            border-radius: var(--radius);
            border: 1px solid var(--border);
            display: block;
        }

        .gen-actions {
            display: flex; gap: 8px; margin-top: 10px; flex-wrap:wrap;
        }

        .gen-btn {
            padding: 7px 14px;
            border-radius: var(--radius-sm);
            font-size: 0.8em;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.2s;
            font-family: 'Inter', sans-serif;
            border: 1px solid var(--border);
            background: var(--bg3);
            color: var(--text-dim);
        }
        .gen-btn:hover { color: var(--text); border-color: rgba(255,255,255,0.15); }
        .gen-btn.primary { background: var(--orange-dim); border-color: rgba(255,140,0,0.25); color: var(--orange-light); }
        .gen-btn.primary:hover { background: rgba(255,140,0,0.2); }

        /* ─── INPUT AREA ─── */
        .input-area {
            padding: 16px 32px 20px;
            border-top: 1px solid var(--border);
            background: var(--bg);
        }

        .input-main {
            max-width: 720px; margin: 0 auto;
        }

        .input-box {
            display: flex;
            align-items: flex-end;
            gap: 10px;
            background: var(--bg2);
            border: 1px solid var(--border);
            border-radius: var(--radius);
            padding: 10px 12px;
            transition: border-color 0.2s;
        }
        .input-box:focus-within { border-color: rgba(255,140,0,0.4); }

        textarea {
            flex:1;
            background: transparent;
            border: none;
            outline: none;
            color: var(--text);
            font-family: 'Inter', sans-serif;
            font-size: 0.92em;
            resize: none;
            max-height: 120px;
            line-height: 1.5;
            padding: 2px 0;
        }
        textarea::placeholder { color: var(--text-dimmer); }

        .send-btn {
            width: 36px; height: 36px;
            background: var(--orange);
            border: none;
            border-radius: var(--radius-sm);
            color: white;
            font-size: 1em;
            cursor: pointer;
            transition: all 0.2s;
            display: flex; align-items: center; justify-content: center;
            flex-shrink: 0;
        }
        .send-btn:hover { background: var(--orange-light); transform: scale(1.05); }

        .input-meta {
            display: flex;
            gap: 10px;
            margin-top: 8px;
            align-items: center;
            flex-wrap: wrap;
        }

        .negative-wrap {
            flex: 1;
            display: flex;
            align-items: center;
            gap: 6px;
            background: var(--bg2);
            border: 1px solid var(--border);
            border-radius: var(--radius-sm);
            padding: 6px 10px;
        }
        .negative-wrap:focus-within { border-color: rgba(255,80,80,0.3); }
        .negative-label { font-size: 0.72em; color: rgba(255,100,100,0.6); white-space: nowrap; font-weight: 500; }
        .negative-input { background:transparent; border:none; outline:none; color:var(--text); font-family:'Inter',sans-serif; font-size:0.82em; flex:1; }
        .negative-input::placeholder { color: var(--text-dimmer); }

        .inspire-btn {
            padding: 6px 12px;
            background: transparent;
            border: 1px solid var(--border);
            border-radius: var(--radius-sm);
            color: var(--text-dim);
            font-size: 0.78em;
            cursor: pointer;
            transition: all 0.2s;
            white-space: nowrap;
            font-family: 'Inter', sans-serif;
        }
        .inspire-btn:hover { border-color: var(--border-hover); color: var(--orange-light); background: var(--orange-dim); }

        /* ─── GALLERY PAGE ─── */
        .page-header {
            padding: 24px 32px 16px;
            border-bottom: 1px solid var(--border);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .page-title { font-size: 1.1em; font-weight: 600; }
        .page-subtitle { font-size: 0.82em; color: var(--text-dim); margin-top: 2px; }

        .page-action-btn {
            padding: 8px 16px;
            background: var(--orange-dim);
            border: 1px solid rgba(255,140,0,0.2);
            border-radius: var(--radius-sm);
            color: var(--orange-light);
            font-size: 0.82em;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.2s;
            font-family: 'Inter', sans-serif;
        }
        .page-action-btn:hover { background: rgba(255,140,0,0.2); }

        .gallery-content { flex:1; overflow-y:auto; padding: 20px 32px; }
        .gallery-content::-webkit-scrollbar { width:5px; }
        .gallery-content::-webkit-scrollbar-thumb { background:rgba(255,255,255,0.1); border-radius:3px; }

        .folders-row { display:flex; flex-wrap:wrap; gap:10px; margin-bottom:24px; }

        .folder-pill {
            display: flex;
            align-items: center;
            gap: 6px;
            padding: 7px 14px;
            border-radius: 20px;
            border: 1px solid var(--border);
            cursor: pointer;
            font-size: 0.82em;
            color: var(--text-dim);
            transition: all 0.2s;
        }
        .folder-pill:hover { border-color: var(--border-hover); color: var(--text); }
        .folder-pill.active { background: var(--orange-dim); border-color: rgba(255,140,0,0.3); color: var(--orange-light); }
        .folder-count-badge { background: rgba(255,255,255,0.08); border-radius: 10px; padding: 1px 7px; font-size: 0.85em; }

        .images-grid { display:grid; grid-template-columns:repeat(auto-fill, minmax(180px, 1fr)); gap:12px; }

        .img-card {
            border-radius: var(--radius);
            overflow: hidden;
            border: 1px solid var(--border);
            background: var(--bg2);
            transition: all 0.2s;
            cursor: pointer;
        }
        .img-card:hover { border-color: var(--border-hover); transform: translateY(-2px); box-shadow: 0 8px 24px rgba(0,0,0,0.3); }
        .img-card img { width:100%; height:160px; object-fit:cover; display:block; }
        .img-card-info { padding: 10px; }
        .img-card-prompt { font-size: 0.75em; color: var(--text-dim); white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
        .img-card-actions { display:flex; gap:5px; margin-top:7px; }
        .img-action { flex:1; padding:4px; text-align:center; border-radius:5px; border:1px solid var(--border); font-size:0.7em; color:var(--text-dim); cursor:pointer; transition:all 0.2s; background:transparent; font-family:'Inter',sans-serif; text-decoration:none; display:flex; align-items:center; justify-content:center; }
        .img-action:hover { background: var(--bg3); color: var(--text); }

        /* ─── HISTORY PAGE ─── */
        .history-content { flex:1; overflow-y:auto; padding: 20px 32px; }
        .history-item {
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 12px 16px;
            border-radius: var(--radius);
            border: 1px solid var(--border);
            background: var(--bg2);
            margin-bottom: 8px;
            transition: all 0.2s;
            cursor: default;
        }
        .history-item:hover { border-color: var(--border-hover); }
        .history-icon { color: var(--text-dimmer); font-size: 0.9em; flex-shrink: 0; }
        .history-text { flex:1; font-size: 0.88em; color: var(--text-dim); }
        .history-reuse {
            padding: 5px 12px;
            border-radius: var(--radius-sm);
            border: 1px solid var(--border);
            background: transparent;
            color: var(--text-dim);
            font-size: 0.75em;
            cursor: pointer;
            transition: all 0.2s;
            font-family: 'Inter', sans-serif;
            flex-shrink: 0;
        }
        .history-reuse:hover { background: var(--orange-dim); border-color: rgba(255,140,0,0.3); color: var(--orange-light); }

        /* ─── MODALS ─── */
        .overlay { display:none; position:fixed; inset:0; background:rgba(0,0,0,0.6); z-index:200; justify-content:center; align-items:center; backdrop-filter:blur(4px); }
        .overlay.active { display:flex; }

        .modal-box {
            background: var(--bg2);
            border: 1px solid var(--border);
            border-radius: 16px;
            padding: 28px;
            width: 380px;
            max-width: 90vw;
            animation: modalIn 0.2s ease;
        }
        @keyframes modalIn { from{opacity:0;transform:scale(0.96)} to{opacity:1;transform:scale(1)} }

        .modal-head { display:flex; justify-content:space-between; align-items:center; margin-bottom:20px; }
        .modal-title { font-size: 1em; font-weight: 600; }
        .modal-close { background:none; border:none; color:var(--text-dim); font-size:1.2em; cursor:pointer; padding:2px; }
        .modal-close:hover { color:var(--text); }

        .field-label { font-size: 0.78em; color: var(--text-dim); margin-bottom: 6px; font-weight: 500; }
        .field-input {
            width: 100%;
            padding: 10px 12px;
            background: var(--bg3);
            border: 1px solid var(--border);
            border-radius: var(--radius-sm);
            color: var(--text);
            font-family: 'Inter', sans-serif;
            font-size: 0.88em;
            outline: none;
            margin-bottom: 14px;
            transition: border-color 0.2s;
        }
        .field-input:focus { border-color: rgba(255,140,0,0.4); }

        .modal-footer { display:flex; gap:8px; margin-top:6px; }
        .btn { flex:1; padding:10px; border-radius:var(--radius-sm); font-family:'Inter',sans-serif; font-size:0.82em; font-weight:500; cursor:pointer; transition:all 0.2s; border:none; }
        .btn-ghost { background:var(--bg3); color:var(--text-dim); border:1px solid var(--border); }
        .btn-ghost:hover { color:var(--text); }
        .btn-orange { background:var(--orange); color:white; }
        .btn-orange:hover { background:var(--orange-light); }

        .auth-switch { text-align:center; margin-top:14px; font-size:0.8em; color:var(--text-dim); }
        .auth-switch span { color:var(--orange-light); cursor:pointer; }
        .auth-switch span:hover { text-decoration:underline; }

        .error-msg { font-size:0.78em; color:#ff6b6b; margin-bottom:10px; display:none; padding:8px 10px; background:rgba(255,100,100,0.08); border-radius:var(--radius-sm); border:1px solid rgba(255,100,100,0.15); }

        .save-folders { display:flex; flex-wrap:wrap; gap:8px; margin-bottom:14px; }
        .save-folder-btn { padding:8px 14px; background:var(--bg3); border:1px solid var(--border); border-radius:var(--radius-sm); color:var(--text-dim); font-size:0.82em; cursor:pointer; transition:all 0.2s; font-family:'Inter',sans-serif; }
        .save-folder-btn:hover { border-color:var(--border-hover); color:var(--orange-light); background:var(--orange-dim); }

        .empty-state { text-align:center; padding:60px 20px; color:var(--text-dimmer); }
        .empty-state .empty-icon { font-size:2.5em; margin-bottom:12px; }
        .empty-state p { font-size:0.88em; line-height:1.6; }
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
            <div class="nav-item active" onclick="showPage('chat', this)">
                <span class="icon">✦</span> Créer
            </div>
            <div class="nav-item" onclick="showPage('gallery', this)">
                <span class="icon">⊞</span> Galerie
            </div>
            <div class="nav-item" onclick="showPage('history', this)">
                <span class="icon">↺</span> Historique
            </div>

            <div class="nav-divider"></div>
            <div class="nav-label">Style rapide</div>
        </div>

        <div class="styles-section">
            <div class="style-chip selected" onclick="selectStyle(this, '')">
                <span>◈</span> Auto
            </div>
            <div class="style-chip" onclick="selectStyle(this, 'photorealistic, ultra detailed, 8k photography')">
                <span>📷</span> Réaliste
            </div>
            <div class="style-chip" onclick="selectStyle(this, 'anime style, manga, vibrant, studio ghibli')">
                <span>🎌</span> Anime
            </div>
            <div class="style-chip" onclick="selectStyle(this, 'oil painting, artistic brushstrokes, renaissance')">
                <span>🎨</span> Peinture
            </div>
            <div class="style-chip" onclick="selectStyle(this, 'pixel art, 16-bit retro game style')">
                <span>👾</span> Pixel Art
            </div>
            <div class="style-chip" onclick="selectStyle(this, 'cyberpunk, neon lights, futuristic dark city')">
                <span>🌆</span> Cyberpunk
            </div>
            <div class="style-chip" onclick="selectStyle(this, 'watercolor, soft dreamy artistic illustration')">
                <span>💧</span> Aquarelle
            </div>
            <div class="style-chip" onclick="selectStyle(this, 'dark fantasy, dramatic lighting, epic scene')">
                <span>⚔️</span> Dark Fantasy
            </div>
            <div class="style-chip" onclick="selectStyle(this, 'minimalist, clean lines, geometric, modern design')">
                <span>◻</span> Minimaliste
            </div>
        </div>

        <div class="user-area">
            <div class="user-card" onclick="openAuthModal()" id="userCard">
                <div class="user-avatar" id="userAvatar">?</div>
                <div>
                    <div class="user-name" id="userName">Mode invité</div>
                    <div class="user-status" id="userStatus">Se connecter →</div>
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
                    <div class="progress-label">
                        <span id="progressText">Génération en cours...</span>
                        <span style="color:var(--orange-light)">✦</span>
                    </div>
                    <div class="progress-bar"><div class="progress-fill"></div></div>
                </div>
            </div>

            <div class="input-area">
                <div class="input-main">
                    <div class="input-box">
                        <textarea id="userInput" rows="1" placeholder="Décris ce que tu veux créer..."
                            oninput="autoResize(this)"
                            onkeydown="if(event.key==='Enter'&&!event.shiftKey){event.preventDefault();envoyer();}"></textarea>
                        <button class="send-btn" onclick="envoyer()">↑</button>
                    </div>
                    <div class="input-meta">
                        <div class="negative-wrap">
                            <span class="negative-label">✕ Exclure :</span>
                            <input type="text" class="negative-input" id="negativeInput" placeholder="flou, texte, déformé, mauvaise qualité...">
                        </div>
                        <button class="inspire-btn" onclick="inspire()">✦ Inspire-moi</button>
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
                <button class="page-action-btn" onclick="openCreateFolder()">+ Nouveau dossier</button>
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
                <button class="page-action-btn" onclick="clearHistory()">Effacer tout</button>
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
            <button class="modal-close" onclick="closeOverlay('authOverlay')">✕</button>
        </div>
        <div class="error-msg" id="authError"></div>
        <div class="field-label">Nom d'utilisateur</div>
        <input type="text" class="field-input" id="authUsername" placeholder="ex: johndoe">
        <div class="field-label">Mot de passe</div>
        <input type="password" class="field-input" id="authPassword" placeholder="••••••••" onkeydown="if(event.key==='Enter') authAction()">
        <div class="modal-footer">
            <button class="btn btn-ghost" onclick="closeOverlay('authOverlay')">Annuler</button>
            <button class="btn btn-orange" id="authActionBtn" onclick="authAction()">Se connecter</button>
        </div>
        <div class="auth-switch">
            <span id="authSwitchText">Pas de compte ?</span>
            <span onclick="toggleAuthMode()"> <span id="authSwitchLink">S'inscrire</span></span>
        </div>
    </div>
</div>

<!-- Modal Dossier -->
<div class="overlay" id="folderOverlay">
    <div class="modal-box">
        <div class="modal-head">
            <div class="modal-title">Nouveau dossier</div>
            <button class="modal-close" onclick="closeOverlay('folderOverlay')">✕</button>
        </div>
        <div class="field-label">Nom du projet</div>
        <input type="text" class="field-input" id="folderNameInput" placeholder="ex: Paysages fantasy" onkeydown="if(event.key==='Enter') createFolder()">
        <div class="modal-footer">
            <button class="btn btn-ghost" onclick="closeOverlay('folderOverlay')">Annuler</button>
            <button class="btn btn-orange" onclick="createFolder()">Créer</button>
        </div>
    </div>
</div>

<!-- Modal Sauvegarde -->
<div class="overlay" id="saveOverlay">
    <div class="modal-box">
        <div class="modal-head">
            <div class="modal-title">Sauvegarder dans...</div>
            <button class="modal-close" onclick="closeOverlay('saveOverlay')">✕</button>
        </div>
        <div class="save-folders" id="saveFoldersList"></div>
        <div class="modal-footer">
            <button class="btn btn-ghost" onclick="closeOverlay('saveOverlay')">Annuler</button>
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
let pendingSaveUrl = null;
let pendingSavePrompt = null;

const inspireIdeas = [
    "Un astronaute solitaire sur une planète déserte au coucher de soleil",
    "Une bibliothèque magique flottant dans les nuages",
    "Un dragon endormi dans une forêt de cristaux lumineux",
    "Une ville sous-marine habitée par des créatures de lumière",
    "Un chat géant gardant une cité médiévale",
    "Une forêt enchantée où les arbres brillent comme des étoiles",
    "Un robot artiste peignant un tableau au milieu du désert",
    "Une île volante avec une cascade qui tombe dans les nuages",
];

window.onload = async function() {
    const res = await fetch("/me");
    const data = await res.json();
    if (data.username) {
        setLoggedIn(data.username);
        promptHistory = data.prompt_history || promptHistory;
    }
};

function autoResize(el) {
    el.style.height = 'auto';
    el.style.height = Math.min(el.scrollHeight, 120) + 'px';
}

function showPage(page, el) {
    document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
    document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
    document.getElementById('page-' + page).classList.add('active');
    if (el) el.classList.add('active');
    if (page === 'gallery') loadGallery();
    if (page === 'history') loadHistory();
}

function selectStyle(el, style) {
    document.querySelectorAll('.style-chip').forEach(c => c.classList.remove('selected'));
    el.classList.add('selected');
    selectedStyle = style;
}

function inspire() {
    const idea = inspireIdeas[Math.floor(Math.random() * inspireIdeas.length)];
    document.getElementById('userInput').value = idea;
    autoResize(document.getElementById('userInput'));
}

function addMessage(role, text) {
    const welcome = document.getElementById('welcomeMsg');
    if (welcome) welcome.style.display = 'none';

    const messages = document.getElementById('messages');
    const row = document.createElement('div');
    row.className = 'msg-row ' + role;

    const avatar = document.createElement('div');
    avatar.className = 'msg-avatar ' + role;
    avatar.innerText = role === 'bot' ? '✦' : '✎';

    const bubble = document.createElement('div');
    bubble.className = 'msg-bubble ' + role;
    bubble.innerText = text;

    row.appendChild(avatar);
    row.appendChild(bubble);
    messages.appendChild(row);
    document.getElementById('chatArea').scrollTop = 99999;
    return row;
}

function addImageToChat(imgUrl, prompt, count, index) {
    const messages = document.getElementById('messages');
    const wrap = document.createElement('div');
    wrap.className = 'gen-image-wrap';

    const img = document.createElement('img');
    img.src = imgUrl;

    const actions = document.createElement('div');
    actions.className = 'gen-actions';

    const dlBtn = document.createElement('a');
    dlBtn.href = imgUrl;
    dlBtn.download = `astax-${Date.now()}.png`;
    dlBtn.className = 'gen-btn';
    dlBtn.innerText = '⬇ Télécharger';

    const saveBtn = document.createElement('button');
    saveBtn.className = 'gen-btn primary';
    saveBtn.innerText = '💾 Sauvegarder';
    saveBtn.onclick = () => {
        if (!currentUser) {
            addMessage('bot', '⚠️ Connecte-toi pour sauvegarder tes images !');
            return;
        }
        pendingSaveUrl = imgUrl;
        pendingSavePrompt = prompt;
        openSaveModal();
    };

    if (count > 1) {
        const label = document.createElement('span');
        label.style = 'font-size:0.78em;color:var(--text-dim);align-self:center;';
        label.innerText = `Image ${index + 1}/${count}`;
        actions.appendChild(label);
    }

    actions.appendChild(dlBtn);
    actions.appendChild(saveBtn);
    wrap.appendChild(img);
    wrap.appendChild(actions);
    messages.appendChild(wrap);
    document.getElementById('chatArea').scrollTop = 99999;
}

async function envoyer() {
    const input = document.getElementById('userInput');
    const text = input.value.trim();
    if (!text) return;

    addMessage('user', text);
    conversation.push({role: 'user', content: text});
    input.value = '';
    input.style.height = 'auto';

    const res = await fetch('/chat', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({messages: conversation, style: selectedStyle})
    });
    const data = await res.json();

    if (data.type === 'question') {
        addMessage('bot', data.message);
        conversation.push({role: 'assistant', content: data.message});
    } else if (data.type === 'generate') {
        addMessage('bot', data.message);
        conversation.push({role: 'assistant', content: data.message});
        addToHistory(data.prompt);

        const count = data.count || 1;
        const negPrompt = document.getElementById('negativeInput').value.trim();
        const progress = document.getElementById('progressWrap');
        const progressText = document.getElementById('progressText');
        progress.style.display = 'block';

        for (let i = 0; i < count; i++) {
            progressText.innerText = count > 1 ? `Génération ${i+1} sur ${count}...` : 'Génération en cours...';
            const imgRes = await fetch('/generate', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({prompt: data.prompt, negative_prompt: negPrompt, style: selectedStyle})
            });
            if (imgRes.ok) {
                const blob = await imgRes.blob();
                addImageToChat(URL.createObjectURL(blob), data.prompt, count, i);
            }
        }

        progress.style.display = 'none';
        conversation = [];
    }
}

function addToHistory(prompt) {
    promptHistory = [prompt, ...promptHistory.filter(p => p !== prompt)].slice(0, 20);
    localStorage.setItem('astax_history', JSON.stringify(promptHistory));
    if (currentUser) {
        fetch('/save-history', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({history: promptHistory})
        });
    }
}

function loadHistory() {
    const list = document.getElementById('historyList');
    list.innerHTML = '';
    if (!promptHistory.length) {
        list.innerHTML = '<div class="empty-state"><div class="empty-icon">↺</div><p>Aucun prompt encore.<br>Génère ta première image !</p></div>';
        return;
    }
    promptHistory.forEach(p => {
        const item = document.createElement('div');
        item.className = 'history-item';
        item.innerHTML = `
            <span class="history-icon">✦</span>
            <span class="history-text">${p}</span>
            <button class="history-reuse" onclick="reusePrompt('${p.replace(/'/g, "\\'")}')">Réutiliser</button>`;
        list.appendChild(item);
    });
}

function clearHistory() {
    promptHistory = [];
    localStorage.removeItem('astax_history');
    loadHistory();
}

function reusePrompt(prompt) {
    document.getElementById('userInput').value = prompt;
    autoResize(document.getElementById('userInput'));
    showPage('chat', document.querySelectorAll('.nav-item')[0]);
}

async function loadGallery() {
    if (!currentUser) {
        document.getElementById('foldersList').innerHTML = '<div class="empty-state" style="width:100%"><div class="empty-icon">🔒</div><p>Connecte-toi pour accéder à ta galerie</p></div>';
        document.getElementById('imagesGrid').innerHTML = '';
        return;
    }
    const res = await fetch('/galleries');
    const data = await res.json();
    const fList = document.getElementById('foldersList');
    const iGrid = document.getElementById('imagesGrid');
    fList.innerHTML = '';
    iGrid.innerHTML = '';

    if (!Object.keys(data).length) {
        fList.innerHTML = '<div class="empty-state" style="width:100%"><div class="empty-icon">⊞</div><p>Aucun dossier encore.<br>Crée ton premier projet !</p></div>';
        return;
    }

    Object.keys(data).forEach(name => {
        const pill = document.createElement('div');
        pill.className = 'folder-pill' + (currentFolder === name ? ' active' : '');
        pill.innerHTML = `📁 ${name} <span class="folder-count-badge">${data[name].length}</span>`;
        pill.onclick = () => { currentFolder = name; loadGallery(); };
        fList.appendChild(pill);
    });

    if (currentFolder && data[currentFolder]) {
        data[currentFolder].forEach(img => {
            const card = document.createElement('div');
            card.className = 'img-card';
            card.innerHTML = `
                <img src="${img.image_b64}" alt="">
                <div class="img-card-info">
                    <div class="img-card-prompt">${img.prompt}</div>
                    <div class="img-card-actions">
                        <a href="${img.image_b64}" download="astax.png" class="img-action">⬇</a>
                        <button class="img-action" onclick="deleteImage('${currentFolder}','${img.id}')">✕</button>
                    </div>
                </div>`;
            iGrid.appendChild(card);
        });
    }
}

function openCreateFolder() {
    if (!currentUser) { addMessage('bot', '⚠️ Connecte-toi pour créer des dossiers !'); return; }
    document.getElementById('folderOverlay').classList.add('active');
    document.getElementById('folderNameInput').focus();
}

async function createFolder() {
    const name = document.getElementById('folderNameInput').value.trim();
    if (!name) return;
    await fetch('/create-folder', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({name})});
    document.getElementById('folderNameInput').value = '';
    closeOverlay('folderOverlay');
    loadGallery();
}

function openSaveModal() {
    fetch('/galleries').then(r => r.json()).then(data => {
        const list = document.getElementById('saveFoldersList');
        list.innerHTML = '';
        if (!Object.keys(data).length) {
            list.innerHTML = '<span style="font-size:0.82em;color:var(--text-dim)">Aucun dossier — crée-en un dans la galerie d\'abord !</span>';
        } else {
            Object.keys(data).forEach(name => {
                const btn = document.createElement('button');
                btn.className = 'save-folder-btn';
                btn.innerText = '📁 ' + name;
                btn.onclick = () => saveImageToFolder(name);
                list.appendChild(btn);
            });
        }
        document.getElementById('saveOverlay').classList.add('active');
    });
}

async function saveImageToFolder(folder) {
    const blob = await (await fetch(pendingSaveUrl)).blob();
    const b64 = await new Promise(res => { const r = new FileReader(); r.onloadend = () => res(r.result); r.readAsDataURL(blob); });
    await fetch('/save-image', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({folder, image_b64: b64, prompt: pendingSavePrompt})});
    closeOverlay('saveOverlay');
    addMessage('bot', `✅ Image sauvegardée dans "${folder}" !`);
}

async function deleteImage(folder, id) {
    await fetch('/delete-image', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({folder, id})});
    loadGallery();
}

function closeOverlay(id) { document.getElementById(id).classList.remove('active'); }

function openAuthModal() {
    if (currentUser) { logout(); return; }
    authMode = 'login';
    document.getElementById('authTitle').innerText = 'Connexion';
    document.getElementById('authActionBtn').innerText = 'Se connecter';
    document.getElementById('authSwitchText').innerText = 'Pas de compte ?';
    document.getElementById('authSwitchLink').i
