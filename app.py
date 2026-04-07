import os
import io
import uuid
import hashlib
import time
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
            --bg:#161616; --bg2:#1e1e1e; --bg3:#262626; --bg4:#2e2e2e;
            --border:rgba(255,255,255,0.07); --border2:rgba(255,255,255,0.12);
            --orange:#f97316; --orange2:#fb923c; --orange3:#fdba74;
            --orange-dim:rgba(249,115,22,0.1); --orange-dim2:rgba(249,115,22,0.18);
            --text:#f0f0f0; --text2:rgba(255,255,255,0.55); --text3:rgba(255,255,255,0.3);
            --r:10px; --r2:7px; --r3:5px;
            --shadow:0 4px 24px rgba(0,0,0,0.4);
            --shadow-orange:0 4px 20px rgba(249,115,22,0.25);
        }
        body { background:var(--bg); color:var(--text); font-family:'Inter',sans-serif; height:100vh; display:flex; flex-direction:column; overflow:hidden; font-size:14px; line-height:1.5; }

        /* PARTICLES */
        #particles { position:fixed; inset:0; z-index:0; pointer-events:none; overflow:hidden; }
        .particle { position:absolute; width:2px; height:2px; background:var(--orange); border-radius:50%; opacity:0; animation:float linear infinite; }
        @keyframes float {
            0% { transform:translateY(100vh) translateX(0); opacity:0; }
            10% { opacity:0.4; }
            90% { opacity:0.1; }
            100% { transform:translateY(-100px) translateX(40px); opacity:0; }
        }

        /* LAYOUT */
        .layout { display:flex; flex:1; overflow:hidden; position:relative; z-index:1; }

        /* ── SIDEBAR ── */
        .sidebar { width:232px; background:var(--bg2); border-right:1px solid var(--border); display:flex; flex-direction:column; flex-shrink:0; }

        .logo-wrap { padding:18px 16px 16px; border-bottom:1px solid var(--border); }
        .logo { display:flex; align-items:center; gap:10px; }
        .logo-icon {
            width:36px; height:36px;
            background:linear-gradient(135deg, var(--orange), #dc2626);
            border-radius:10px; display:flex; align-items:center; justify-content:center;
            font-size:17px; flex-shrink:0; box-shadow:var(--shadow-orange);
            transition:transform 0.3s;
        }
        .logo-icon:hover { transform:rotate(15deg) scale(1.05); }
        .logo-name { font-weight:700; font-size:1.08em; letter-spacing:0.3px; }
        .logo-tag { font-size:0.64em; color:var(--text3); margin-top:1px; letter-spacing:0.5px; }

        .sidebar-nav { padding:12px 10px 0; }
        .section-label { font-size:0.6em; color:var(--text3); letter-spacing:1.8px; text-transform:uppercase; padding:0 6px; margin:10px 0 5px; font-weight:600; }
        .nav-item {
            display:flex; align-items:center; gap:9px; padding:8px 10px;
            border-radius:var(--r2); cursor:pointer; color:var(--text2);
            font-size:0.87em; font-weight:500; transition:all 0.18s;
            margin-bottom:1px; border:1px solid transparent; user-select:none;
            position:relative;
        }
        .nav-item:hover { background:var(--bg3); color:var(--text); }
        .nav-item.active { background:var(--orange-dim); color:var(--orange2); border-color:rgba(249,115,22,0.12); }
        .nav-item .badge {
            margin-left:auto; background:var(--orange); color:white;
            font-size:0.65em; padding:1px 6px; border-radius:10px; font-weight:600;
            display:none;
        }
        .nav-item .badge.show { display:inline; }

        .nav-divider { height:1px; background:var(--border); margin:10px 6px; }

        .styles-wrap { padding:0 10px; flex:1; overflow-y:auto; }
        .styles-wrap::-webkit-scrollbar { width:3px; }
        .styles-wrap::-webkit-scrollbar-thumb { background:rgba(255,255,255,0.08); border-radius:2px; }

        .style-chip {
            display:flex; align-items:center; gap:8px; padding:7px 10px;
            border-radius:var(--r2); cursor:pointer; color:var(--text2);
            font-size:0.82em; transition:all 0.18s; margin-bottom:1px; user-select:none;
        }
        .style-chip:hover { background:var(--bg3); color:var(--text); }
        .style-chip.selected { color:var(--orange2); background:var(--orange-dim); font-weight:500; }
        .style-chip .chip-dot { width:6px; height:6px; border-radius:50%; background:var(--text3); flex-shrink:0; transition:background 0.2s; }
        .style-chip.selected .chip-dot { background:var(--orange); }

        /* User card */
        .user-wrap { padding:10px; border-top:1px solid var(--border); margin-top:auto; }
        .user-card {
            display:flex; align-items:center; gap:9px; padding:9px 10px;
            border-radius:var(--r2); background:var(--bg3); cursor:pointer;
            transition:all 0.18s; user-select:none; border:1px solid transparent;
        }
        .user-card:hover { border-color:var(--border2); }
        .user-avatar {
            width:30px; height:30px; border-radius:50%; flex-shrink:0;
            display:flex; align-items:center; justify-content:center;
            font-size:0.8em; font-weight:700;
            background:linear-gradient(135deg, var(--orange), #dc2626);
        }
        .user-avatar.guest { background:var(--bg4); font-size:1em; }
        .u-name { font-size:0.84em; font-weight:500; }
        .u-status { font-size:0.68em; color:var(--text3); margin-top:1px; }

        /* ── MAIN ── */
        .main { flex:1; display:flex; flex-direction:column; overflow:hidden; min-width:0; }
        .page { display:none; flex:1; flex-direction:column; overflow:hidden; }
        .page.active { display:flex; }

        /* ── CHAT PAGE ── */
        .chat-scroll { flex:1; overflow-y:auto; padding:24px 24px 8px; }
        .chat-scroll::-webkit-scrollbar { width:5px; }
        .chat-scroll::-webkit-scrollbar-thumb { background:rgba(255,255,255,0.08); border-radius:3px; }

        /* Welcome */
        .welcome {
            display:flex; flex-direction:column; align-items:center;
            justify-content:center; padding:60px 20px 40px; text-align:center;
        }
        .welcome-orb {
            width:64px; height:64px; border-radius:18px;
            background:linear-gradient(135deg, var(--orange), #dc2626);
            display:flex; align-items:center; justify-content:center;
            font-size:26px; margin-bottom:18px;
            box-shadow:var(--shadow-orange);
            animation:orbPulse 3s ease-in-out infinite;
        }
        @keyframes orbPulse { 0%,100%{box-shadow:0 4px 20px rgba(249,115,22,0.25)} 50%{box-shadow:0 4px 32px rgba(249,115,22,0.45)} }
        .welcome h2 { font-size:1.35em; font-weight:600; margin-bottom:8px; }
        .welcome p { color:var(--text2); font-size:0.88em; max-width:360px; line-height:1.65; }

        /* Quick prompts */
        .quick-prompts { display:flex; flex-wrap:wrap; gap:7px; justify-content:center; margin-top:20px; }
        .quick-chip {
            padding:6px 13px; border-radius:20px; border:1px solid var(--border2);
            font-size:0.78em; color:var(--text2); cursor:pointer; transition:all 0.18s;
            background:var(--bg2);
        }
        .quick-chip:hover { border-color:rgba(249,115,22,0.35); color:var(--orange2); background:var(--orange-dim); }

        /* Messages */
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

        /* Typing indicator */
        .typing { display:flex; align-items:center; gap:4px; padding:10px 14px; }
        .typing span { width:6px; height:6px; border-radius:50%; background:var(--text3); animation:typingDot 1.2s ease-in-out infinite; }
        .typing span:nth-child(2) { animation-delay:0.2s; }
        .typing span:nth-child(3) { animation-delay:0.4s; }
        @keyframes typingDot { 0%,60%,100%{transform:translateY(0)} 30%{transform:translateY(-5px)} }

        /* Progress */
        .progress-card {
            display:none; max-width:660px; margin:0 auto;
            padding:14px 16px; background:var(--bg3); border:1px solid var(--border);
            border-radius:var(--r); animation:msgIn 0.25s ease;
        }
        .progress-top { display:flex; justify-content:space-between; align-items:center; margin-bottom:10px; }
        .progress-label { font-size:0.78em; color:var(--text2); }
        .progress-timer { font-size:0.72em; color:var(--orange2); font-weight:500; }
        .pbar { height:3px; background:rgba(255,255,255,0.06); border-radius:2px; overflow:hidden; }
        .pbar-fill { height:100%; background:linear-gradient(90deg,var(--orange),#dc2626); animation:pbarAnim 2s ease-in-out infinite; border-radius:2px; }
        @keyframes pbarAnim { 0%{width:0%;margin-left:0} 50%{width:65%;margin-left:0} 100%{width:0%;margin-left:100%} }

        /* Generated image card */
        .img-result {
            max-width:660px; margin:0 auto; background:var(--bg3);
            border:1px solid var(--border); border-radius:var(--r);
            overflow:hidden; animation:msgIn 0.3s ease;
        }
        .img-result img { width:100%; max-height:520px; object-fit:cover; display:block; cursor:pointer; transition:opacity 0.2s; }
        .img-result img:hover { opacity:0.92; }
        .img-result-meta { padding:10px 13px; border-top:1px solid var(--border); }
        .img-prompt-used { font-size:0.72em; color:var(--text3); margin-bottom:8px; line-height:1.5; }
        .img-result-actions { display:flex; gap:6px; flex-wrap:wrap; }
        .act-btn {
            padding:5px 12px; border-radius:var(--r3); font-size:0.75em; font-weight:500;
            cursor:pointer; transition:all 0.18s; font-family:'Inter',sans-serif;
            border:1px solid var(--border2); background:transparent; color:var(--text2);
            display:flex; align-items:center; gap:5px;
        }
        .act-btn:hover { background:var(--bg4); color:var(--text); }
        .act-btn.orange { background:var(--orange-dim); border-color:rgba(249,115,22,0.2); color:var(--orange2); }
        .act-btn.orange:hover { background:var(--orange-dim2); }
        .act-btn a { color:inherit; text-decoration:none; }

        /* ── INPUT ── */
        .input-wrap { padding:12px 24px 16px; border-top:1px solid var(--border); }
        .input-inner { max-width:660px; margin:0 auto; }

        .input-box {
            display:flex; align-items:flex-end; gap:8px;
            background:var(--bg2); border:1px solid var(--border2);
            border-radius:var(--r); padding:10px 12px; transition:border-color 0.2s;
        }
        .input-box:focus-within { border-color:rgba(249,115,22,0.45); box-shadow:0 0 0 3px rgba(249,115,22,0.06); }

        textarea#userInput {
            flex:1; background:transparent; border:none; outline:none;
            color:var(--text); font-family:'Inter',sans-serif; font-size:0.9em;
            resize:none; line-height:1.55; padding:2px 0; max-height:130px;
        }
        textarea#userInput::placeholder { color:var(--text3); }

        .char-count { font-size:0.65em; color:var(--text3); align-self:flex-end; padding-bottom:3px; flex-shrink:0; }
        .char-count.warn { color:var(--orange2); }

        .send-btn {
            width:34px; height:34px; border-radius:var(--r2);
            background:var(--orange); border:none; color:white;
            font-size:1.05em; cursor:pointer; transition:all 0.2s;
            display:flex; align-items:center; justify-content:center; flex-shrink:0;
        }
        .send-btn:hover { background:var(--orange2); transform:scale(1.06); }
        .send-btn:active { transform:scale(0.96); }

        .input-meta { display:flex; gap:7px; margin-top:7px; align-items:center; flex-wrap:wrap; }

        .neg-box {
            flex:1; display:flex; align-items:center; gap:6px;
            background:var(--bg2); border:1px solid var(--border);
            border-radius:var(--r2); padding:5px 10px; min-width:0;
            transition:border-color 0.2s;
        }
        .neg-box:focus-within { border-color:rgba(239,68,68,0.3); }
        .neg-label { font-size:0.68em; color:rgba(239,68,68,0.5); white-space:nowrap; font-weight:600; }
        #negativeInput { background:transparent; border:none; outline:none; color:var(--text); font-family:'Inter',sans-serif; font-size:0.8em; flex:1; min-width:0; }
        #negativeInput::placeholder { color:var(--text3); }

        .meta-btn {
            padding:5px 11px; background:transparent; border:1px solid var(--border);
            border-radius:var(--r2); color:var(--text3); font-size:0.74em;
            cursor:pointer; transition:all 0.18s; white-space:nowrap;
            font-family:'Inter',sans-serif; flex-shrink:0;
        }
        .meta-btn:hover { border-color:rgba(249,115,22,0.35); color:var(--orange2); background:var(--orange-dim); }

        /* ── GALLERY & HISTORY PAGE ── */
        .page-hdr { padding:18px 24px 14px; border-bottom:1px solid var(--border); display:flex; justify-content:space-between; align-items:center; flex-shrink:0; }
        .page-hdr-left h2 { font-size:1em; font-weight:600; }
        .page-hdr-left p { font-size:0.76em; color:var(--text3); margin-top:2px; }
        .page-hdr-btn { padding:7px 14px; background:var(--orange-dim); border:1px solid rgba(249,115,22,0.18); border-radius:var(--r2); color:var(--orange2); font-size:0.76em; font-weight:500; cursor:pointer; transition:all 0.18s; font-family:'Inter',sans-serif; }
        .page-hdr-btn:hover { background:var(--orange-dim2); }

        .gallery-body { flex:1; overflow-y:auto; padding:18px 24px; }
        .gallery-body::-webkit-scrollbar { width:4px; }
        .gallery-body::-webkit-scrollbar-thumb { background:rgba(255,255,255,0.08); border-radius:2px; }

        /* Search */
        .search-wrap { position:relative; margin-bottom:16px; }
        .search-icon { position:absolute; left:10px; top:50%; transform:translateY(-50%); color:var(--text3); font-size:0.85em; pointer-events:none; }
        #gallerySearch { width:100%; padding:8px 12px 8px 30px; background:var(--bg3); border:1px solid var(--border); border-radius:var(--r2); color:var(--text); font-family:'Inter',sans-serif; font-size:0.84em; outline:none; transition:border-color 0.2s; }
        #gallerySearch:focus { border-color:rgba(249,115,22,0.35); }
        #gallerySearch::placeholder { color:var(--text3); }

        .folders-row { display:flex; flex-wrap:wrap; gap:7px; margin-bottom:16px; }
        .folder-pill { display:flex; align-items:center; gap:5px; padding:5px 13px; border-radius:20px; border:1px solid var(--border); cursor:pointer; font-size:0.78em; color:var(--text2); transition:all 0.18s; user-select:none; }
        .folder-pill:hover { border-color:rgba(249,115,22,0.3); color:var(--text); }
        .folder-pill.active { background:var(--orange-dim); border-color:rgba(249,115,22,0.25); color:var(--orange2); font-weight:500; }
        .folder-badge { background:rgba(255,255,255,0.07); border-radius:10px; padding:1px 6px; font-size:0.82em; }

        .images-grid { display:grid; grid-template-columns:repeat(auto-fill,minmax(165px,1fr)); gap:10px; }
        .img-card { border-radius:var(--r); overflow:hidden; border:1px solid var(--border); background:var(--bg2); transition:all 0.2s; cursor:pointer; }
        .img-card:hover { border-color:rgba(249,115,22,0.25); transform:translateY(-2px); box-shadow:0 8px 24px rgba(0,0,0,0.3); }
        .img-card img { width:100%; height:145px; object-fit:cover; display:block; }
        .img-card-body { padding:8px; }
        .img-card-prompt { font-size:0.7em; color:var(--text3); white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
        .img-card-btns { display:flex; gap:4px; margin-top:6px; }
        .img-card-btn { flex:1; padding:4px; text-align:center; border-radius:4px; border:1px solid var(--border); font-size:0.66em; color:var(--text3); cursor:pointer; transition:all 0.18s; background:transparent; font-family:'Inter',sans-serif; text-decoration:none; display:flex; align-items:center; justify-content:center; }
        .img-card-btn:hover { background:var(--bg3); color:var(--text); }

        /* History */
        .hist-body { flex:1; overflow-y:auto; padding:16px 24px; }
        .hist-item { display:flex; align-items:center; gap:10px; padding:10px 13px; border-radius:var(--r); border:1px solid var(--border); background:var(--bg2); margin-bottom:6px; transition:all 0.18s; }
        .hist-item:hover { border-color:var(--border2); }
        .hist-icon { color:var(--text3); flex-shrink:0; }
        .hist-text { flex:1; font-size:0.85em; color:var(--text2); overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
        .hist-btn { padding:4px 10px; border-radius:var(--r3); border:1px solid var(--border); background:transparent; color:var(--text3); font-size:0.7em; cursor:pointer; transition:all 0.18s; font-family:'Inter',sans-serif; flex-shrink:0; }
        .hist-btn:hover { background:var(--orange-dim); border-color:rgba(249,115,22,0.25); color:var(--orange2); }

        /* ── MODALS ── */
        .overlay { display:none; position:fixed; inset:0; background:rgba(0,0,0,0.6); z-index:1000; justify-content:center; align-items:center; backdrop-filter:blur(6px); }
        .overlay.open { display:flex; }

        .modal { background:var(--bg2); border:1px solid var(--border2); border-radius:14px; padding:24px; width:350px; max-width:92vw; animation:modalIn 0.2s ease; box-shadow:var(--shadow); }
        @keyframes modalIn { from{opacity:0;transform:scale(0.95)translateY(8px)} to{opacity:1;transform:scale(1)translateY(0)} }

        .modal-hdr { display:flex; justify-content:space-between; align-items:center; margin-bottom:18px; }
        .modal-hdr h3 { font-size:0.96em; font-weight:600; }
        .modal-x { background:none; border:none; color:var(--text3); cursor:pointer; font-size:1.1em; padding:2px 5px; border-radius:4px; transition:all 0.15s; }
        .modal-x:hover { background:var(--bg4); color:var(--text); }

        .f-label { font-size:0.74em; color:var(--text2); margin-bottom:5px; font-weight:500; }
        .f-input { width:100%; padding:9px 12px; background:var(--bg3); border:1px solid var(--border); border-radius:var(--r2); color:var(--text); font-family:'Inter',sans-serif; font-size:0.86em; outline:none; margin-bottom:12px; transition:border-color 0.2s; }
        .f-input:focus { border-color:rgba(249,115,22,0.4); }

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

        /* Lightbox */
        .lightbox { display:none; position:fixed; inset:0; background:rgba(0,0,0,0.9); z-index:2000; justify-content:center; align-items:center; cursor:zoom-out; }
        .lightbox.open { display:flex; }
        .lightbox img { max-width:90vw; max-height:90vh; border-radius:var(--r); box-shadow:var(--shadow); }

        /* Empty state */
        .empty { text-align:center; padding:50px 20px; color:var(--text3); }
        .empty-i { font-size:2.4em; margin-bottom:12px; }
        .empty p { font-size:0.84em; line-height:1.7; }

        /* Toast */
        .toast { position:fixed; bottom:24px; right:24px; background:var(--bg3); border:1px solid var(--border2); border-radius:var(--r); padding:10px 16px; font-size:0.82em; color:var(--text); box-shadow:var(--shadow); z-index:3000; transform:translateY(80px); opacity:0; transition:all 0.3s ease; pointer-events:none; }
        .toast.show { transform:translateY(0); opacity:1; }
        .toast.success { border-left:3px solid #4ade80; }
        .toast.error { border-left:3px solid #f87171; }
        .toast.info { border-left:3px solid var(--orange); }
    </style>
</head>
<body>

<!-- Particles -->
<div id="particles"></div>

<!-- Toast -->
<div class="toast" id="toast"></div>

<!-- Layout -->
<div class="layout">

    <!-- SIDEBAR -->
    <aside class="sidebar">
        <div class="logo-wrap">
            <div class="logo">
                <div class="logo-icon">✦</div>
                <div>
                    <div class="logo-name">Astax</div>
                    <div class="logo-tag">Generative Image AI</div>
                </div>
            </div>
        </div>

        <div class="sidebar-nav">
            <div class="section-label">Navigation</div>
            <div class="nav-item active" id="nav-chat" onclick="showPage('chat')">
                <span>✦</span> Créer
            </div>
            <div class="nav-item" id="nav-gallery" onclick="showPage('gallery')">
                <span>⊞</span> Galerie
                <span class="badge" id="galleryBadge">0</span>
            </div>
            <div class="nav-item" id="nav-history" onclick="showPage('history')">
                <span>↺</span> Historique
                <span class="badge" id="historyBadge">0</span>
            </div>
            <div class="nav-divider"></div>
            <div class="section-label">Style rapide</div>
        </div>

        <div class="styles-wrap">
            <div class="style-chip selected" id="style-auto" onclick="selectStyle(this,'')">
                <span class="chip-dot"></span> Auto
            </div>
            <div class="style-chip" onclick="selectStyle(this,'photorealistic, ultra detailed, 8k photography, sharp focus')">
                <span class="chip-dot"></span> 📷 Réaliste
            </div>
            <div class="style-chip" onclick="selectStyle(this,'anime style, manga illustration, vibrant colors, studio ghibli')">
                <span class="chip-dot"></span> 🎌 Anime
            </div>
            <div class="style-chip" onclick="selectStyle(this,'oil painting, impasto, artistic brushstrokes, museum quality')">
                <span class="chip-dot"></span> 🎨 Peinture
            </div>
            <div class="style-chip" onclick="selectStyle(this,'pixel art, 16-bit, retro game style, crisp pixels')">
                <span class="chip-dot"></span> 👾 Pixel Art
            </div>
            <div class="style-chip" onclick="selectStyle(this,'cyberpunk, neon lights, rain reflections, futuristic dark city')">
                <span class="chip-dot"></span> 🌆 Cyberpunk
            </div>
            <div class="style-chip" onclick="selectStyle(this,'watercolor painting, soft colors, dreamy, artistic illustration')">
                <span class="chip-dot"></span> 💧 Aquarelle
            </div>
            <div class="style-chip" onclick="selectStyle(this,'dark fantasy, dramatic lighting, epic cinematic scene, moody')">
                <span class="chip-dot"></span> ⚔️ Dark Fantasy
            </div>
            <div class="style-chip" onclick="selectStyle(this,'minimalist design, clean geometric shapes, modern, flat design')">
                <span class="chip-dot"></span> ◻ Minimaliste
            </div>
            <div class="style-chip" onclick="selectStyle(this,'3d render, octane render, volumetric lighting, highly detailed')">
                <span class="chip-dot"></span> 🔮 3D Render
            </div>
            <div class="style-chip" onclick="selectStyle(this,'vintage photograph, film grain, 1970s color grading, nostalgic')">
                <span class="chip-dot"></span> 📸 Vintage
            </div>
            <div class="style-chip" onclick="selectStyle(this,'comic book style, bold outlines, halftone dots, superhero')">
                <span class="chip-dot"></span> 💥 Comics
            </div>
        </div>

        <div class="user-wrap">
            <div class="user-card" id="userCard" onclick="userCardClick()">
                <div class="user-avatar guest" id="userAv">?</div>
                <div>
                    <div class="u-name" id="uName">Mode invité</div>
                    <div class="u-status" id="uStatus">Cliquer pour se connecter</div>
                </div>
            </div>
        </div>
    </aside>

    <!-- MAIN -->
    <main class="main">

        <!-- CHAT -->
        <div class="page active" id="page-chat">
            <div class="chat-scroll" id="chatScroll">
                <div class="welcome" id="welcomeMsg">
                    <div class="welcome-orb">✦</div>
                    <h2>Qu'est-ce qu'on crée aujourd'hui ?</h2>
                    <p>Décris ton idée, je vais te poser quelques questions pour affiner ta vision et générer l'image parfaite.</p>
                    <div class="quick-prompts">
                        <div class="quick-chip" onclick="useQuickPrompt('Un paysage de montagne au coucher de soleil')">🏔️ Montagne</div>
                        <div class="quick-chip" onclick="useQuickPrompt('Un personnage de science-fiction futuriste')">🚀 Sci-Fi</div>
                        <div class="quick-chip" onclick="useQuickPrompt('Un animal fantastique dans une forêt enchantée')">🐉 Fantasy</div>
                        <div class="quick-chip" onclick="useQuickPrompt('Une ville futuriste vue du ciel la nuit')">🌃 Ville</div>
                        <div class="quick-chip" onclick="useQuickPrompt('Un portrait artistique expressif')">🎭 Portrait</div>
                        <div class="quick-chip" onclick="useQuickPrompt('Une scène sous-marine mystérieuse')">🌊 Océan</div>
                    </div>
                </div>
                <div class="messages" id="messages"></div>
                <div class="progress-card" id="progressCard">
                    <div class="progress-top">
                        <span class="progress-label" id="progressLabel">Génération en cours...</span>
                        <span class="progress-timer" id="progressTimer">0s</span>
                    </div>
                    <div class="pbar"><div class="pbar-fill"></div></div>
                </div>
            </div>

            <div class="input-wrap">
                <div class="input-inner">
                    <div class="input-box">
                        <textarea id="userInput" rows="1" placeholder="Décris ce que tu veux créer..."></textarea>
                        <span class="char-count" id="charCount">0</span>
                        <button class="send-btn" id="sendBtn">↑</button>
                    </div>
                    <div class="input-meta">
                        <div class="neg-box">
                            <span class="neg-label">✕</span>
                            <input type="text" id="negativeInput" placeholder="Exclure : flou, texte, déformé...">
                        </div>
                        <button class="meta-btn" id="inspireBtn">✦ Inspire</button>
                        <button class="meta-btn" id="newChatBtn">↺ Nouveau</button>
                    </div>
                </div>
            </div>
        </div>

        <!-- GALLERY -->
        <div class="page" id="page-gallery">
            <div class="page-hdr">
                <div class="page-hdr-left">
                    <h2>Galerie</h2>
                    <p>Tes créations organisées par projet</p>
                </div>
                <button class="page-hdr-btn" id="newFolderBtn">+ Nouveau dossier</button>
            </div>
            <div class="gallery-body">
                <div class="search-wrap">
                    <span class="search-icon">🔍</span>
                    <input type="text" id="gallerySearch" placeholder="Rechercher par prompt...">
                </div>
                <div class="folders-row" id="foldersList"></div>
                <div class="images-grid" id="imagesGrid"></div>
            </div>
        </div>

        <!-- HISTORY -->
        <div class="page" id="page-history">
            <div class="page-hdr">
                <div class="page-hdr-left">
                    <h2>Historique</h2>
                    <p>Tes <span id="histCount">0</span> derniers prompts</p>
                </div>
                <button class="page-hdr-btn" id="clearHistBtn">Effacer tout</button>
            </div>
            <div class="hist-body" id="historyList"></div>
        </div>

    </main>
</div>

<!-- Lightbox -->
<div class="lightbox" id="lightbox" onclick="closeLightbox()">
    <img id="lightboxImg" src="" alt="">
</div>

<!-- Auth Modal -->
<div class="overlay" id="authOverlay">
    <div class="modal">
        <div class="modal-hdr">
            <h3 id="authTitle">Connexion</h3>
            <button class="modal-x" id="authX">✕</button>
        </div>
        <div class="err-box" id="authErr"></div>
        <div class="f-label">Nom d'utilisateur</div>
        <input type="text" class="f-input" id="authUser" placeholder="johndoe" autocomplete="username">
        <div class="f-label">Mot de passe</div>
        <input type="password" class="f-input" id="authPass" placeholder="••••••••" autocomplete="current-password">
        <div class="modal-foot">
            <button class="btn btn-ghost" id="authCancel">Annuler</button>
            <button class="btn btn-orange" id="authAction">Se connecter</button>
        </div>
        <div class="auth-foot">
            <span id="authSwTxt">Pas de compte ?</span>
            <span class="auth-link" id="authSwLink">S'inscrire</span>
        </div>
    </div>
</div>

<!-- Folder Modal -->
<div class="overlay" id="folderOverlay">
    <div class="modal">
        <div class="modal-hdr">
            <h3>Nouveau dossier</h3>
            <button class="modal-x" id="folderX">✕</button>
        </div>
        <div class="f-label">Nom du projet</div>
        <input type="text" class="f-input" id="folderName" placeholder="ex: Mes paysages fantasy">
        <div class="modal-foot">
            <button class="btn btn-ghost" id="folderCancel">Annuler</button>
            <button class="btn btn-orange" id="folderConfirm">Créer</button>
        </div>
    </div>
</div>

<!-- Save Modal -->
<div class="overlay" id="saveOverlay">
    <div class="modal">
        <div class="modal-hdr">
            <h3>Sauvegarder dans...</h3>
            <button class="modal-x" id="saveX">✕</button>
        </div>
        <div class="save-folders" id="saveFolders"></div>
        <div class="modal-foot">
            <button class="btn btn-ghost" id="saveCancel">Annuler</button>
        </div>
    </div>
</div>

<script>
// ── STATE ──
var conv = [], currentFolder = null, selectedStyle = '', authMode = 'login';
var currentUser = null, promptHistory = [], pendingUrl = null, pendingPrompt = null;
var genTimer = null, genStart = 0, totalImages = 0;

var inspirePool = [
    'Un astronaute solitaire explorant une planète alien au coucher de soleil',
    'Une bibliothèque ancienne et magique flottant dans les nuages',
    'Un dragon de cristal endormi au cœur d\'une forêt lumineuse',
    'Une ville sous-marine futuriste peuplée de créatures bioluminescentes',
    'Un titan mécanique gardant les ruines d\'une cité ancienne',
    'Une forêt de champignons géants sous une lune violette',
    'Un robot peintre créant une fresque dans un désert de sel',
    'Une île volante avec des cascades qui tombent dans les nuages',
    'Un samurai fantôme marchant dans une forêt de cerisiers enneigés',
    'Un marché de magie nocturne dans une ruelle médiévale',
    'Un phare solitaire sur une falaise pendant une tempête cosmique',
    'Une créature mi-renard mi-dragon gardant un temple zen',
    'Un café confortable dans une station spatiale avec vue sur la Terre',
    'Un tunnel de tunnels de couleurs néon dans un monde de données'
];

var quickIdeas = ['Un paysage de montagne au coucher de soleil','Un personnage de science-fiction futuriste','Un animal fantastique dans une forêt enchantée','Une ville futuriste vue du ciel la nuit','Un portrait artistique expressif','Une scène sous-marine mystérieuse'];

// ── PARTICLES ──
function createParticles() {
    var container = document.getElementById('particles');
    for (var i = 0; i < 18; i++) {
        var p = document.createElement('div');
        p.className = 'particle';
        p.style.left = Math.random() * 100 + '%';
        p.style.animationDuration = (12 + Math.random() * 20) + 's';
        p.style.animationDelay = (Math.random() * 15) + 's';
        p.style.opacity = Math.random() * 0.4;
        container.appendChild(p);
    }
}

// ── TOAST ──
function showToast(msg, type) {
    var t = document.getElementById('toast');
    t.innerText = msg;
    t.className = 'toast ' + (type || 'info');
    t.classList.add('show');
    setTimeout(function() { t.classList.remove('show'); }, 3000);
}

// ── INIT ──
window.addEventListener('load', function() {
    createParticles();
    try { promptHistory = JSON.parse(localStorage.getItem('astax_history') || '[]'); } catch(e) { promptHistory = []; }
    updateBadges();

    // Nav
    ['chat','gallery','history'].forEach(function(p) {
        document.getElementById('nav-' + p).addEventListener('click', function() { showPage(p); });
    });

    // Chat
    document.getElementById('sendBtn').addEventListener('click', envoyer);
    document.getElementById('userInput').addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); envoyer(); }
    });
    document.getElementById('userInput').addEventListener('input', function() {
        autoResize(this);
        var n = this.value.length;
        var cc = document.getElementById('charCount');
        cc.innerText = n;
        cc.className = 'char-count' + (n > 400 ? ' warn' : '');
    });
    document.getElementById('inspireBtn').addEventListener('click', inspire);
    document.getElementById('newChatBtn').addEventListener('click', newChat);

    // Gallery
    document.getElementById('newFolderBtn').addEventListener('click', openCreateFolder);
    document.getElementById('gallerySearch').addEventListener('input', filterGallery);

    // History
    document.getElementById('clearHistBtn').addEventListener('click', clearHistory);

    // Modals
    document.getElementById('authX').addEventListener('click', function() { closeOverlay('authOverlay'); });
    document.getElementById('authCancel').addEventListener('click', function() { closeOverlay('authOverlay'); });
    document.getElementById('authAction').addEventListener('click', doAuth);
    document.getElementById('authSwLink').addEventListener('click', toggleAuthMode);
    document.getElementById('authPass').addEventListener('keydown', function(e) { if (e.key === 'Enter') doAuth(); });

    document.getElementById('folderX').addEventListener('click', function() { closeOverlay('folderOverlay'); });
    document.getElementById('folderCancel').addEventListener('click', function() { closeOverlay('folderOverlay'); });
    document.getElementById('folderConfirm').addEventListener('click', createFolder);
    document.getElementById('folderName').addEventListener('keydown', function(e) { if (e.key === 'Enter') createFolder(); });

    document.getElementById('saveX').addEventListener('click', function() { closeOverlay('saveOverlay'); });
    document.getElementById('saveCancel').addEventListener('click', function() { closeOverlay('saveOverlay'); });

    document.getElementById('userCard').addEventListener('click', userCardClick);

    // Check session
    fetch('/me').then(function(r) { return r.json(); }).then(function(d) {
        if (d.username) { setLoggedIn(d.username); if (d.prompt_history && d.prompt_history.length) promptHistory = d.prompt_history; updateBadges(); }
    });
});

// ── UTILS ──
function autoResize(el) { el.style.height = 'auto'; el.style.height = Math.min(el.scrollHeight, 130) + 'px'; }
function scrollDown() { var s = document.getElementById('chatScroll'); s.scrollTop = s.scrollHeight; }
function updateBadges() {
    var hb = document.getElementById('historyBadge');
    if (promptHistory.length > 0) { hb.innerText = promptHistory.length; hb.classList.add('show'); } else { hb.classList.remove('show'); }
}

function showPage(p) {
    document.querySelectorAll('.page').forEach(function(el) { el.classList.remove('active'); });
    document.querySelectorAll('.nav-item').forEach(function(el) { el.classList.remove('active'); });
    document.getElementById('page-' + p).classList.add('active');
    document.getElementById('nav-' + p).classList.add('active');
    if (p === 'gallery') loadGallery();
    if (p === 'history') loadHistory();
}

function selectStyle(el, style) {
    document.querySelectorAll('.style-chip').forEach(function(c) { c.classList.remove('selected'); });
    el.classList.add('selected');
    selectedStyle = style;
}

function inspire() {
    var idea = inspirePool[Math.floor(Math.random() * inspirePool.length)];
    var inp = document.getElementById('userInput');
    inp.value = idea;
    autoResize(inp);
    inp.focus();
}

function useQuickPrompt(text) {
    document.getElementById('userInput').value = text;
    autoResize(document.getElementById('userInput'));
    document.getElementById('userInput').focus();
}

function newChat() {
    conv = [];
    document.getElementById('messages').innerHTML = '';
    document.getElementById('welcomeMsg').style.display = '';
    document.getElementById('progressCard').style.display = 'none';
    showToast('Nouvelle conversation démarrée', 'info');
}

// ── MESSAGES ──
function hideWelcome() { document.getElementById('welcomeMsg').style.display = 'none'; }

function addMsg(role, text) {
    hideWelcome();
    var msgs = document.getElementById('messages');
    var row = document.createElement('div');
    row.className = 'msg-row ' + role;
    var av = document.createElement('div');
    av.className = 'msg-av ' + role;
    av.innerText = role === 'bot' ? '✦' : '✎';
    var bbl = document.createElement('div');
    bbl.className = 'msg-bbl ' + role;
    bbl.innerText = text;
    row.appendChild(av);
    row.appendChild(bbl);
    msgs.appendChild(row);
    scrollDown();
}

function showTyping() {
    hideWelcome();
    var msgs = document.getElementById('messages');
    var row = document.createElement('div');
    row.className = 'msg-row bot';
    row.id = 'typingRow';
    var av = document.createElement('div');
    av.className = 'msg-av bot';
    av.innerText = '✦';
    var bbl = document.createElement('div');
    bbl.className = 'msg-bbl bot typing';
    bbl.innerHTML = '<span></span><span></span><span></span>';
    row.appendChild(av);
    row.appendChild(bbl);
    msgs.appendChild(row);
    scrollDown();
}

function removeTyping() {
    var t = document.getElementById('typingRow');
    if (t) t.remove();
}

function addImageResult(imgUrl, prompt, count, idx) {
    var msgs = document.getElementById('messages');
    var card = document.createElement('div');
    card.className = 'img-result';

    var img = document.createElement('img');
    img.src = imgUrl;
    img.title = 'Cliquer pour agrandir';
    img.addEventListener('click', function() { openLightbox(imgUrl); });

    var meta = document.createElement('div');
    meta.className = 'img-result-meta';
    var pused = document.createElement('div');
    pused.className = 'img-prompt-used';
    pused.innerText = '🖼 ' + (count > 1 ? 'Image ' + (idx+1) + '/' + count + ' — ' : '') + prompt.substring(0, 100) + (prompt.length > 100 ? '...' : '');

    var actions = document.createElement('div');
    actions.className = 'img-result-actions';

    var dlA = document.createElement('a');
    dlA.href = imgUrl;
    dlA.download = 'astax-' + Date.now() + '.png';
    dlA.className = 'act-btn';
    dlA.innerText = '⬇ Télécharger';

    var saveBtn = document.createElement('button');
    saveBtn.className = 'act-btn orange';
    saveBtn.innerText = '💾 Sauvegarder';
    var cu = imgUrl, cp = prompt;
    saveBtn.addEventListener('click', function() {
        if (!currentUser) { showToast('Connecte-toi pour sauvegarder !', 'error'); return; }
        pendingUrl = cu; pendingPrompt = cp; openSaveModal();
    });

    var copyBtn = document.createElement('button');
    copyBtn.className = 'act-btn';
    copyBtn.innerText = '📋 Copier le prompt';
    copyBtn.addEventListener('click', function() {
        navigator.clipboard.writeText(prompt).then(function() { showToast('Prompt copié !', 'success'); });
    });

    var regenBtn = document.createElement('button');
    regenBtn.className = 'act-btn';
    regenBtn.innerText = '🔄 Régénérer';
    var rp = prompt, rs = selectedStyle, rn = document.getElementById('negativeInput').value;
    regenBtn.addEventListener('click', function() { regenerate(rp, rs, rn); });

    actions.appendChild(dlA);
    actions.appendChild(saveBtn);
    actions.appendChild(copyBtn);
    actions.appendChild(regenBtn);
    meta.appendChild(pused);
    meta.appendChild(actions);
    card.appendChild(img);
    card.appendChild(meta);
    msgs.appendChild(card);
    scrollDown();
}

// ── CHAT ──
function envoyer() {
    var inp = document.getElementById('userInput');
    var text = inp.value.trim();
    if (!text) return;
    addMsg('user', text);
    conv.push({role:'user', content:text});
    inp.value = ''; inp.style.height = 'auto';
    document.getElementById('charCount').innerText = '0';
    showTyping();

    fetch('/chat', {
        method:'POST', headers:{'Content-Type':'application/json'},
        body: JSON.stringify({messages:conv, style:selectedStyle})
    }).then(function(r) { return r.json(); }).then(function(d) {
        removeTyping();
        if (d.type === 'question') {
            addMsg('bot', d.message);
            conv.push({role:'assistant', content:d.message});
        } else if (d.type === 'generate') {
            addMsg('bot', d.message);
            conv.push({role:'assistant', content:d.message});
            addToHistory(d.prompt);
            var count = d.count || 1;
            var neg = document.getElementById('negativeInput').value.trim();
            startGeneration(d.prompt, neg, count, 0);
        }
    }).catch(function() { removeTyping(); showToast('Erreur de connexion', 'error'); });
}

function startGeneration(prompt, neg, count, idx) {
    var pc = document.getElementById('progressCard');
    var pl = document.getElementById('progressLabel');
    var pt = document.getElementById('progressTimer');

    pc.style.display = 'block';
    pl.innerText = count > 1 ? 'Génération ' + (idx+1) + ' sur ' + count + '...' : 'Génération en cours...';
    genStart = Date.now();
    if (genTimer) clearInterval(genTimer);
    genTimer = setInterval(function() {
        pt.innerText = ((Date.now() - genStart) / 1000).toFixed(1) + 's';
    }, 100);

    fetch('/generate', {
        method:'POST', headers:{'Content-Type':'application/json'},
        body: JSON.stringify({prompt:prompt, negative_prompt:neg, style:selectedStyle})
    }).then(function(r) {
        if (!r.ok) throw new Error('gen failed');
        return r.blob();
    }).then(function(blob) {
        clearInterval(genTimer);
        var elapsed = ((Date.now() - genStart) / 1000).toFixed(1);
        pt.innerText = elapsed + 's ✓';
        addImageResult(URL.createObjectURL(blob), prompt, count, idx);
        totalImages++;
        if (idx + 1 < count) {
            setTimeout(function() { startGeneration(prompt, neg, count, idx + 1); }, 300);
        } else {
            pc.style.display = 'none';
            conv = [];
            showToast('✦ ' + count + ' image' + (count > 1 ? 's' : '') + ' générée' + (count > 1 ? 's' : '') + ' en ' + elapsed + 's !', 'success');
        }
    }).catch(function() {
        clearInterval(genTimer);
        pc.style.display = 'none';
        showToast('Erreur lors de la génération', 'error');
    });
}

function regenerate(prompt, style, neg) {
    addMsg('bot', '🔄 Je régénère cette image...');
    startGeneration(prompt, neg, 1, 0);
}

// ── HISTORY ──
function addToHistory(prompt) {
    promptHistory = [prompt].concat(promptHistory.filter(function(p) { return p !== prompt; })).slice(0, 25);
    try { localStorage.setItem('astax_history', JSON.stringify(promptHistory)); } catch(e) {}
    if (currentUser) fetch('/save-history', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({history:promptHistory})});
    updateBadges();
    var hc = document.getElementById('histCount');
    if (hc) hc.innerText = promptHistory.length;
}

function loadHistory() {
    var list = document.getElementById('historyList');
    list.innerHTML = '';
    document.getElementById('histCount').innerText = promptHistory.length;
    if (!promptHistory.length) {
        list.innerHTML = '<div class="empty"><div class="empty-i">↺</div><p>Aucun prompt encore.<br>Génère ta première image !</p></div>';
        return;
    }
    promptHistory.forEach(function(p) {
        var item = document.createElement('div');
        item.className = 'hist-item';
        var icon = document.createElement('span');
        icon.className = 'hist-icon';
        icon.innerText = '✦';
        var txt = document.createElement('span');
        txt.className = 'hist-text';
        txt.innerText = p;
        var btn = document.createElement('button');
        btn.className = 'hist-btn';
        btn.innerText = 'Réutiliser';
        var cap = p;
        btn.addEventListener('click', function() { reusePrompt(cap); });
        item.appendChild(icon);
        item.appendChild(txt);
        item.appendChild(btn);
        list.appendChild(item);
    });
}

function clearHistory() {
    promptHistory = [];
    try { localStorage.removeItem('astax_history'); } catch(e) {}
    if (currentUser) fetch('/save-history', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({history:[]})});
    updateBadges();
    loadHistory();
    showToast('Historique effacé', 'info');
}

function reusePrompt(p) {
    var inp = document.getElementById('userInput');
    inp.value = p;
    autoResize(inp);
    showPage('chat');
    inp.focus();
}

// ── GALLERY ──
var allGalleryData = {};
function loadGallery() {
    if (!currentUser) {
        document.getElementById('foldersList').innerHTML = '<div class="empty" style="width:100%"><div class="empty-i">🔒</div><p>Connecte-toi<br>pour accéder à ta galerie</p></div>';
        document.getElementById('imagesGrid').innerHTML = '';
        return;
    }
    fetch('/galleries').then(function(r) { return r.json(); }).then(function(data) {
        allGalleryData = data;
        renderGallery(data);
    });
}

function renderGallery(data) {
    var fList = document.getElementById('foldersList');
    var iGrid = document.getElementById('imagesGrid');
    fList.innerHTML = '';
    iGrid.innerHTML = '';
    var keys = Object.keys(data);
    if (!keys.length) {
        fList.innerHTML = '<div class="empty" style="width:100%"><div class="empty-i">⊞</div><p>Aucun dossier encore.<br>Crée ton premier projet !</p></div>';
        return;
    }
    keys.forEach(function(name) {
        var pill = document.createElement('div');
        pill.className = 'folder-pill' + (currentFolder === name ? ' active' : '');
        pill.innerHTML = '📁 ' + name + ' <span class="folder-badge">' + data[name].length + '</span>';
        var cap = name;
        pill.addEventListener('click', function() { currentFolder = cap; loadGallery(); });
        fList.appendChild(pill);
    });
    var images = currentFolder && data[currentFolder] ? data[currentFolder] : [];
    var search = document.getElementById('gallerySearch').value.toLowerCase();
    if (search) images = images.filter(function(img) { return img.prompt.toLowerCase().includes(search); });
    if (!images.length && currentFolder) {
        iGrid.innerHTML = '<div class="empty"><div class="empty-i">🖼️</div><p>Aucune image dans ce dossier</p></div>';
        return;
    }
    images.forEach(function(img) {
        var card = document.createElement('div');
        card.className = 'img-card';
        var imgEl = document.createElement('img');
        imgEl.src = img.image_b64;
        imgEl.addEventListener('click', function() { openLightbox(img.image_b64); });
        var body = document.createElement('div');
        body.className = 'img-card-body';
        var pEl = document.createElement('div');
        pEl.className = 'img-card-prompt';
        pEl.innerText = img.prompt;
        pEl.title = img.prompt;
        var btns = document.createElement('div');
        btns.className = 'img-card-btns';
        var dlA = document.createElement('a');
        dlA.href = img.image_b64;
        dlA.download = 'astax.png';
        dlA.className = 'img-card-btn';
        dlA.innerText = '⬇';
        dlA.title = 'Télécharger';
        var delB = document.createElement('button');
        delB.className = 'img-card-btn';
        delB.innerText = '✕';
        delB.title = 'Supprimer';
        var cf = currentFolder, ci = img.id;
        delB.addEventListener('click', function(e) { e.stopPropagation(); deleteImage(cf, ci); });
        btns.appendChild(dlA);
        btns.appendChild(delB);
        body.appendChild(pEl);
        body.appendChild(btns);
        card.appendChild(imgEl);
        card.appendChild(body);
        iGrid.appendChild(card);
    });
}

function filterGallery() { renderGallery(allGalleryData); }

function openCreateFolder() {
    if (!currentUser) { showToast('Connecte-toi d\'abord !', 'error'); return; }
    document.getElementById('folderName').value = '';
    openOverlay('folderOverlay');
    setTimeout(function() { document.getElementById('folderName').focus(); }, 100);
}

function createFolder() {
    var name = document.getElementById('folderName').value.trim();
    if (!name) return;
    fetch('/create-folder', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({name:name})})
    .then(function() { closeOverlay('folderOverlay'); loadGallery(); showToast('Dossier "' + name + '" créé !', 'success'); });
}

function openSaveModal() {
    fetch('/galleries').then(function(r) { return r.json(); }).then(function(data) {
        var list = document.getElementById('saveFolders');
        list.innerHTML = '';
        var keys = Object.keys(data);
        if (!keys.length) {
            list.innerHTML = '<span style="font-size:0.82em;color:var(--text3)">Aucun dossier — crée-en un dans la galerie !</span>';
        } else {
            keys.forEach(function(name) {
                var btn = document.createElement('button');
                btn.className = 'sfbtn';
                btn.innerText = '📁 ' + name;
                var cap = name;
                btn.addEventListener('click', function() { saveToFolder(cap); });
                list.appendChild(btn);
            });
        }
        openOverlay('saveOverlay');
    });
}

function saveToFolder(folder) {
    fetch(pendingUrl).then(function(r) { return r.blob(); }).then(function(blob) {
        var reader = new FileReader();
        reader.onloadend = function() {
            fetch('/save-image', {
                method:'POST', headers:{'Content-Type':'application/json'},
                body:JSON.stringify({folder:folder, image_b64:reader.result, prompt:pendingPrompt})
            }).then(function() {
                closeOverlay('saveOverlay');
                showToast('✦ Image sauvegardée dans "' + folder + '" !', 'success');
                updateBadges();
            });
        };
        reader.readAsDataURL(blob);
    });
}

function deleteImage(folder, id) {
    fetch('/delete-image', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({folder:folder, id:id})})
    .then(function() { loadGallery(); showToast('Image supprimée', 'info'); });
}

