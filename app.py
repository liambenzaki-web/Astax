import os
import io
import uuid
import hashlib
import urllib.parse
import requests as req
from flask import Flask, request, send_file, jsonify, session

from groq import Groq

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "astax-secret-2026")

GROQ_KEY = os.environ.get("GROQ_API_KEY")
groq_client = Groq(api_key=GROQ_KEY)

users = {}

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# ─────────────────────────────────────────
#  STATIC FILES FOR PWA
# ─────────────────────────────────────────
@app.route("/manifest.json")
def manifest():
    import json
    data = {
        "name": "Astax",
        "short_name": "Astax",
        "description": "Generative AI image application",
        "start_url": "/",
        "display": "standalone",
        "background_color": "#161616",
        "theme_color": "#f97316",
        "orientation": "portrait-primary",
        "icons": [
            {"src": "/static/icons/icon-72x72.png",   "sizes": "72x72",   "type": "image/png", "purpose": "maskable any"},
            {"src": "/static/icons/icon-96x96.png",   "sizes": "96x96",   "type": "image/png", "purpose": "maskable any"},
            {"src": "/static/icons/icon-128x128.png", "sizes": "128x128", "type": "image/png", "purpose": "maskable any"},
            {"src": "/static/icons/icon-144x144.png", "sizes": "144x144", "type": "image/png", "purpose": "maskable any"},
            {"src": "/static/icons/icon-152x152.png", "sizes": "152x152", "type": "image/png", "purpose": "maskable any"},
            {"src": "/static/icons/icon-192x192.png", "sizes": "192x192", "type": "image/png", "purpose": "maskable any"},
            {"src": "/static/icons/icon-384x384.png", "sizes": "384x384", "type": "image/png", "purpose": "maskable any"},
            {"src": "/static/icons/icon-512x512.png", "sizes": "512x512", "type": "image/png", "purpose": "maskable any"}
        ]
    }
    from flask import Response
    return Response(json.dumps(data), mimetype="application/json")

