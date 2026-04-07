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
            --bg:#161616; --bg2:#1e1e1e; --bg3:#262626; --bg4:#2e2e2e;
            --border:rgba(255,255,255,0.07); --border2:rgba(255,255,255,0.12);
            --orange:#f97316; --orange2:#fb923c; --orange-dim:rgba(249,115,22,0.1); --orange-dim2:rgba(249,115,22,0.18);
            --text:#f0f0f0; --text2:rgba(255,255,255,0.55); --text3:rgba(255,255,255,0.28);
            --r:10px; --r2:7px; --r3:5px;
            --shadow:0 4px 24px rgba(0,0,0,0.4); --shadow-o:0 4px 20px rgba(249,115,22,0.25);
        }
        body { background:var(--bg); color:var(--text); font-family:'Inter',sans-serif; height:100vh; display:flex; flex-direction:column; overflow:hidden; font-size:14px; }
        #particles { position:fixed; inset:0; z-index:0; pointer-events:none; overflow:hidden; }
        .particle { position:absolute; width:2px; height:2px; background:var(--orange); border-radius:50%; opacity:0; animation:floatUp linear infinite; }
        @keyframes floatUp { 0%{transform:translateY(100vh);opacity:0} 10%{opacity:0.3} 90%{opacity:0.1} 100%{transform:translateY(-100px);opacity:0} }
        .layout { display:flex; flex:1; overflow:hidden; position:relative; z-index:1; }
        .sidebar { width:232px; background:var(--bg2); border-right:1px solid var(--border); display:flex; flex-direction:column; flex-shrink:0; }
        .logo-wrap { padding:18px 16px 16px; border-bottom:1px solid var(--border); }
        .logo { display:flex; align-items:center; gap:10px; }
        .logo-icon { width:36px; height:36px; background:linear-gradient(135deg,var(--orange),#dc2626); border-radius:10px; display:flex; align-items:center; justify-content:center; font-size:17px; flex-shrink:0; box-shadow:var(--shadow-o); transition:transform 0.3s; cursor:default; }
        .logo-icon:hover { transform:rotate(15deg) scale(1.05); }
        .logo-name { font-weight:700; font-size:1.08em; }
        .logo-tag { font-size:0.64em; color:var(--text3); margin-top:1px; }
        .sidebar-nav { padding:12px 10px 0; }
        .sec-label { font-size:0.6em; color:var(--text3); letter-spacing:1.8px; text-transform:uppercase; padding:0 6px; margin:10px 0 5px; font-weight:600; }
        .nav-item { display:flex; align-items:center; gap:9px; padding:8px 10px; border-radius:var(--r2); cursor:pointer; color:var(--text2); font-size:0.87em; font-weight:500; transition:all 0.18s; margin-bottom:1px; border:1px solid transparent; user-select:none; }
        .nav-item:hover { background:var(--bg3); color:var(--text); }
        .nav-item.active { background:var(--orange-dim); color:var(--orange2); border-color:rgba(249,115,22,0.12); }
        .badge { margin-left:auto; background:var(--orange); color:white; font-size:0.65em; padding:1px 6px; border-radius:10px; font-weight:600; display:none; }
        .badge.on { display:inline; }
        .nav-divider { height:1px; background:var(--border); margin:10px 6px; }
        .styles-wrap { padding:0 10px; flex:1; overflow-y:auto; }
        .styles-wrap::-webkit-scrollbar { width:3px; }
        .styles-wrap::-webkit-scrollbar-thumb { background:rgba(255,255,255,0.08); border-radius:2px; }
        .style-chip { display:flex; align-items:center; gap:8px; padding:7px 10px; border-radius:var(--r2); cursor:pointer; color:var(--text2); font-size:0.82em; transition:all 0.18s; margin-bottom:1px; user-select:none; }
        .style-chip:hover { background:var(--bg3); color:var(--text); }
        .style-chip.on { color:var(--orange2); background:var(--orange-dim); font-weight:500; }
        .chip-dot { width:6px; height:6px; border-radius:50%; background:var(--text3); flex-shrink:0; transition:background 0.2s; }
        .style-chip.on .chip-dot { background:var(--orange); }
        .user-wrap { padding:10px; border-top:1px solid var(--border); margin-top:auto; }
        .user-card { display:flex; align-items:center; gap:9px; padding:9px 10px; border-radius:var(--r2); background:var(--bg3); cursor:pointer; transition:all 0.18s; user-select:none; border:1px solid transparent; }
        .user-card:hover { border-color:var(--border2); }
        .user-av { width:30px; height:30px; border-radius:50%; flex-shrink:0; display:flex; align-items:center; justify-content:center; font-size:0.8em; font-weight:700; background:linear-gradient(135deg,var(--orange),#dc2626); }
        .user-av.guest { background:var(--bg4); color:var(--text3); font-size:1em; }
        .u-name { font-size:0.84em; font-weight:500; }
        .u-status { font-size:0.68em; color:var(--text3); margin-top:1px; }
        .main { flex:1; display:flex; flex-direction:column; overflow:hidden; min-width:0; }
        .page { display:none; flex:1; flex-direction:column; overflow:hidden; }
        .page.active { display:flex; }
        .chat-scroll { flex:1; overflow-y:auto; padding:24px 24px 8px; }
        .chat-scroll::-webkit-scrollbar { width:5px; }
        .chat-scroll::-webkit-scrollbar-thumb { background:rgba(255,255,255,0.08); border-radius:3px; }
        .welcome { display:flex; flex-direction:column; align-items:center; justify-content:center; padding:60px 20px 40px; text-align:center; }
        .welcome-orb { width:64px; height:64px; border-radius:18px; background:linear-gradient(135deg,var(--orange),#dc2626); display:flex; align-items:center; justify-content:center; font-size:26px; margin-bottom:18px; box-shadow:var(--shadow-o); animation:orbPulse 3s ease-in-out infinite; }
        @keyframes orbPulse { 0%,100%{box-shadow:0 4px 20px rgba(249,115,22,0.25)} 50%{box-shadow:0 4px 32px rgba(249,115,22,0.45)} }
        .welcome h2 { font-size:1.35em; font-weight:600; margin-bottom:8px; }
        .welcome p { color:var(--text2); font-size:0.88em; max-width:360px; line-height:1.65; }
        .quick-prompts { display:flex; flex-wrap:wrap; gap:7px; justify-content:center; margin-top:20px; }
        .qchip { padding:6px 13px; border-radius:20px; border:1px solid var(--border2); font-size:0.78em; color:var(--text2); cursor:pointer; transition:all 0.18s; background:var(--bg2); }
        .qchip:hover { border-color:rgba(249,115,22,0.35); color:var(--orange2); background:var(--orange-dim); }
        .messages { display:flex; flex-direction:column; gap:12px; max-width:660px; margin:0 auto; width:100%; }
        .msg-row { display:flex; gap:9px; align-items:flex-start; animation:msgIn 0.25s ease; }
        @keyframes msgIn { from{opacity:0;transform:translateY(8px)} to{opacity:1;transform:translateY(0)} }
        .msg-row.user { flex-direction:row-reverse; }
        .msg-av { width:28px; height:28px; border-radius:50%; flex-shrink:0; margin-top:2px; display:flex; align-items:center; justify-content:center; font-size:0.75em; font-weight:700; }
        .msg-av.bot { background:linear-gradient(135deg,var(--orange),#dc2626); }
        .msg-av.user { background:var(--bg4); border:1px solid var(--border2); color:var(--text2); }
        .msg-bbl { padding:9px 13px; border-radius:var(--r); max-width:78%; font-size:0.88em; line-height:1.6; }
        .msg-bbl.bot { background:var(--bg3); border:1px solid var(--border); border-top-left-radius:3px; }
        .msg-bbl.user { background:var(--orange-dim); border:1px solid rgba(249,115,22,0.15); border-top-right-radius:3px; }
        .typing { display:flex; align-items:center; gap:4px; padding:10px 14px; }
        .typing span { width:6px; height:6px; border-radius:50%; background:var(--text3); animation:typeDot 1.2s ease-in-out infinite; }
        .typing span:nth-child(2){animation-delay:0.2s} .typing span:nth-child(3){animation-delay:0.4s}
        @keyframes typeDot { 0%,60%,100%{transform:translateY(0)} 30%{transform:translateY(-5px)} }
        .progress-card { display:none; max-width:660px; margin:0 auto; padding:14px 16px; background:var(--bg3); border:1px solid var(--border); border-radius:var(--r); animation:msgIn 0.25s ease; }
        .progress-top { display:flex; justify-content:space-between; align-items:center; margin-bottom:10px; }
        .progress-lbl { font-size:0.78em; color:var(--text2); }
        .progress-timer { font-size:0.72em; color:var(--orange2); font-weight:500; }
        .pbar { height:3px; background:rgba(255,255,255,0.06); border-radius:2px; overflow:hidden; }
        .pbar-fill { height:100%; background:linear-gradient(90deg,var(--orange),#dc2626); animation:pbarAnim 2s ease-in-out infinite; border-radius:2px; }
        @keyframes pbarAnim { 0%{width:0%;margin-left:0} 50%{width:65%;margin-left:0} 100%{width:0%;margin-left:100%} }
        .img-result { max-width:660px; margin:0 auto; background:var(--bg3); border:1px solid var(--border); border-radius:var(--r); overflow:hidden; animation:msgIn 0.3s ease; }
        .img-result img { width:100%; max-height:520px; object-fit:cover; display:block; cursor:zoom-in; transition:opacity 0.2s; }
        .img-result img:hover { opacity:0.9; }
        .img-meta { padding:10px 13px; border-top:1px solid var(--border); }
        .img-prompt-used { font-size:0.72em; color:var(--text3); margin-bottom:8px; line-height:1.5; }
        .img-actions { display:flex; gap:6px; flex-wrap:wrap; }
        .act-btn { padding:5px 12px; border-radius:var(--r3); font-size:0.75em; font-weight:500; cursor:pointer; transition:all 0.18s; font-family:'Inter',sans-serif; border:1px solid var(--border2); background:transparent; color:var(--text2); display:inline-flex; align-items:center; gap:5px; text-decoration:none; }
        .act-btn:hover { background:var(--bg4); color:var(--text); }
        .act-btn.orange { background:var(--orange-dim); border-color:rgba(249,115,22,0.2); color:var(--orange2); }
        .act-btn.orange:hover { background:var(--orange-dim2); }
        .input-wrap { padding:12px 24px 16px; border-top:1px solid var(--border); }
        .input-inner { max-width:660px; margin:0 auto; }
        .input-box { display:flex; align-items:flex-end; gap:8px; background:var(--bg2); border:1px solid var(--border2); border-radius:var(--r); padding:10px 12px; transition:border-color 0.2s; }
        .input-box:focus-within { border-color:rgba(249,115,22,0.45); box-shadow:0 0 0 3px rgba(249,115,22,0.06); }
        textarea#mainInput { flex:1; background:transparent; border:none; outline:none; color:var(--text); font-family:'Inter',sans-serif; font-size:0.9em; resize:none; line-height:1.55; padding:2px 0; max-height:130px; }
        textarea#mainInput::placeholder { color:var(--text3); }
        .char-count { font-size:0.65em; color:var(--text3); align-self:flex-end; padding-bottom:3px; flex-shrink:0; }
        .char-count.warn { color:var(--orange2); }
        .send-btn { width:34px; height:34px; border-radius:var(--r2); background:var(--orange); border:none; color:white; font-size:1.1em; cursor:pointer; transition:all 0.2s; display:flex; align-items:center; justify-content:center; flex-shrink:0; }
        .send-btn:hover { background:var(--orange2); transform:scale(1.06); }
        .send-btn:active { transform:scale(0.95); }
        .input-meta { display:flex; gap:7px; margin-top:7px; align-items:center; flex-wrap:wrap; }
        .neg-box { flex:1; display:flex; align-items:center; gap:6px; background:var(--bg2); border:1px solid var(--border); border-radius:var(--r2); padding:5px 10px; min-width:0; transition:border-color 0.2s; }
        .neg-box:focus-within { border-color:rgba(239,68,68,0.3); }
        .neg-lbl { font-size:0.68em; color:rgba(239,68,68,0.5); white-space:nowrap; font-weight:600; }
        #negInput { background:transparent; border:none; outline:none; color:var(--text); font-family:'Inter',sans-serif; font-size:0.8em; flex:1; min-width:0; }
        #negInput::placeholder { color:var(--text3); }
        .meta-btn { padding:5px 11px; background:transparent; border:1px solid var(--border); border-radius:var(--r2); color:var(--text3); font-size:0.74em; cursor:pointer; transition:all 0.18s; white-space:nowrap; font-family:'Inter',sans-serif; flex-shrink:0; }
        .meta-btn:hover { border-color:rgba(249,115,22,0.35); color:var(--orange2); background:var(--orange-dim); }
        .page-hdr { padding:18px 24px 14px; border-bottom:1px solid var(--border); display:flex; justify-content:space-between; align-items:center; flex-shrink:0; }
        .page-hdr h2 { font-size:1em; font-weight:600; }
        .page-hdr p { font-size:0.76em; color:var(--text3); margin-top:2px; }
        .hdr-btn { padding:7px 14px; background:var(--orange-dim); border:1px solid rgba(249,115,22,0.18); border-radius:var(--r2); color:var(--orange2); font-size:0.76em; font-weight:500; cursor:pointer; transition:all 0.18s; font-family:'Inter',sans-serif; }
        .hdr-btn:hover { background:var(--orange-dim2); }
        .gallery-body { flex:1; overflow-y:auto; padding:16px 24px; }
        .gallery-body::-webkit-scrollbar { width:4px; }
        .gallery-body::-webkit-scrollbar-thumb { background:rgba(255,255,255,0.08); border-radius:2px; }
        .search-box { width:100%; padding:8px 12px; background:var(--bg3); border:1px solid var(--border); border-radius:var(--r2); color:var(--text); font-family:'Inter',sans-serif; font-size:0.84em; outline:none; margin-bottom:14px; transition:border-color 0.2s; }
        .search-box:focus { border-color:rgba(249,115,22,0.35); }
        .search-box::placeholder { color:var(--text3); }
        .folders-row { display:flex; flex-wrap:wrap; gap:7px; margin-bottom:14px; }
        .folder-pill { display:flex; align-items:center; gap:5px; padding:5px 13px; border-radius:20px; border:1px solid var(--border); cursor:pointer; font-size:0.78em; color:var(--text2); transition:all 0.18s; user-select:none; }
        .folder-pill:hover { border-color:rgba(249,115,22,0.3); color:var(--text); }
        .folder-pill.active { background:var(--orange-dim); border-color:rgba(249,115,22,0.25); color:var(--orange2); font-weight:500; }
        .folder-badge { background:rgba(255,255,255,0.07); border-radius:10px; padding:1px 6px; font-size:0.82em; }
        .img-grid { display:grid; grid-template-columns:repeat(auto-fill,minmax(165px,1fr)); gap:10px; }
        .img-card { border-radius:var(--r); overflow:hidden; border:1px solid var(--border); background:var(--bg2); transition:all 0.2s; }
        .img-card:hover { border-color:rgba(249,115,22,0.25); transform:translateY(-2px); box-shadow:0 8px 24px rgba(0,0,0,0.3); }
        .img-card img { width:100%; height:145px; object-fit:cover; display:block; cursor:zoom-in; }
        .img-card-body { padding:8px; }
        .img-card-prompt { font-size:0.7em; color:var(--text3); white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
        .img-card-btns { display:flex; gap:4px; margin-top:6px; }
        .icb { flex:1; padding:4px; text-align:center; border-radius:4px; border:1px solid var(--border); font-size:0.66em; color:var(--text3); cursor:pointer; transition:all 0.18s; background:transparent; font-family:'Inter',sans-serif; text-decoration:none; display:flex; align-items:center; justify-content:center; }
        .icb:hover { background:var(--bg3); color:var(--text); }
        .hist-body { flex:1; overflow-y:auto; padding:16px 24px; }
        .hist-item { display:flex; align-items:center; gap:10px; padding:10px 13px; border-radius:var(--r); border:1px solid var(--border); background:var(--bg2); margin-bottom:6px; transition:all 0.18s; }
        .hist-item:hover { border-color:var(--border2); }
        .hist-icon { color:var(--text3); flex-shrink:0; }
        .hist-text { flex:1; font-size:0.85em; color:var(--text2); overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
        .hist-btn { padding:4px 10px; border-radius:var(--r3); border:1px solid var(--border); background:transparent; color:var(--text3); font-size:0.7em; cursor:pointer; transition:all 0.18s; font-family:'Inter',sans-serif; flex-shrink:0; }
        .hist-btn:hover { background:var(--orange-dim); border-color:rgba(249,115,22,0.25); color:var(--orange2); }
        .overlay { display:none; position:fixed; inset:0; background:rgba(0,0,0,0.6); z-index:1000; justify-content:center; align-items:center; backdrop-filter:blur(6px); }
        .overlay.open { display:flex; }
        .modal { background:var(--bg2); border:1px solid var(--border2); border-radius:14px; padding:24px; width:350px; max-width:92vw; animation:modalIn 0.2s ease; box-shadow:var(--shadow); }
        @keyframes modalIn { from{opacity:0;transform:scale(0.95)} to{opacity:1;transform:scale(1)} }
        .modal-hdr { display:flex; justify-content:space-between; align-items:center; margin-bottom:18px; }
        .modal-hdr h3 { font-size:0.96em; font-weight:600; }
        .modal-x { background:none; border:none; color:var(--text3); cursor:pointer; font-size:1.1em; padding:2px 5px; border-radius:4px; transition:all 0.15s; }
        .modal-x:hover { background:var(--bg4); color:var(--text); }
        .f-lbl { font-size:0.74em; color:var(--text2); margin-bottom:5px; font-weight:500; }
        .f-inp { width:100%; padding:9px 12px; background:var(--bg3); border:1px solid var(--border); border-radius:var(--r2); color:var(--text); font-family:'Inter',sans-serif; font-size:0.86em; outline:none; margin-bottom:12px; transition:border-color 0.2s; }
        .f-inp:focus { border-color:rgba(249,115,22,0.4); }
        .modal-foot { display:flex; gap:7px; margin-top:4px; }
        .btn { flex:1; padding:9px; border-radius:var(--r2); font-family:'Inter',sans-serif; font-size:0.78em; font-weight:500; cursor:pointer; transition:all 0.18s; border:none; }
        .btn-ghost { background:var(--bg4); color:var(--text2); border:1px solid var(--border) !important; }
        .btn-ghost:hover { color:var(--text); }
        .btn-orange { background:var(--orange); color:white; }
        .btn-orange:hover { background:var(--orange2); }
        .err-box { font-size:0.75em; color:#f87171; padding:7px 10px; background:rgba(239,68,68,0.08); border:1px solid rgba(239,68,68,0.15); border-radius:var(--r2); margin-bottom:10px; display:none; }
        .auth-foot { text-align:center; margin-top:12px; font-size:0.77em; color:var(--text3); }
        .auth-link { color:var(--orange2); cursor:pointer; }
        .auth-link:hover { text-decoration:underline; }
        .save-folders { display:flex; flex-wrap:wrap; gap:6px; margin-bottom:12px; }
        .sfbtn { padding:7px 12px; background:var(--bg3); border:1px solid var(--border); border-radius:var(--r2); color:var(--text2); font-size:0.8em; cursor:pointer; transition:all 0.18s; font-family:'Inter',sans-serif; }
        .sfbtn:hover { border-color:rgba(249,115,22,0.3); color:var(--orange2); background:var(--orange-dim); }
        .lightbox { display:none; position:fixed; inset:0; background:rgba(0,0,0,0.92); z-index:2000; justify-content:center; align-items:center; cursor:zoom-out; }
        .lightbox.open { display:flex; }
        .lightbox img { max-width:90vw; max-height:90vh; border-radius:var(--r); box-shadow:var(--shadow); }
        .toast { position:fixed; bottom:24px; right:24px; background:var(--bg3); border:1px solid var(--border2); border-radius:var(--r); padding:10px 16px; font-size:0.82em; color:var(--text); box-shadow:var(--shadow); z-index:3000; transform:translateY(80px); opacity:0; transition:all 0.3s ease; pointer-events:none; max-width:280px; }
        .toast.show { transform:translateY(0); opacity:1; }
        .toast.success { border-left:3px solid #4ade80; }
        .toast.error { border-left:3px solid #f87171; }
        .toast.info { border-left:3px solid var(--orange); }
        .empty { text-align:center; padding:50px 20px; color:var(--text3); }
        .empty-i { font-size:2.4em; margin-bottom:12px; }
        .empty p { font-size:0.84em; line-height:1.7; }
    </style>
</head>
<body>
<div id="particles"></div>
<div class="toast" id="toast"></div>
<div class="layout">
    <aside class="sidebar">
        <div class="logo-wrap">
            <div class="logo">
                <div class="logo-icon">&#10022;</div>
                <div><div class="logo-name">Astax</div><div class="logo-tag">Generative Image AI</div></div>
            </div>
        </div>
        <div class="sidebar-nav">
            <div class="sec-label">Navigation</div>
            <div class="nav-item active" id="nav-chat"><span>&#10022;</span> Creer</div>
            <div class="nav-item" id="nav-gallery"><span>&#8862;</span> Galerie <span class="badge" id="galBadge">0</span></div>
            <div class="nav-item" id="nav-history"><span>&#8635;</span> Historique <span class="badge" id="histBadge">0</span></div>
            <div class="nav-divider"></div>
            <div class="sec-label">Style rapide</div>
        </div>
        <div class="styles-wrap">
            <div class="style-chip on" data-style=""><span class="chip-dot"></span> Auto</div>
            <div class="style-chip" data-style="photorealistic, ultra detailed, 8k photography, sharp focus"><span class="chip-dot"></span> Realiste</div>
            <div class="style-chip" data-style="anime style, manga illustration, vibrant colors, studio ghibli"><span class="chip-dot"></span> Anime</div>
            <div class="style-chip" data-style="oil painting, impasto brushstrokes, museum quality art"><span class="chip-dot"></span> Peinture</div>
            <div class="style-chip" data-style="pixel art, 16-bit retro game style, crisp pixels"><span class="chip-dot"></span> Pixel Art</div>
            <div class="style-chip" data-style="cyberpunk, neon lights, rain reflections, futuristic dark city"><span class="chip-dot"></span> Cyberpunk</div>
            <div class="style-chip" data-style="watercolor painting, soft colors, dreamy illustration"><span class="chip-dot"></span> Aquarelle</div>
            <div class="style-chip" data-style="dark fantasy, dramatic lighting, epic cinematic moody scene"><span class="chip-dot"></span> Dark Fantasy</div>
            <div class="style-chip" data-style="minimalist design, clean geometric shapes, modern flat"><span class="chip-dot"></span> Minimaliste</div>
            <div class="style-chip" data-style="3d render, octane render, volumetric lighting, highly detailed"><span class="chip-dot"></span> 3D Render</div>
            <div class="style-chip" data-style="vintage photograph, film grain, 1970s color grading"><span class="chip-dot"></span> Vintage</div>
            <div class="style-chip" data-style="comic book style, bold outlines, halftone dots, superhero art"><span class="chip-dot"></span> Comics</div>
        </div>
        <div class="user-wrap">
            <div class="user-card" id="userCard">
                <div class="user-av guest" id="userAv">?</div>
                <div><div class="u-name" id="uName">Mode invite</div><div class="u-status" id="uStatus">Cliquer pour se connecter</div></div>
            </div>
        </div>
    </aside>
    <main class="main">
        <div class="page active" id="page-chat">
            <div class="chat-scroll" id="chatScroll">
                <div class="welcome" id="welcomeMsg">
                    <div class="welcome-orb">&#10022;</div>
                    <h2>Qu'est-ce qu'on cree aujourd'hui ?</h2>
                    <p>Decris ton idee, je vais te poser quelques questions pour affiner ta vision et generer l'image parfaite.</p>
                    <div class="quick-prompts">
                        <div class="qchip" data-prompt="Un paysage de montagne au coucher de soleil">Montagne</div>
                        <div class="qchip" data-prompt="Un personnage de science-fiction futuriste">Sci-Fi</div>
                        <div class="qchip" data-prompt="Un animal fantastique dans une foret enchantee">Fantasy</div>
                        <div class="qchip" data-prompt="Une ville futuriste vue du ciel la nuit">Ville</div>
                        <div class="qchip" data-prompt="Un portrait artistique expressif">Portrait</div>
                        <div class="qchip" data-prompt="Une scene sous-marine mysterieuse">Ocean</div>
                    </div>
                </div>
                <div class="messages" id="messages"></div>
                <div class="progress-card" id="progressCard">
                    <div class="progress-top">
                        <span class="progress-lbl" id="progressLbl">Generation en cours...</span>
                        <span class="progress-timer" id="progressTimer">0s</span>
                    </div>
                    <div class="pbar"><div class="pbar-fill"></div></div>
                </div>
            </div>
            <div class="input-wrap">
                <div class="input-inner">
                    <div class="input-box">
                        <textarea id="mainInput" rows="1" placeholder="Decris ce que tu veux creer..."></textarea>
                        <span class="char-count" id="charCount">0</span>
                        <button class="send-btn" id="sendBtn">&#8593;</button>
                    </div>
                    <div class="input-meta">
                        <div class="neg-box">
                            <span class="neg-lbl">X</span>
                            <input type="text" id="negInput" placeholder="Exclure : flou, texte, deforme...">
                        </div>
                        <button class="meta-btn" id="inspireBtn">Inspire</button>
                        <button class="meta-btn" id="newChatBtn">Nouveau</button>
                    </div>
                </div>
            </div>
        </div>
        <div class="page" id="page-gallery">
            <div class="page-hdr">
                <div><h2>Galerie</h2><p>Tes creations organisees par projet</p></div>
                <button class="hdr-btn" id="newFolderBtn">+ Nouveau dossier</button>
            </div>
            <div class="gallery-body">
                <input type="text" class="search-box" id="searchBox" placeholder="Rechercher par prompt...">
                <div class="folders-row" id="foldersList"></div>
                <div class="img-grid" id="imagesGrid"></div>
            </div>
        </div>
        <div class="page" id="page-history">
            <div class="page-hdr">
                <div><h2>Historique</h2><p id="histCount">0 prompts</p></div>
                <button class="hdr-btn" id="clearHistBtn">Effacer tout</button>
            </div>
            <div class="hist-body" id="histList"></div>
        </div>
    </main>
</div>
<div class="lightbox" id="lightbox"><img id="lbImg" src="" alt=""></div>
<div class="overlay" id="authOverlay">
    <div class="modal">
        <div class="modal-hdr"><h3 id="authTitle">Connexion</h3><button class="modal-x" id="authX">X</button></div>
        <div class="err-box" id="authErr"></div>
        <div class="f-lbl">Nom d'utilisateur</div>
        <input type="text" class="f-inp" id="authUser" placeholder="johndoe" autocomplete="username">
        <div class="f-lbl">Mot de passe</div>
        <input type="password" class="f-inp" id="authPass" placeholder="••••••••" autocomplete="current-password">
        <div class="modal-foot">
            <button class="btn btn-ghost" id="authCancel">Annuler</button>
            <button class="btn btn-orange" id="authAction">Se connecter</button>
        </div>
        <div class="auth-foot"><span id="authSwTxt">Pas de compte ?</span> <span class="auth-link" id="authSwLink">S inscrire</span></div>
    </div>
</div>
<div class="overlay" id="folderOverlay">
    <div class="modal">
        <div class="modal-hdr"><h3>Nouveau dossier</h3><button class="modal-x" id="folderX">X</button></div>
        <div class="f-lbl">Nom du projet</div>
        <input type="text" class="f-inp" id="folderName" placeholder="ex: Mes paysages">
        <div class="modal-foot">
            <button class="btn btn-ghost" id="folderCancel">Annuler</button>
            <button class="btn btn-orange" id="folderConfirm">Creer</button>
        </div>
    </div>
</div>
<div class="overlay" id="saveOverlay">
    <div class="modal">
        <div class="modal-hdr"><h3>Sauvegarder dans...</h3><button class="modal-x" id="saveX">X</button></div>
        <div class="save-folders" id="saveFolders"></div>
        <div class="modal-foot"><button class="btn btn-ghost" id="saveCancel">Annuler</button></div>
    </div>
</div>
<script>
var conv = [], currentFolder = null, selectedStyle = "", authMode = "login";
var currentUser = null, hist = [], pendingUrl = null, pendingPrompt = null;
var genTimer = null, genStart = 0, galleryData = {};

var inspirePool = [
    "Un astronaute solitaire explorant une planete alien au coucher de soleil",
    "Une bibliotheque ancienne et magique flottant dans les nuages",
    "Un dragon de cristal endormi dans une foret lumineuse",
    "Une ville sous-marine futuriste peuplee de creatures bioluminescentes",
    "Un titan mecanique gardant les ruines d'une cite ancienne",
    "Une foret de champignons geants sous une lune violette",
    "Un robot peintre creant une fresque dans un desert de sel",
    "Un samurai fantome dans une foret de cerisiers enneiges",
    "Un marche de magie nocturne dans une ruelle medievale",
    "Un cafe dans une station spatiale avec vue sur la Terre"
];

window.addEventListener("load", function() {
    var pc = document.getElementById("particles");
    for (var i = 0; i < 15; i++) {
        var p = document.createElement("div");
        p.className = "particle";
        p.style.left = Math.random() * 100 + "%";
        p.style.animationDuration = (12 + Math.random() * 20) + "s";
        p.style.animationDelay = (Math.random() * 15) + "s";
        pc.appendChild(p);
    }
    try { hist = JSON.parse(localStorage.getItem("astax_h") || "[]"); } catch(e) { hist = []; }
    updateBadges();

    document.getElementById("nav-chat").addEventListener("click", function() { showPage("chat"); });
    document.getElementById("nav-gallery").addEventListener("click", function() { showPage("gallery"); });
    document.getElementById("nav-history").addEventListener("click", function() { showPage("history"); });

    document.querySelectorAll(".style-chip").forEach(function(chip) {
        chip.addEventListener("click", function() {
            document.querySelectorAll(".style-chip").forEach(function(c) { c.classList.remove("on"); });
            chip.classList.add("on");
            selectedStyle = chip.getAttribute("data-style");
        });
    });

    document.querySelectorAll(".qchip").forEach(function(chip) {
        chip.addEventListener("click", function() {
            var inp = document.getElementById("mainInput");
            inp.value = chip.getAttribute("data-prompt");
            autoResize(inp);
            inp.focus();
        });
    });

    document.getElementById("sendBtn").addEventListener("click", envoyer);
    document.getElementById("mainInput").addEventListener("keydown", function(e) {
        if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); envoyer(); }
    });
    document.getElementById("mainInput").addEventListener("input", function() {
        autoResize(this);
        var n = this.value.length;
        var cc = document.getElementById("charCount");
        cc.innerText = n;
        cc.className = "char-count" + (n > 400 ? " warn" : "");
    });

    document.getElementById("inspireBtn").addEventListener("click", function() {
        var inp = document.getElementById("mainInput");
        inp.value = inspirePool[Math.floor(Math.random() * inspirePool.length)];
        autoResize(inp);
        inp.focus();
    });

    document.getElementById("newChatBtn").addEventListener("click", function() {
        conv = [];
        document.getElementById("messages").innerHTML = "";
        document.getElementById("welcomeMsg").style.display = "";
        document.getElementById("progressCard").style.display = "none";
        toast("Nouvelle conversation", "info");
    });

    document.getElementById("newFolderBtn").addEventListener("click", openCreateFolder);
    document.getElementById("searchBox").addEventListener("input", function() { renderGallery(galleryData); });

    document.getElementById("clearHistBtn").addEventListener("click", function() {
        hist = [];
        try { localStorage.removeItem("astax_h"); } catch(e) {}
        if (currentUser) saveHistServer();
        updateBadges();
        renderHistory();
        toast("Historique efface", "info");
    });

    document.getElementById("authX").addEventListener("click", function() { closeOverlay("authOverlay"); });
    document.getElementById("authCancel").addEventListener("click", function() { closeOverlay("authOverlay"); });
    document.getElementById("authAction").addEventListener("click", doAuth);
    document.getElementById("authSwLink").addEventListener("click", toggleAuthMode);
    document.getElementById("authPass").addEventListener("keydown", function(e) { if (e.key === "Enter") doAuth(); });

    document.getElementById("folderX").addEventListener("click", function() { closeOverlay("folderOverlay"); });
    document.getElementById("folderCancel").addEventListener("click", function() { closeOverlay("folderOverlay"); });
    document.getElementById("folderConfirm").addEventListener("click", createFolder);
    document.getElementById("folderName").addEventListener("keydown", function(e) { if (e.key === "Enter") createFolder(); });

    document.getElementById("saveX").addEventListener("click", function() { closeOverlay("saveOverlay"); });
    document.getElementById("saveCancel").addEventListener("click", function() { closeOverlay("saveOverlay"); });
    document.getElementById("userCard").addEventListener("click", userCardClick);
    document.getElementById("lightbox").addEventListener("click", function() {
        document.getElementById("lightbox").classList.remove("open");
    });

    fetch("/me").then(function(r) { return r.json(); }).then(function(d) {
        if (d.username) {
            setLoggedIn(d.username);
            if (d.prompt_history && d.prompt_history.length) { hist = d.prompt_history; updateBadges(); }
        }
    });
});

function autoResize(el) { el.style.height = "auto"; el.style.height = Math.min(el.scrollHeight, 130) + "px"; }
function scrollDown() { var s = document.getElementById("chatScroll"); s.scrollTop = s.scrollHeight; }
function openOverlay(id) { document.getElementById(id).classList.add("open"); }
function closeOverlay(id) { document.getElementById(id).classList.remove("open"); }
function openLightbox(src) { document.getElementById("lbImg").src = src; document.getElementById("lightbox").classList.add("open"); }

function toast(msg, type) {
    var t = document.getElementById("toast");
    t.innerText = msg;
    t.className = "toast " + (type || "info");
    t.classList.add("show");
    setTimeout(function() { t.classList.remove("show"); }, 3000);
}

function updateBadges() {
    var hb = document.getElementById("histBadge");
    if (hist.length) { hb.innerText = hist.length; hb.classList.add("on"); } else { hb.classList.remove("on"); }
}

function showPage(p) {
    document.querySelectorAll(".page").forEach(function(el) { el.classList.remove("active"); });
    document.querySelectorAll(".nav-item").forEach(function(el) { el.classList.remove("active"); });
    document.getElementById("page-" + p).classList.add("active");
    document.getElementById("nav-" + p).classList.add("active");
    if (p === "gallery") loadGallery();
    if (p === "history") renderHistory();
}

function hideWelcome() { document.getElementById("welcomeMsg").style.display = "none"; }

function addMsg(role, text) {
    hideWelcome();
    var msgs = document.getElementById("messages");
    var row = document.createElement("div"); row.className = "msg-row " + role;
    var av = document.createElement("div"); av.className = "msg-av " + role; av.innerText = role === "bot" ? "✦" : "✎";
    var bbl = document.createElement("div"); bbl.className = "msg-bbl " + role; bbl.innerText = text;
    row.appendChild(av); row.appendChild(bbl); msgs.appendChild(row); scrollDown();
}

function showTyping() {
    hideWelcome();
    var msgs = document.getElementById("messages");
    var row = document.createElement("div"); row.className = "msg-row bot"; row.id = "typingRow";
    var av = document.createElement("div"); av.className = "msg-av bot"; av.innerText = "✦";
    var bbl = document.createElement("div"); bbl.className = "msg-bbl bot typing";
    bbl.innerHTML = "<span></span><span></span><span></span>";
    row.appendChild(av); row.appendChild(bbl); msgs.appendChild(row); scrollDown();
}

function removeTyping() { var t = document.getElementById("typingRow"); if (t) t.remove(); }

function addImageResult(imgUrl, prompt, count, idx) {
    var msgs = document.getElementById("messages");
    var card = document.createElement("div"); card.className = "img-result";
    var img = document.createElement("img"); img.src = imgUrl; img.title = "Cliquer pour agrandir";
    img.addEventListener("click", function() { openLightbox(imgUrl); });
    var meta = document.createElement("div"); meta.className = "img-meta";
    var pused = document.createElement("div"); pused.className = "img-prompt-used";
    pused.innerText = (count > 1 ? "Image " + (idx+1) + "/" + count + " - " : "") + prompt.substring(0, 100) + (prompt.length > 100 ? "..." : "");
    var actions = document.createElement("div"); actions.className = "img-actions";

    var dlA = document.createElement("a");
    dlA.href = imgUrl; dlA.download = "astax-" + Date.now() + ".png";
    dlA.className = "act-btn"; dlA.innerText = "Telecharger";

    var saveBtn = document.createElement("button");
    saveBtn.className = "act-btn orange"; saveBtn.innerText = "Sauvegarder";
    var cu = imgUrl, cp = prompt;
    saveBtn.addEventListener("click", function() {
        if (!currentUser) { toast("Connecte-toi pour sauvegarder !", "error"); return; }
        pendingUrl = cu; pendingPrompt = cp; openSaveModal();
    });

    var copyBtn = document.createElement("button");
    copyBtn.className = "act-btn"; copyBtn.innerText = "Copier prompt";
    copyBtn.addEventListener("click", function() {
        navigator.clipboard.writeText(prompt).then(function() { toast("Prompt copie !", "success"); });
    });

    var regenBtn = document.createElement("button");
    regenBtn.className = "act-btn"; regenBtn.innerText = "Regenerer";
    var rp = prompt, rn = document.getElementById("negInput").value;
    regenBtn.addEventListener("click", function() { addMsg("bot", "Je regenere..."); startGen(rp, rn, 1, 0); });

    actions.appendChild(dlA); actions.appendChild(saveBtn);
    actions.appendChild(copyBtn); actions.appendChild(regenBtn);
    meta.appendChild(pused); meta.appendChild(actions);
    card.appendChild(img); card.appendChild(meta);
    msgs.appendChild(card); scrollDown();
}

function envoyer() {
    var inp = document.getElementById("mainInput");
    var text = inp.value.trim();
    if (!text) return;
    addMsg("user", text);
    conv.push({role:"user", content:text});
    inp.value = ""; inp.style.height = "auto";
    document.getElementById("charCount").innerText = "0";
    showTyping();
    fetch("/chat", {
        method:"POST", headers:{"Content-Type":"application/json"},
        body: JSON.stringify({messages:conv, style:selectedStyle})
    }).then(function(r) { return r.json(); }).then(function(d) {
        removeTyping();
        if (d.type === "question") {
            addMsg("bot", d.message);
            conv.push({role:"assistant", content:d.message});
        } else if (d.type === "generate") {
            addMsg("bot", d.message);
            conv.push({role:"assistant", content:d.message});
            addToHistory(d.prompt);
            startGen(d.prompt, document.getElementById("negInput").value.trim(), d.count||1, 0);
        }
    }).catch(function() { removeTyping(); toast("Erreur de connexion", "error"); });
}

function startGen(prompt, neg, count, idx) {
    var pc = document.getElementById("progressCard");
    var pl = document.getElementById("progressLbl");
    var pt = document.getElementById("progressTimer");
    pc.style.display = "block";
    pl.innerText = count > 1 ? "Generation " + (idx+1) + "/" + count + "..." : "Generation en cours...";
    genStart = Date.now();
    if (genTimer) clearInterval(genTimer);
    genTimer = setInterval(function() { pt.innerText = ((Date.now()-genStart)/1000).toFixed(1) + "s"; }, 100);
    fetch("/generate", {
        method:"POST", headers:{"Content-Type":"application/json"},
        body: JSON.stringify({prompt:prompt, negative_prompt:neg, style:selectedStyle})
    }).then(function(r) {
        if (!r.ok) throw new Error("fail");
        return r.blob();
    }).then(function(blob) {
        clearInterval(genTimer);
        var elapsed = ((Date.now()-genStart)/1000).toFixed(1);
        pt.innerText = elapsed + "s OK";
        addImageResult(URL.createObjectURL(blob), prompt, count, idx);
        if (idx + 1 < count) {
            setTimeout(function() { startGen(prompt, neg, count, idx+1); }, 300);
        } else {
            pc.style.display = "none"; conv = [];
            toast(count + " image" + (count>1?"s":"") + " en " + elapsed + "s !", "success");
        }
    }).catch(function() { clearInterval(genTimer); pc.style.display = "none"; toast("Erreur generation", "error"); });
}

function addToHistory(prompt) {
    hist = [prompt].concat(hist.filter(function(p) { return p !== prompt; })).slice(0, 25);
    try { localStorage.setItem("astax_h", JSON.stringify(hist)); } catch(e) {}
    if (currentUser) saveHistServer();
    updateBadges();
}

function saveHistServer() {
    fetch("/save-history", {method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify({history:hist})});
}

function renderHistory() {
    var list = document.getElementById("histList");
    document.getElementById("histCount").innerText = hist.length + " prompt" + (hist.length > 1 ? "s" : "");
    list.innerHTML = "";
    if (!hist.length) {
        list.innerHTML = "<div class='empty'><div class='empty-i'>&#8635;</div><p>Aucun prompt encore.<br>Genere ta premiere image !</p></div>";
        return;
    }
    hist.forEach(function(p) {
        var item = document.createElement("div"); item.className = "hist-item";
        var icon = document.createElement("span"); icon.className = "hist-icon"; icon.innerText = "✦";
        var txt = document.createElement("span"); txt.className = "hist-text"; txt.innerText = p;
        var btn = document.createElement("button"); btn.className = "hist-btn"; btn.innerText = "Reutiliser";
        var cap = p;
        btn.addEventListener("click", function() {
            document.getElementById("mainInput").value = cap;
            autoResize(document.getElementById("mainInput"));
            showPage("chat");
        });
        item.appendChild(icon); item.appendChild(txt); item.appendChild(btn);
        list.appendChild(item);
    });
}

function loadGallery() {
    if (!currentUser) {
        document.getElementById("foldersList").innerHTML = "<div class='empty' style='width:100%'><div class='empty-i'>&#128274;</div><p>Connecte-toi<br>pour acceder a ta galerie</p></div>";
        document.getElementById("imagesGrid").innerHTML = "";
        return;
    }
    fetch("/galleries").then(function(r) { return r.json(); }).then(function(d) { galleryData = d; renderGallery(d); });
}

function renderGallery(data) {
    var fList = document.getElementById("foldersList");
    var iGrid = document.getElementById("imagesGrid");
    fList.innerHTML = ""; iGrid.innerHTML = "";
    var keys = Object.keys(data);
    if (!keys.length) {
        fList.innerHTML = "<div class='empty' style='width:100%'><div class='empty-i'>&#8862;</div><p>Aucun dossier.<br>Cree ton premier projet !</p></div>";
        return;
    }
    keys.forEach(function(name) {
        var pill = document.createElement("div");
        pill.className = "folder-pill" + (currentFolder === name ? " active" : "");
        pill.innerHTML = "&#128193; " + name + " <span class='folder-badge'>" + data[name].length + "</span>";
        var cap = name;
        pill.addEventListener("click", function() { currentFolder = cap; renderGallery(galleryData); });
        fList.appendChild(pill);
    });
    if (!currentFolder || !data[currentFolder]) return;
    var search = document.getElementById("searchBox").value.toLowerCase();
    var images = data[currentFolder].filter(function(img) { return !search || img.prompt.toLowerCase().includes(search); });
    if (!images.length) { iGrid.innerHTML = "<div class='empty'><div class='empty-i'>&#128444;</div><p>Aucune image ici</p></div>"; return; }
    images.forEach(function(img) {
        var card = document.createElement("div"); card.className = "img-card";
        var imgEl = document.createElement("img"); imgEl.src = img.image_b64;
        imgEl.addEventListener("click", function() { openLightbox(img.image_b64); });
        var body = document.createElement("div"); body.className = "img-card-body";
        var pEl = document.createElement("div"); pEl.className = "img-card-prompt"; pEl.innerText = img.prompt; pEl.title = img.prompt;
        var btns = document.createElement("div"); btns.className = "img-card-btns";
        var dlA = document.createElement("a"); dlA.href = img.image_b64; dlA.download = "astax.png"; dlA.className = "icb"; dlA.innerText = "DL";
        var delB = document.createElement("button"); delB.className = "icb"; delB.innerText = "X";
        var cf = currentFolder, ci = img.id;
        delB.addEventListener("click", function(e) {
            e.stopPropagation();
            fetch("/delete-image", {method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify({folder:cf, id:ci})})
            .then(function() { loadGallery(); toast("Image supprimee", "info"); });
        });
        btns.appendChild(dlA); btns.appendChild(delB);
        body.appendChild(pEl); body.appendChild(btns);
        card.appendChild(imgEl); card.appendChild(body);
        iGrid.appendChild(card);
    });
}

function openCreateFolder() {
    if (!currentUser) { toast("Connecte-toi dabord !", "error"); return; }
    document.getElementById("folderName").value = "";
    openOverlay("folderOverlay");
    setTimeout(function() { document.getElementById("folderName").focus(); }, 100);
}

function createFolder() {
    var name = document.getElementById("folderName").value.trim();
    if (!name) return;
    fetch("/create-folder", {method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify({name:name})})
    .then(function() { closeOverlay("folderOverlay"); loadGallery(); toast("Dossier cree !", "success"); });
}

function openSaveModal() {
    fetch("/galleries").then(function(r) { return r.json(); }).then(function(data) {
        var list = document.getElementById("saveFolders"); list.innerHTML = "";
        var keys = Object.keys(data);
        if (!keys.length) {
            list.innerHTML = "<span style='font-size:0.82em;color:var(--text3)'>Aucun dossier - cree-en un dans la galerie !</span>";
        } else {
            keys.forEach(function(name) {
                var btn = document.createElement("button"); btn.className = "sfbtn"; btn.innerText = name;
                var cap = name;
                btn.addEventListener("click", function() {
                    fetch(pendingUrl).then(function(r) { return r.blob(); }).then(function(blob) {
                        var reader = new FileReader();
                        reader.onloadend = function() {
                            fetch("/save-image", {method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify({folder:cap, image_b64:reader.result, prompt:pendingPrompt})})
                            .then(function() { closeOverlay("saveOverlay"); toast("Sauvegardee dans " + cap + " !", "success"); });
                        };
                        reader.readAsDataURL(blob);
                    });
                });
                list.appendChild(btn);
            });
        }
        openOverlay("saveOverlay");
    });
}

function userCardClick() { if (currentUser) logout(); else openAuthModal(); }

function openAuthModal() {
    authMode = "login";
    document.getElementById("authTitle").innerText = "Connexion";
    document.getElementById("authAction").innerText = "Se connecter";
    document.getElementById("authSwTxt").innerText = "Pas de compte ?";
    document.getElementById("authSwLink").innerText = "S inscrire";
    document.getElementById("authErr").style.display = "none";
    document.getElementById("authUser").value = "";
    document.getElementById("authPass").value = "";
    openOverlay("authOverlay");
    setTimeout(function() { document.getElementById("authUser").focus(); }, 100);
}

function toggleAuthMode() {
    authMode = authMode === "login" ? "register" : "login";
    var isL = authMode === "login";
    document.getElementById("authTitle").innerText = isL ? "Connexion" : "Inscription";
    document.getElementById("authAction").innerText = isL ? "Se connecter" : "S inscrire";
    document.getElementById("authSwTxt").innerText = isL ? "Pas de compte ?" : "Deja un compte ?";
    document.getElementById("authSwLink").innerText = isL ? "S inscrire" : "Se connecter";
    document.getElementById("authErr").style.display = "none";
}

function doAuth() {
    var user = document.getElementById("authUser").value.trim();
    var pass = document.getElementById("authPass").value;
    if (!user || !pass) return;
    fetch(authMode === "login" ? "/login" : "/register", {
        method:"POST", headers:{"Content-Type":"application/json"},
        body:JSON.stringify({username:user, password:pass})
    }).then(function(r) { return r.json(); }).then(function(d) {
        if (d.success) {
            setLoggedIn(user);
            if (d.prompt_history) { hist = d.prompt_history; updateBadges(); }
            closeOverlay("authOverlay");
            toast(authMode === "login" ? "Bon retour " + user + " !" : "Bienvenue " + user + " !", "success");
        } else {
            var e = document.getElementById("authErr"); e.innerText = d.error; e.style.display = "block";
        }
    });
}

function setLoggedIn(username) {
    currentUser = username;
    var av = document.getElementById("userAv");
    av.innerText = username[0].toUpperCase(); av.className = "user-av";
    document.getElementById("uName").innerText = username;
    document.getElementById("uStatus").innerText = "Connecte - cliquer pour deconnecter";
}

function logout() {
    fetch("/logout", {method:"POST"}).then(function() {
        currentUser = null;
        var av = document.getElementById("userAv"); av.innerText = "?"; av.className = "user-av guest";
        document.getElementById("uName").innerText = "Mode invite";
        document.getElementById("uStatus").innerText = "Cliquer pour se connecter";
        try { hist = JSON.parse(localStorage.getItem("astax_h") || "[]"); } catch(e) { hist = []; }
        updateBadges();
        toast("Deconnecte. A bientot !", "info");
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
    style_hint = " Style visuel choisi : " + style + "." if style else ""
    system = "Tu es un assistant creatif qui aide a creer des images avec une IA generative." + style_hint + """
Pose des questions precises en francais, puis genere un prompt detaille en anglais.
Regles STRICTES :
- Reponds TOUJOURS en francais
- UNE seule question courte a la fois
- Maximum 3 questions avant de generer
- Apres 3 questions maximum, genere OBLIGATOIREMENT
- Reponds UNIQUEMENT avec ce format exact sur 3 lignes separees :
GENERATE: [prompt anglais ultra detaille]
COUNT: [nombre entre 1 et 5]
MESSAGE: [phrase courte enthousiaste en francais]"""
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
            if line.startswith("GENERATE:"): prompt = line[9:].strip()
            elif line.startswith("COUNT:"):
                try: count = max(1, min(5, int(line[6:].strip())))
                except: count = 1
            elif line.startswith("MESSAGE:"): message = line[8:].strip()
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
    if u and u in users: return jsonify({"username": u, "prompt_history": users[u].get("prompt_history", [])})
    return jsonify({"username": None})

@app.route("/register", methods=["POST"])
def register():
    d = request.json
    u, p = d.get("username", "").strip(), d.get("password", "")
    if not u or not p: return jsonify({"success": False, "error": "Remplis tous les champs."})
    if len(p) < 6: return jsonify({"success": False, "error": "Mot de passe trop court (6 min)."})
    if u in users: return jsonify({"success": False, "error": "Nom deja pris."})
    users[u] = {"password_hash": hash_password(p), "galleries": {}, "prompt_history": []}
    session["username"] = u
    return jsonify({"success": True})

@app.route("/login", methods=["POST"])
def login():
    d = request.json
    u, p = d.get("username", "").strip(), d.get("password", "")
    if u not in users: return jsonify({"success": False, "error": "Utilisateur introuvable."})
    if users[u]["password_hash"] != hash_password(p): return jsonify({"success": False, "error": "Mot de passe incorrect."})
    session["username"] = u
    return jsonify({"success": True, "prompt_history": users[u].get("prompt_history", [])})

@app.route("/logout", methods=["POST"])
def logout():
    session.pop("username", None)
    return jsonify({"success": True})

@app.route("/galleries")
def get_galleries():
    u = session.get("username")
    if u and u in users: return jsonify(users[u]["galleries"])
    return jsonify({})

@app.route("/create-folder", methods=["POST"])
def create_folder():
    u = session.get("username")
    if not u: return jsonify({"success": False})
    name = request.json.get("name", "").strip()
    if name and name not in users[u]["galleries"]: users[u]["galleries"][name] = []
    return jsonify({"success": True})

@app.route("/save-image", methods=["POST"])
def save_image():
    u = session.get("username")
    if not u: return jsonify({"success": False})
    d = request.json
    folder = d.get("folder")
    if folder in users[u]["galleries"]:
        users[u]["galleries"][folder].append({
            "id": str(uuid.uuid4()),
            "image_b64": d.get("image_b64"),
            "prompt": d.get("prompt", "")
        })
    return jsonify({"success": True})

@app.route("/delete-image", methods=["POST"])
def delete_image():
    u = session.get("username")
    if not u: return jsonify({"success": False})
    d = request.json
    folder, iid = d.get("folder"), d.get("id")
    if folder in users[u]["galleries"]:
        users[u]["galleries"][folder] = [i for i in users[u]["galleries"][folder] if str(i["id"]) != str(iid)]
    return jsonify({"success": True})

@app.route("/save-history", methods=["POST"])
def save_history():
    u = session.get("username")
    if u and u in users: users[u]["prompt_history"] = request.json.get("history", [])
    return jsonify({"success": True})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=7860)