// ── LIGHTBOX ──
function openLightbox(src) {
    document.getElementById('lightboxImg').src = src;
    document.getElementById('lightbox').classList.add('open');
}
function closeLightbox() { document.getElementById('lightbox').classList.remove('open'); }

// ── OVERLAYS ──
function openOverlay(id) { document.getElementById(id).classList.add('open'); }
function closeOverlay(id) { document.getElementById(id).classList.remove('open'); }

// ── AUTH ──
function userCardClick() { if (currentUser) logout(); else openAuthModal(); }

function openAuthModal() {
    authMode = 'login';
    document.getElementById('authTitle').innerText = 'Connexion';
    document.getElementById('authAction').innerText = 'Se connecter';
    document.getElementById('authSwTxt').innerText = 'Pas de compte ?';
    document.getElementById('authSwLink').innerText = "S'inscrire";
    document.getElementById('authErr').style.display = 'none';
    document.getElementById('authUser').value = '';
    document.getElementById('authPass').value = '';
    openOverlay('authOverlay');
    setTimeout(function() { document.getElementById('authUser').focus(); }, 100);
}

function toggleAuthMode() {
    authMode = authMode === 'login' ? 'register' : 'login';
    var isLogin = authMode === 'login';
    document.getElementById('authTitle').innerText = isLogin ? 'Connexion' : 'Inscription';
    document.getElementById('authAction').innerText = isLogin ? 'Se connecter' : "S'inscrire";
    document.getElementById('authSwTxt').innerText = isLogin ? 'Pas de compte ?' : 'Déjà un compte ?';
    document.getElementById('authSwLink').innerText = isLogin ? "S'inscrire" : 'Se connecter';
    document.getElementById('authErr').style.display = 'none';
}