# ─────────────────────────────────────────
#  MAIN PAGE
# ─────────────────────────────────────────
@app.route("/")
def home():
    return """<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Astax</title>

<!-- PWA -->
<link rel="manifest" href="/manifest.json">
<meta name="theme-color" content="#f97316">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="apple-mobile-web-app-title" content="Astax">
<link rel="apple-touch-icon" href="/static/icons/apple-touch-icon.png">
<link rel="icon" type="image/png" sizes="32x32" href="/static/icons/favicon-32x32.png">

<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
<style>
* { box-sizing:border-box; margin:0; padding:0; }
:root {
    --bg:#161616; --bg2:#1e1e1e; --bg3:#262626; --bg4:#2e2e2e;
    --border:rgba(255,255,255,0.07); --border2:rgba(255,255,255,0.12);
    --orange:#f97316; --orange2:#fb923c;
    --orange-dim:rgba(249,115,22,0.1); --orange-dim2:rgba(249,115,22,0.18);
    --text:#f0f0f0; --text2:rgba(255,255,255,0.55); --text3:rgba(255,255,255,0.28);
    --r:10px; --r2:7px; --r3:5px;
    --shadow:0 4px 24px rgba(0,0,0,0.4); --shadow-o:0 4px 20px rgba(249,115,22,0.25);
}
body { background:var(--bg); color:var(--text); font-family:'Inter',sans-serif; height:100vh; display:flex; flex-direction:column; overflow:hidden; font-size:14px; }
#particles { position:fixed; inset:0; z-index:0; pointer-events:none; overflow:hidden; }
.particle { position:absolute; width:2px; height:2px; background:var(--orange); border-radius:50%; opacity:0; animation:floatUp linear infinite; }
@keyframes floatUp { 0%{transform:translateY(100vh);opacity:0} 10%{opacity:0.3} 90%{opacity:0.1} 100%{transform:translateY(-100px);opacity:0} }

.layout { display:flex; flex:1; overflow:hidden; position:relative; z-index:1; }

/* SIDEBAR */
.sidebar { width:232px; background:var(--bg2); border-right:1px solid var(--border); display:flex; flex-direction:column; flex-shrink:0; overflow-y:auto; }
.logo-wrap { padding:18px 16px 16px; border-bottom:1px solid var(--border); flex-shrink:0; }
.logo { display:flex; align-items:center; gap:10px; }
.logo-icon { width:36px; height:36px; background:linear-gradient(135deg,var(--orange),#dc2626); border-radius:10px; display:flex; align-items:center; justify-content:center; font-size:18px; flex-shrink:0; box-shadow:var(--shadow-o); }
.logo-name { font-weight:700; font-size:1.05em; letter-spacing:0.02em; }
.logo-tag { font-size:0.7em; color:var(--text3); margin-top:1px; }

.sidebar-section { padding:12px 10px 6px; }
.sec-label { font-size:0.65em; font-weight:600; color:var(--text3); text-transform:uppercase; letter-spacing:0.08em; padding:0 6px 6px; }
.nav-item { display:flex; align-items:center; gap:8px; padding:8px 10px; border-radius:var(--r2); color:var(--text2); cursor:pointer; transition:all 0.15s; font-size:0.85em; font-weight:500; user-select:none; }
.nav-item:hover { background:var(--bg3); color:var(--text); }
.nav-item.active { background:var(--orange-dim2); color:var(--orange2); }
.nav-item .badge { margin-left:auto; background:var(--orange); color:white; font-size:0.7em; padding:1px 6px; border-radius:99px; font-weight:600; }

.styles-wrap { padding:6px 10px 12px; }
.style-chip { display:inline-block; padding:4px 10px; border-radius:99px; border:1px solid var(--border); color:var(--text3); font-size:0.73em; cursor:pointer; margin:2px; transition:all 0.15s; }
.style-chip:hover { border-color:rgba(249,115,22,0.4); color:var(--orange2); }
.style-chip.active { background:var(--orange-dim2); border-color:var(--orange); color:var(--orange2); }

.user-area { margin-top:auto; padding:12px 10px; border-top:1px solid var(--border); flex-shrink:0; }
.user-card { display:flex; align-items:center; gap:10px; padding:8px 10px; border-radius:var(--r2); cursor:pointer; transition:background 0.15s; }
.user-card:hover { background:var(--bg3); }
.user-avatar { width:30px; height:30px; border-radius:50%; background:var(--orange-dim2); border:1px solid rgba(249,115,22,0.3); display:flex; align-items:center; justify-content:center; font-size:0.8em; font-weight:700; color:var(--orange2); flex-shrink:0; }
.user-name { font-size:0.82em; font-weight:500; }
.user-status { font-size:0.7em; color:var(--text3); margin-top:1px; }

/* MAIN AREA */
.main { flex:1; display:flex; flex-direction:column; overflow:hidden; }

/* CHAT PAGE */
#chatPage { flex:1; display:flex; flex-direction:column; overflow:hidden; }
.msgs-wrap { flex:1; overflow-y:auto; padding:20px; }
.msgs-wrap::-webkit-scrollbar { width:4px; }
.msgs-wrap::-webkit-scrollbar-track { background:transparent; }
.msgs-wrap::-webkit-scrollbar-thumb { background:var(--border2); border-radius:2px; }
.msg { display:flex; gap:10px; margin-bottom:14px; }
.msg.user { flex-direction:row-reverse; }
.msg-avatar { width:28px; height:28px; border-radius:50%; flex-shrink:0; display:flex; align-items:center; justify-content:center; font-size:0.75em; font-weight:700; margin-top:2px; }
.msg.bot .msg-avatar { background:var(--orange-dim2); border:1px solid rgba(249,115,22,0.25); color:var(--orange2); }
.msg.user .msg-avatar { background:var(--bg3); border:1px solid var(--border2); color:var(--text2); }
.msg-bubble { max-width:72%; padding:10px 14px; border-radius:14px; font-size:0.88em; line-height:1.55; }
.msg.bot .msg-bubble { background:var(--bg3); border:1px solid var(--border); border-radius:4px 14px 14px 14px; }
.msg.user .msg-bubble { background:var(--orange-dim2); border:1px solid rgba(249,115,22,0.2); border-radius:14px 4px 14px 14px; color:var(--text); }
.msg-img { max-width:300px; border-radius:var(--r); margin-top:8px; cursor:zoom-in; border:1px solid var(--border); display:block; }
.img-actions { display:flex; gap:6px; margin-top:6px; flex-wrap:wrap; }
.img-btn { padding:4px 10px; border-radius:var(--r3); border:1px solid var(--border2); background:var(--bg4); color:var(--text2); font-size:0.75em; cursor:pointer; transition:all 0.15s; font-family:'Inter',sans-serif; }
.img-btn:hover { border-color:var(--orange); color:var(--orange2); }
.typing { display:flex; gap:4px; align-items:center; padding:4px 0; }
.dot { width:6px; height:6px; border-radius:50%; background:var(--text3); animation:blink 1.2s infinite; }
.dot:nth-child(2) { animation-delay:0.2s; }
.dot:nth-child(3) { animation-delay:0.4s; }
@keyframes blink { 0%,80%,100%{opacity:0.3} 40%{opacity:1} }

.input-area { padding:14px 16px; background:var(--bg2); border-top:1px solid var(--border); flex-shrink:0; }
.neg-wrap { display:flex; align-items:center; gap:6px; margin-bottom:8px; }
.neg-label { font-size:0.72em; color:var(--text3); white-space:nowrap; }
.neg-input { flex:1; padding:5px 10px; background:var(--bg3); border:1px solid var(--border); border-radius:var(--r3); color:var(--text2); font-size:0.78em; font-family:'Inter',sans-serif; outline:none; }
.neg-input:focus { border-color:rgba(249,115,22,0.35); }
.input-row { display:flex; gap:8px; }
.msg-input { flex:1; padding:10px 14px; background:var(--bg3); border:1px solid var(--border); border-radius:var(--r2); color:var(--text); font-size:0.9em; font-family:'Inter',sans-serif; outline:none; transition:border 0.15s; }
.msg-input:focus { border-color:rgba(249,115,22,0.4); }
.send-btn { padding:10px 18px; background:var(--orange); border:none; border-radius:var(--r2); color:white; font-size:0.88em; font-weight:600; cursor:pointer; transition:background 0.15s; font-family:'Inter',sans-serif; }
.send-btn:hover { background:var(--orange2); }
.send-btn:disabled { opacity:0.5; cursor:not-allowed; }

/* GALLERY PAGE */
#galleryPage { flex:1; display:none; flex-direction:column; overflow:hidden; }
.gallery-header { padding:16px 20px; border-bottom:1px solid var(--border); display:flex; align-items:center; justify-content:space-between; flex-shrink:0; }
.gallery-title { font-weight:600; font-size:0.95em; }
.new-folder-btn { padding:6px 14px; background:var(--orange-dim); border:1px solid rgba(249,115,22,0.3); border-radius:var(--r2); color:var(--orange2); font-size:0.78em; cursor:pointer; transition:all 0.15s; font-family:'Inter',sans-serif; }
.new-folder-btn:hover { background:var(--orange-dim2); }
.gallery-body { flex:1; overflow-y:auto; padding:16px 20px; }
.folder-list { display:flex; flex-wrap:wrap; gap:8px; margin-bottom:16px; }
.folder-btn { padding:6px 14px; background:var(--bg3); border:1px solid var(--border); border-radius:var(--r2); color:var(--text2); font-size:0.8em; cursor:pointer; transition:all 0.15s; font-family:'Inter',sans-serif; }
.folder-btn:hover, .folder-btn.active { border-color:var(--orange); color:var(--orange2); background:var(--orange-dim); }
.img-grid { display:grid; grid-template-columns:repeat(auto-fill,minmax(160px,1fr)); gap:10px; }
.thumb { position:relative; border-radius:var(--r); overflow:hidden; border:1px solid var(--border); cursor:zoom-in; aspect-ratio:1; background:var(--bg3); }
.thumb img { width:100%; height:100%; object-fit:cover; display:block; transition:transform 0.2s; }
.thumb:hover img { transform:scale(1.04); }
.thumb-del { position:absolute; top:5px; right:5px; background:rgba(0,0,0,0.7); border:none; border-radius:50%; width:22px; height:22px; color:white; font-size:12px; cursor:pointer; display:none; align-items:center; justify-content:center; }
.thumb:hover .thumb-del { display:flex; }
.empty-state { text-align:center; padding:50px 20px; color:var(--text3); }
.empty-icon { font-size:2.4em; margin-bottom:12px; }
.empty-state p { font-size:0.84em; line-height:1.7; }

/* SAVE OVERLAY */
.overlay { display:none; position:fixed; inset:0; background:rgba(0,0,0,0.75); z-index:500; align-items:center; justify-content:center; backdrop-filter:blur(4px); }
.overlay.open { display:flex; }
.modal { background:var(--bg2); border:1px solid var(--border2); border-radius:var(--r); padding:24px; width:340px; max-width:90vw; }
.modal-title { font-weight:600; font-size:0.95em; margin-bottom:16px; }
.modal input { width:100%; padding:9px 12px; background:var(--bg3); border:1px solid var(--border); border-radius:var(--r2); color:var(--text); font-size:0.85em; font-family:'Inter',sans-serif; outline:none; margin-bottom:12px; }
.modal input:focus { border-color:rgba(249,115,22,0.4); }
.modal-btns { display:flex; gap:8px; justify-content:flex-end; }
.btn-cancel { padding:7px 16px; background:var(--bg3); border:1px solid var(--border); border-radius:var(--r2); color:var(--text2); font-size:0.82em; cursor:pointer; font-family:'Inter',sans-serif; }
.btn-orange { padding:7px 16px; background:var(--orange); border:none; border-radius:var(--r2); color:white; font-size:0.82em; font-weight:600; cursor:pointer; font-family:'Inter',sans-serif; }
.btn-orange:hover { background:var(--orange2); }
.err-box { font-size:0.75em; color:#f87171; padding:6px 10px; background:rgba(239,68,68,0.08); border:1px solid rgba(239,68,68,0.15); border-radius:var(--r2); margin-bottom:10px; display:none; }
.folder-chips { display:flex; flex-wrap:wrap; gap:6px; margin-bottom:12px; }
.fchip { padding:5px 12px; background:var(--bg3); border:1px solid var(--border); border-radius:var(--r2); color:var(--text2); font-size:0.78em; cursor:pointer; transition:all 0.15s; font-family:'Inter',sans-serif; }
.fchip:hover,.fchip.active { border-color:var(--orange); color:var(--orange2); background:var(--orange-dim); }

/* AUTH OVERLAY */
.auth-foot { text-align:center; margin-top:12px; font-size:0.77em; color:var(--text3); }
.auth-link { color:var(--orange2); cursor:pointer; }
.auth-link:hover { text-decoration:underline; }

/* LIGHTBOX */
.lightbox { display:none; position:fixed; inset:0; background:rgba(0,0,0,0.93); z-index:2000; justify-content:center; align-items:center; cursor:zoom-out; }
.lightbox.open { display:flex; }
.lightbox img { max-width:90vw; max-height:90vh; border-radius:var(--r); box-shadow:var(--shadow); }

/* TOAST */
.toast { position:fixed; bottom:24px; right:24px; background:var(--bg3); border:1px solid var(--border2); border-radius:var(--r); padding:10px 16px; font-size:0.82em; color:var(--text); box-shadow:var(--shadow); z-index:3000; transform:translateY(80px); opacity:0; transition:all 0.3s; pointer-events:none; max-width:280px; }
.toast.show { transform:translateY(0); opacity:1; }
.toast.success { border-left:3px solid #4ade80; }
.toast.error { border-left:3px solid #f87171; }
.toast.info { border-left:3px solid var(--orange); }
</style>
</head>
<body>
<div id="particles"></div>
<div class="toast" id="toast"></div>

<!-- LIGHTBOX -->
<div class="lightbox" id="lightbox" onclick="closeLightbox()">
  <img id="lightboxImg" src="">
</div>

<!-- SAVE TO FOLDER OVERLAY -->
<div class="overlay" id="saveOverlay">
  <div class="modal">
    <div class="modal-title">Sauvegarder dans un dossier</div>
    <div class="err-box" id="saveErr"></div>
    <div class="folder-chips" id="saveChips"></div>
    <div class="modal-btns">
      <button class="btn-cancel" onclick="closeOverlay('saveOverlay')">Annuler</button>
      <button class="btn-orange" onclick="confirmSave()">Sauvegarder</button>
    </div>
  </div>
</div>

<!-- NEW FOLDER OVERLAY -->
<div class="overlay" id="folderOverlay">
  <div class="modal">
    <div class="modal-title">Nouveau dossier</div>
    <div class="err-box" id="folderErr"></div>
    <input id="folderName" placeholder="Nom du dossier..." maxlength="40">
    <div class="modal-btns">
      <button class="btn-cancel" onclick="closeOverlay('folderOverlay')">Annuler</button>
      <button class="btn-orange" onclick="confirmNewFolder()">Creer</button>
    </div>
  </div>
</div>

<!-- AUTH OVERLAY -->
<div class="overlay" id="authOverlay">
  <div class="modal">
    <div class="modal-title" id="authTitle">Connexion</div>
    <div class="err-box" id="authError"></div>
    <input id="authUsername" placeholder="Nom utilisateur..." maxlength="30" onkeydown="if(event.key==='Enter') authAction()">
    <input id="authPassword" type="password" placeholder="Mot de passe..." maxlength="60" onkeydown="if(event.key==='Enter') authAction()">
    <div class="modal-btns">
      <button class="btn-cancel" onclick="closeOverlay('authOverlay')">Annuler</button>
      <button class="btn-orange" id="authActionBtn" onclick="authAction()">Se connecter</button>
    </div>
    <div class="auth-foot">
      <span id="authSwitchText">Pas de compte ?</span>
      <span class="auth-link" id="authSwitchLink" onclick="toggleAuthMode()">S'inscrire</span>
    </div>
  </div>
</div>

<div class="layout">
  <!-- SIDEBAR -->
  <aside class="sidebar">
    <div class="logo-wrap">
      <div class="logo">
        <div class="logo-icon">&#10022;</div>
        <div>
          <div class="logo-name">Astax</div>
          <div class="logo-tag">Generative Image AI</div>
        </div>
      </div>
    </div>

    <div class="sidebar-section">
      <div class="sec-label">Navigation</div>
      <div class="nav-item active" id="navChat" onclick="showPage('chat')">&#10022; Creer</div>
      <div class="nav-item" id="navGallery" onclick="showPage('gallery')">&#8862; Galerie <span class="badge" id="galBadge">0</span></div>
    </div>

    <div class="sidebar-section">
      <div class="sec-label">Style rapide</div>
    </div>
    <div class="styles-wrap">
      <div class="style-chip active" onclick="setStyle(this,'')">Auto</div>
      <div class="style-chip" onclick="setStyle(this,'photorealistic, ultra detailed, 8k photography')">Photo</div>
      <div class="style-chip" onclick="setStyle(this,'anime style, manga, vibrant, studio ghibli')">Anime</div>
      <div class="style-chip" onclick="setStyle(this,'oil painting, artistic brushstrokes, renaissance')">Peinture</div>
      <div class="style-chip" onclick="setStyle(this,'pixel art, 16-bit retro game style')">Pixel Art</div>
      <div class="style-chip" onclick="setStyle(this,'cyberpunk, neon lights, futuristic dark city')">Cyberpunk</div>
      <div class="style-chip" onclick="setStyle(this,'watercolor, soft dreamy artistic illustration')">Aquarelle</div>
      <div class="style-chip" onclick="setStyle(this,'dark fantasy, dramatic lighting, epic scene')">Dark Fantasy</div>
      <div class="style-chip" onclick="setStyle(this,'minimalist, clean lines, geometric, modern')">Minimaliste</div>
    </div>

    <div class="user-area">
      <div class="user-card" onclick="handleUserClick()">
        <div class="user-avatar" id="userAvatar">?</div>
        <div>
          <div class="user-name" id="userName">Mode invite</div>
          <div class="user-status" id="userStatus">Cliquer pour se connecter</div>
        </div>
      </div>
    </div>
  </aside>

  <!-- MAIN -->
  <div class="main">

    <!-- CHAT PAGE -->
    <div id="chatPage">
      <div class="msgs-wrap" id="msgsWrap">
        <div id="msgs"></div>
      </div>
      <div class="input-area">
        <div class="neg-wrap">
          <span class="neg-label">Exclure :</span>
          <input class="neg-input" id="negInput" placeholder="ex : flou, texte, deformation...">
        </div>
        <div class="input-row">
          <input class="msg-input" id="msgInput" placeholder="Decris ce que tu veux creer..." onkeydown="if(event.key==='Enter'&&!event.shiftKey){send();event.preventDefault();}">
          <button class="send-btn" id="sendBtn" onclick="send()">Envoyer</button>
        </div>
      </div>
    </div>

    <!-- GALLERY PAGE -->
    <div id="galleryPage">
      <div class="gallery-header">
        <div class="gallery-title">Ma Galerie</div>
        <button class="new-folder-btn" onclick="openNewFolder()">+ Nouveau dossier</button>
      </div>
      <div class="gallery-body">
        <div class="folder-list" id="folderList"></div>
        <div id="imgGrid"></div>
      </div>
    </div>

  </div>
</div>

<script>
// ── STATE ──────────────────────────────────────────────────────────
var conversation = [];
var selectedStyle = "";
var currentUser = null;
var authMode = "login";
var galleries = {};
var currentFolder = null;
var pendingSaveImg = null;
var pendingSavePrompt = "";
var promptHistory = [];
var totalImages = 0;
var isGenerating = false;

// ── INIT ───────────────────────────────────────────────────────────
window.onload = function() {
  createParticles();
  fetch("/me").then(function(r){return r.json();}).then(function(d){
    if (d.username) {
      setLoggedIn(d.username);
      promptHistory = d.prompt_history || [];
    } else {
      try { promptHistory = JSON.parse(localStorage.getItem("astax_history") || "[]"); } catch(e) { promptHistory = []; }
    }
  });
  addMsg("bot", "Bonjour ! Je suis ton assistant creatif Astax. Decris ce que tu veux creer comme image !");
};

function createParticles() {
  var c = document.getElementById("particles");
  for (var i = 0; i < 25; i++) {
    var p = document.createElement("div");
    p.className = "particle";
    p.style.left = Math.random()*100+"%";
    p.style.animationDuration = (8+Math.random()*12)+"s";
    p.style.animationDelay = (Math.random()*10)+"s";
    p.style.opacity = Math.random()*0.4;
    c.appendChild(p);
  }
}

// ── PAGES ──────────────────────────────────────────────────────────
function showPage(page) {
  document.getElementById("chatPage").style.display = page==="chat" ? "flex" : "none";
  document.getElementById("galleryPage").style.display = page==="gallery" ? "flex" : "none";
  document.getElementById("navChat").classList.toggle("active", page==="chat");
  document.getElementById("navGallery").classList.toggle("active", page==="gallery");
  if (page==="gallery") renderGallery();
}

// ── STYLE ──────────────────────────────────────────────────────────
function setStyle(el, style) {
  document.querySelectorAll(".style-chip").forEach(function(c){ c.classList.remove("active"); });
  el.classList.add("active");
  selectedStyle = style;
}

// ── CHAT ───────────────────────────────────────────────────────────
function send() {
  var text = document.getElementById("msgInput").value.trim();
  if (!text || isGenerating) return;
  document.getElementById("msgInput").value = "";
  addMsg("user", text);
  conversation.push({role:"user", content:text});
  showTyping();
  isGenerating = true;
  document.getElementById("sendBtn").disabled = true;

  fetch("/chat", {
    method:"POST",
    headers:{"Content-Type":"application/json"},
    body: JSON.stringify({messages: conversation, style: selectedStyle})
  }).then(function(r){return r.json();}).then(function(d) {
    removeTyping();
    if (d.type === "generate") {
      addMsg("bot", d.message);
      conversation.push({role:"assistant", content:d.message});
      generateImages(d.prompt, d.count || 1);
      addToHistory(text);
    } else {
      addMsg("bot", d.message);
      conversation.push({role:"assistant", content:d.message});
      isGenerating = false;
      document.getElementById("sendBtn").disabled = false;
    }
  }).catch(function() {
    removeTyping();
    addMsg("bot", "Erreur de connexion. Reessaie !");
    isGenerating = false;
    document.getElementById("sendBtn").disabled = false;
  });
}

function generateImages(prompt, count) {
  var neg = document.getElementById("negInput").value.trim();
  var remaining = count;
  var generated = 0;
  addMsg("bot", "Generation de " + count + " image(s) en cours...");

  for (var i = 0; i < count; i++) {
    (function(idx) {
      fetch("/generate", {
        method:"POST",
        headers:{"Content-Type":"application/json"},
        body: JSON.stringify({prompt:prompt, negative_prompt:neg, style:selectedStyle})
      }).then(function(r){return r.blob();}).then(function(blob) {
        var url = URL.createObjectURL(blob);
        addImageMsg(url, prompt);
        totalImages++;
        document.getElementById("galBadge").innerText = totalImages;
        generated++;
        if (generated >= count) {
          isGenerating = false;
          document.getElementById("sendBtn").disabled = false;
          conversation = [];
        }
      }).catch(function() {
        addMsg("bot", "Erreur generation image " + (idx+1));
        generated++;
        if (generated >= count) {
          isGenerating = false;
          document.getElementById("sendBtn").disabled = false;
          conversation = [];
        }
      });
    })(i);
  }
}

// ── MESSAGES ───────────────────────────────────────────────────────
function addMsg(role, text) {
  var msgs = document.getElementById("msgs");
  var div = document.createElement("div");
  div.className = "msg " + role;
  var av = role==="bot" ? "&#10022;" : (currentUser ? currentUser[0].toUpperCase() : "U");
  div.innerHTML = '<div class="msg-avatar">'+av+'</div><div class="msg-bubble">'+escHtml(text)+'</div>';
  msgs.appendChild(div);
  scrollBottom();
}

function addImageMsg(url, prompt) {
  var msgs = document.getElementById("msgs");
  var div = document.createElement("div");
  div.className = "msg bot";
  var imgId = "img_" + Date.now() + "_" + Math.random().toString(36).substr(2,5);
  div.innerHTML = '<div class="msg-avatar">&#10022;</div><div class="msg-bubble">' +
    '<img class="msg-img" id="'+imgId+'" src="'+url+'" onclick="openLightbox(this.src)">' +
    '<div class="img-actions">' +
    '<button class="img-btn" onclick="downloadImg(\''+url+'\')">Telecharger</button>' +
    '<button class="img-btn" onclick="openSave(\''+url+'\',\''+escAttr(prompt)+'\')">Sauvegarder</button>' +
    '</div></div>';
  msgs.appendChild(div);
  scrollBottom();
}

function showTyping() {
  var msgs = document.getElementById("msgs");
  var div = document.createElement("div");
  div.className = "msg bot";
  div.id = "typingMsg";
  div.innerHTML = '<div class="msg-avatar">&#10022;</div><div class="msg-bubble"><div class="typing"><div class="dot"></div><div class="dot"></div><div class="dot"></div></div></div>';
  msgs.appendChild(div);
  scrollBottom();
}

function removeTyping() {
  var t = document.getElementById("typingMsg");
  if (t) t.remove();
}

function scrollBottom() {
  var w = document.getElementById("msgsWrap");
  w.scrollTop = w.scrollHeight;
}

// ── GALLERY ────────────────────────────────────────────────────────
function renderGallery() {
  var fl = document.getElementById("folderList");
  fl.innerHTML = "";
  var folders = Object.keys(galleries);
  if (folders.length === 0) {
    document.getElementById("imgGrid").innerHTML = '<div class="empty-state"><div class="empty-icon">&#128193;</div><p>Aucun dossier.<br>Cree un dossier pour sauvegarder tes images.</p></div>';
    return;
  }
  if (!currentFolder || !galleries[currentFolder]) currentFolder = folders[0];
  folders.forEach(function(name) {
    var btn = document.createElement("button");
    btn.className = "folder-btn" + (name===currentFolder ? " active" : "");
    btn.innerText = name + " (" + galleries[name].length + ")";
    btn.onclick = function() { currentFolder = name; renderGallery(); };
    fl.appendChild(btn);
  });
  var grid = document.getElementById("imgGrid");
  var imgs = galleries[currentFolder] || [];
  if (imgs.length === 0) {
    grid.innerHTML = '<div class="empty-state"><div class="empty-icon">&#128247;</div><p>Dossier vide.<br>Sauvegarde tes images depuis le chat.</p></div>';
    return;
  }
  grid.innerHTML = "";
  var g = document.createElement("div");
  g.className = "img-grid";
  imgs.forEach(function(item) {
    var d = document.createElement("div");
    d.className = "thumb";
    d.innerHTML = '<img src="'+item.url+'" onclick="openLightbox(\''+item.url+'\')"><button class="thumb-del" onclick="deleteImg(\''+item.id+'\')">&#10005;</button>';
    g.appendChild(d);
  });
  grid.appendChild(g);
}

function openNewFolder() {
  if (!currentUser) { toast("Connecte-toi pour creer des dossiers", "error"); return; }
  document.getElementById("folderName").value = "";
  document.getElementById("folderErr").style.display = "none";
  openOverlay("folderOverlay");
  setTimeout(function(){ document.getElementById("folderName").focus(); }, 100);
}

function confirmNewFolder() {
  var name = document.getElementById("folderName").value.trim();
  if (!name) { showErr("folderErr", "Entre un nom de dossier."); return; }
  if (galleries[name]) { showErr("folderErr", "Ce dossier existe deja."); return; }
  galleries[name] = [];
  if (currentUser) {
    fetch("/create-folder", {method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify({name:name})});
  }
  currentFolder = name;
  closeOverlay("folderOverlay");
  toast("Dossier cree !", "success");
  renderGallery();
}

function openSave(url, prompt) {
  if (!currentUser) { toast("Connecte-toi pour sauvegarder", "error"); return; }
  if (Object.keys(galleries).length === 0) { toast("Cree d'abord un dossier dans Galerie", "info"); return; }
  pendingSaveImg = url;
  pendingSavePrompt = prompt;
  var chips = document.getElementById("saveChips");
  chips.innerHTML = "";
  Object.keys(galleries).forEach(function(name) {
    var c = document.createElement("div");
    c.className = "fchip";
    c.innerText = name;
    c.onclick = function() {
      document.querySelectorAll(".fchip").forEach(function(x){ x.classList.remove("active"); });
      c.classList.add("active");
    };
    chips.appendChild(c);
  });
  if (chips.firstChild) chips.firstChild.classList.add("active");
  document.getElementById("saveErr").style.display = "none";
  openOverlay("saveOverlay");
}

function confirmSave() {
  var active = document.querySelector(".fchip.active");
  if (!active) { showErr("saveErr", "Selectionne un dossier."); return; }
  var folder = active.innerText;
  var id = uuid();
  if (!galleries[folder]) galleries[folder] = [];
  galleries[folder].push({id:id, url:pendingSaveImg, prompt:pendingSavePrompt});
  if (currentUser) {
    fetch("/save-image", {method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify({folder:folder, url:pendingSaveImg, id:id, prompt:pendingSavePrompt})});
  }
  document.getElementById("galBadge").innerText = countAllImages();
  closeOverlay("saveOverlay");
  toast("Image sauvegardee dans " + folder, "success");
}

function deleteImg(id) {
  if (!currentFolder) return;
  galleries[currentFolder] = galleries[currentFolder].filter(function(i){ return i.id !== id; });
  if (currentUser) {
    fetch("/delete-image", {method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify({folder:currentFolder, id:id})});
  }
  document.getElementById("galBadge").innerText = countAllImages();
  renderGallery();
}

function countAllImages() {
  var n = 0;
  Object.values(galleries).forEach(function(arr){ n += arr.length; });
  return n;
}

// ── AUTH ───────────────────────────────────────────────────────────
function handleUserClick() {
  if (currentUser) {
    if (confirm("Se deconnecter ?")) logout();
  } else {
    authMode = "login";
    updateAuthUI();
    document.getElementById("authError").style.display = "none";
    document.getElementById("authUsername").value = "";
    document.getElementById("authPassword").value = "";
    openOverlay("authOverlay");
    setTimeout(function(){ document.getElementById("authUsername").focus(); }, 100);
  }
}

function toggleAuthMode() {
  authMode = authMode==="login" ? "register" : "login";
  updateAuthUI();
}

function updateAuthUI() {
  var isLogin = authMode==="login";
  document.getElementById("authTitle").innerText = isLogin ? "Connexion" : "Inscription";
  document.getElementById("authActionBtn").innerText = isLogin ? "Se connecter" : "S'inscrire";
  document.getElementById("authSwitchText").innerText = isLogin ? "Pas de compte ?" : "Deja un compte ?";
  document.getElementById("authSwitchLink").innerText = isLogin ? "S'inscrire" : "Se connecter";
  document.getElementById("authError").style.display = "none";
}

function authAction() {
  var u = document.getElementById("authUsername").value.trim();
  var p = document.getElementById("authPassword").value;
  if (!u || !p) return;
  var ep = authMode==="login" ? "/login" : "/register";
  fetch(ep, {method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify({username:u, password:p})})
    .then(function(r){return r.json();}).then(function(d) {
      if (d.success) {
        setLoggedIn(u);
        if (d.prompt_history) promptHistory = d.prompt_history;
        if (d.galleries) galleries = convertGalleries(d.galleries);
        closeOverlay("authOverlay");
        addMsg("bot", authMode==="login" ? "Bon retour " + u + " !" : "Bienvenue " + u + " !");
        document.getElementById("galBadge").innerText = countAllImages();
      } else {
        showErr("authError", d.error);
      }
    });
}

function convertGalleries(serverGals) {
  var result = {};
  Object.keys(serverGals).forEach(function(folder) {
    result[folder] = serverGals[folder].map(function(item) {
      return {id: item.id || uuid(), url: item.url || "", prompt: item.prompt || ""};
    });
  });
  return result;
}

function setLoggedIn(username) {
  currentUser = username;
  document.getElementById("userAvatar").innerText = username[0].toUpperCase();
  document.getElementById("userName").innerText = username;
  document.getElementById("userStatus").innerText = "Connecte - cliquer pour deconnecter";
}

function logout() {
  fetch("/logout", {method:"POST"}).then(function() {
    currentUser = null;
    galleries = {};
    document.getElementById("userAvatar").innerText = "?";
    document.getElementById("userName").innerText = "Mode invite";
    document.getElementById("userStatus").innerText = "Cliquer pour se connecter";
    document.getElementById("galBadge").innerText = "0";
    toast("Deconnecte", "info");
  });
}

// ── HISTORY ────────────────────────────────────────────────────────
function addToHistory(prompt) {
  promptHistory = promptHistory.filter(function(p){ return p !== prompt; });
  promptHistory.unshift(prompt);
  if (promptHistory.length > 20) promptHistory = promptHistory.slice(0,20);
  if (currentUser) {
    fetch("/save-history", {method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify({history:promptHistory})});
  } else {
    try { localStorage.setItem("astax_history", JSON.stringify(promptHistory)); } catch(e) {}
  }
}

// ── HELPERS ────────────────────────────────────────────────────────
function downloadImg(url) {
  var a = document.createElement("a");
  a.href = url;
  a.download = "astax_" + Date.now() + ".png";
  a.click();
}

function openLightbox(src) {
  document.getElementById("lightboxImg").src = src;
  document.getElementById("lightbox").classList.add("open");
}

function closeLightbox() {
  document.getElementById("lightbox").classList.remove("open");
}

function openOverlay(id) { document.getElementById(id).classList.add("open"); }
function closeOverlay(id) { document.getElementById(id).classList.remove("open"); }

function showErr(id, msg) {
  var el = document.getElementById(id);
  el.innerText = msg;
  el.style.display = "block";
}

function toast(msg, type) {
  var t = document.getElementById("toast");
  t.innerText = msg;
  t.className = "toast show " + (type||"info");
  clearTimeout(t._timer);
  t._timer = setTimeout(function(){ t.classList.remove("show"); }, 3000);
}

function escHtml(s) { return s.replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;"); }
function escAttr(s) { return s.replace(/'/g,"&#39;").replace(/"/g,"&quot;"); }

function uuid() {
  return "id_" + Math.random().toString(36).substr(2,9) + "_" + Date.now();
}
</script>

<!-- PWA SERVICE WORKER -->
<script>
if ('serviceWorker' in navigator) {
  window.addEventListener('load', function() {
    navigator.serviceWorker.register('/static/service-worker.js')
      .then(function(r){ console.log('SW registered'); })
      .catch(function(e){ console.log('SW error:', e); });
  });
}
</script>
</body>
</html>"""

# ─────────────────────────────────────────
#  API ROUTES
# ─────────────────────────────────────────
@app.route("/chat", methods=["POST"])
def chat():
    data = request.json
    messages = data.get("messages", [])
    style = data.get("style", "")
    style_hint = " Le style visuel choisi : " + style + "." if style else ""

    system = """Tu es un assistant creatif qui aide a creer des images avec une IA.""" + style_hint + """
Pose des questions preciseen francais, puis genere un prompt detaille en anglais.
Regles STRICTES :
- UNE seule question courte a la fois
- Maximum 3 questions
- Avant de generer, demande : "Combien d'images souhaitez-vous ? (1 a 5)"
- Reponds UNIQUEMENT avec ce format exact (3 lignes, rien d'autre) :
GENERATE: [prompt anglais ultra detaille]
COUNT: [1-5]
MESSAGE: [phrase courte enthousiaste en francais sans apostrophe]"""

    response = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        max_tokens=600,
        messages=[{"role": "system", "content": system}] + messages
    )
    text = response.choices[0].message.content

    if "GENERATE:" in text:
        lines = text.split("\n")
        prompt, count, message = "", 1, "Generation en cours !"
        for line in lines:
            line = line.strip()
            if line.startswith("GENERATE:"):
                prompt = line[9:].strip()
            elif line.startswith("COUNT:"):
                try:
                    count = max(1, min(5, int(line[6:].strip())))
                except:
                    count = 1
            elif line.startswith("MESSAGE:"):
                message = line[8:].strip()
        return jsonify({"type": "generate", "prompt": prompt, "count": count, "message": message})
    return jsonify({"type": "question", "message": text})