function doAuth() {
    var user = document.getElementById('authUser').value.trim();
    var pass = document.getElementById('authPass').value;
    if (!user || !pass) return;
    fetch(authMode === 'login' ? '/login' : '/register', {
        method:'POST', headers:{'Content-Type':'application/json'},
        body:JSON.stringify({username:user, password:pass})
    }).then(function(r) { return r.json(); }).then(function(d) {
        if (d.success) {
            setLoggedIn(user);
            if (d.prompt_history) { promptHistory = d.prompt_history; updateBadges(); }
            closeOverlay('authOverlay');
            showToast(authMode === 'login' ? '✦ Bon retour ' + user + ' !' : '🎉 Bienvenue ' + user + ' !', 'success');
        } else {
            var e = document.getElementById('authErr');
            e.innerText = d.error;
            e.style.display = 'block';
        }
    });
}

function setLoggedIn(username) {
    currentUser = username;
    var av = document.getElementById('userAv');
    av.innerText = username[0].toUpperCase();
    av.className = 'user-avatar';
    document.getElementById('uName').innerText = username;
    document.getElementById('uStatus').innerText = 'Connecté — cliquer pour déconnecter';
}

function logout() {
    fetch('/logout', {method:'POST'}).then(function() {
        currentUser = null;
        var av = document.getElementById('userAv');
        av.innerText = '?';
        av.className = 'user-avatar guest';
        document.getElementById('uName').innerText = 'Mode invité';
        document.getElementById('uStatus').innerText = 'Cliquer pour se connecter';
        try { promptHistory = JSON.parse(localStorage.getItem('astax_history') || '[]'); } catch(e) { promptHistory = []; }
        updateBadges();
        showToast('Déconnecté. À bientôt !', 'info');
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

    system = """Tu es un assistant créatif qui aide à créer des images avec une IA générative.""" + style_hint + """

Pose des questions précises en français, puis génère un prompt détaillé en anglais.

Règles STRICTES :
- UNE seule question courte à la fois
- Maximum 3 questions avant de générer
- Avant de générer, demande : "Combien d'images souhaitez-vous ? (1 à 5)"
- Quand tu as tout, réponds UNIQUEMENT avec ce format (3 lignes séparées, rien d'autre) :
GENERATE: [prompt anglais ultra détaillé, qualité maximale, inclure le style si précisé]
COUNT: [nombre 1-5]
MESSAGE: [phrase courte et enthousiaste en français]"""

    response = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        max_tokens=600,
        messages=[{"role": "system", "content": system}] + messages
    )
    text = response.choices[0].message.content

    if "GENERATE:" in text:
        lines = text.split("\n")
        prompt, count, message = "", 1, "Génération en cours ✨"
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
    negative_prompt = data.get("negative_prompt", "")
    style = data.get("style", "")
    full_prompt = (prompt + ", " + style).strip(", ") if style else prompt

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
    if not username or not password: return jsonify({"success": False, "error": "Remplis tous les champs."})
    if len(password) < 6: return jsonify({"success": False, "error": "Mot de passe trop court (6 min)."})
    if username in users: return jsonify({"success": False, "error": "Nom d'utilisateur déjà pris."})
    users[username] = {"password_hash": hash_password(password), "galleries": {}, "prompt_history": []}
    session["username"] = username
    return jsonify({"success": True})

@app.route("/login", methods=["POST"])
def login():
    data = request.json
    username = data.get("username", "").strip()
    password = data.get("password", "")
    if username not in users: return jsonify({"success": False, "error": "Utilisateur introuvable."})
    if users[username]["password_hash"] != hash_password(password): return jsonify({"success": False, "error": "Mot de passe incorrect."})
    session["username"] = username
    return jsonify({"success": True, "prompt_history": users[username].get("prompt_history", [])})

@app.route("/logout", methods=["POST"])
def logout():
    session.pop("username", None)
    return jsonify({"success": True})

@app.route("/galleries")
def get_galleries():
    username = session.get("username")
    if username and username in users: return jsonify(users[username]["galleries"])
    return jsonify({})

@app.route("/create-folder", methods=["POST"])
def create_folder():
    username = session.get("username")
    if not username: return jsonify({"success": False})
    name = request.json.get("name", "").strip()
    if name and name not in users[username]["galleries"]: users[username]["galleries"][name] = []
    return jsonify({"success": True})

@app.route("/save-image", methods=["POST"])
def save_image():
    username = session.get("username")
    if not username: return jsonify({"success": False})
    data = request.json
    folder = data.get("folder")
    if folder in users[username]["galleries"]:
        users[username]["galleries"][folder].append({"id": str(uuid.uuid4()), "image_b64": data.get("image_b64"), "prompt": data.get("prompt", "")})
    return jsonify({"success": True})

@app.route("/delete-image", methods=["POST"])
def delete_image():
    username = session.get("username")
    if not username: return jsonify({"success": False})
    data = request.json
    folder, image_id = data.get("folder"), data.get("id")
    if folder in users[username]["galleries"]:
        users[username]["galleries"][folder] = [i for i in users[username]["galleries"][folder] if str(i["id"]) != str(image_id)]
    return jsonify({"success": True})

@app.route("/save-history", methods=["POST"])
def save_history():
    username = session.get("username")
    if username and username in users: users[username]["prompt_history"] = request.json.get("history", [])
    return jsonify({"success": True})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=7860)