@app.route("/generate", methods=["POST"])
def generate():
    data = request.json
    prompt = data.get("prompt", "a beautiful landscape")
    neg = data.get("negative_prompt", "")
    style = data.get("style", "")

    full = (prompt + ", " + style).strip(", ") if style else prompt
    if neg:
        full = full + ", avoid: " + neg

    encoded = urllib.parse.quote(full)
    seed = str(uuid.uuid4().int % 1000000)
    url = "https://image.pollinations.ai/prompt/" + encoded + "?width=1024&height=1024&nologo=true&enhance=true&seed=" + seed

    response = req.get(url, timeout=120)
    if response.status_code != 200:
        return jsonify({"error": "Generation failed"}), 500

    return send_file(io.BytesIO(response.content), mimetype="image/png")


@app.route("/me")
def me():
    u = session.get("username")
    if u and u in users:
        return jsonify({
            "username": u,
            "prompt_history": users[u].get("prompt_history", []),
            "galleries": users[u].get("galleries", {})
        })
    return jsonify({"username": None})


@app.route("/register", methods=["POST"])
def register():
    d = request.json
    u, p = d.get("username", "").strip(), d.get("password", "")
    if not u or not p:
        return jsonify({"success": False, "error": "Remplis tous les champs."})
    if len(p) < 6:
        return jsonify({"success": False, "error": "Mot de passe trop court (6 caracteres min)."})
    if u in users:
        return jsonify({"success": False, "error": "Nom deja pris."})
    users[u] = {"password_hash": hash_password(p), "galleries": {}, "prompt_history": []}
    session["username"] = u
    return jsonify({"success": True})


@app.route("/login", methods=["POST"])
def login():
    d = request.json
    u, p = d.get("username", "").strip(), d.get("password", "")
    if u not in users:
        return jsonify({"success": False, "error": "Utilisateur introuvable."})
    if users[u]["password_hash"] != hash_password(p):
        return jsonify({"success": False, "error": "Mot de passe incorrect."})
    session["username"] = u
    return jsonify({
        "success": True,
        "prompt_history": users[u].get("prompt_history", []),
        "galleries": users[u].get("galleries", {})
    })


@app.route("/logout", methods=["POST"])
def logout():
    session.pop("username", None)
    return jsonify({"success": True})


@app.route("/create-folder", methods=["POST"])
def create_folder():
    u = session.get("username")
    if not u or u not in users:
        return jsonify({"success": False})
    name = request.json.get("name", "").strip()
    if name and name not in users[u]["galleries"]:
        users[u]["galleries"][name] = []
    return jsonify({"success": True})


@app.route("/save-image", methods=["POST"])
def save_image():
    u = session.get("username")
    if not u or u not in users:
        return jsonify({"success": False})
    d = request.json
    folder, url, prompt, img_id = d.get("folder"), d.get("url"), d.get("prompt", ""), d.get("id", str(uuid.uuid4()))
    if folder in users[u]["galleries"]:
        users[u]["galleries"][folder].append({"id": img_id, "url": url, "prompt": prompt})
    return jsonify({"success": True})


@app.route("/delete-image", methods=["POST"])
def delete_image():
    u = session.get("username")
    if not u or u not in users:
        return jsonify({"success": False})
    d = request.json
    folder, img_id = d.get("folder"), d.get("id")
    if folder in users[u]["galleries"]:
        users[u]["galleries"][folder] = [i for i in users[u]["galleries"][folder] if str(i["id"]) != str(img_id)]
    return jsonify({"success": True})


@app.route("/save-history", methods=["POST"])
def save_history():
    u = session.get("username")
    if u and u in users:
        users[u]["prompt_history"] = request.json.get("history", [])
    return jsonify({"success": True})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=7860)
