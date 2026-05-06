"""
Local HR RAG Chatbot — Streamlit UI
Design: warm-paper editorial, forest-green accent, three-region layout.
"""
import html as _html
import logging
import sys
import time
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).parent))

import src.config as cfg
from src.providers.base import Message
from src.rag_pipeline import RAGPipeline

logging.basicConfig(
    level=getattr(logging, cfg.LOG_LEVEL, logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Local HR — Assistant RH",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Design system CSS ─────────────────────────────────────────────────────────
st.markdown("""
<link rel="preconnect" href="https://fonts.googleapis.com"/>
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin/>
<link href="https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&family=JetBrains+Mono:wght@400;500;600&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet"/>
<style>
:root {
  --bg:          #f4f1ea;
  --bg-card:     #faf8f3;
  --bg-sunk:     #ece8de;
  --ink:         #1a1814;
  --ink-soft:    #4a463e;
  --ink-mute:    #847f73;
  --ink-faint:   #b6b1a4;
  --rule:        #d9d4c5;
  --rule-soft:   #e6e1d3;
  --accent:      oklch(0.45 0.08 155);
  --accent-soft: oklch(0.92 0.04 155);
  --accent-ink:  oklch(0.32 0.06 155);
  --ok:          oklch(0.55 0.12 155);
  --bad:         oklch(0.55 0.16 25);
  --serif:       "Instrument Serif", "Times New Roman", serif;
  --sans:        "Inter", -apple-system, BlinkMacSystemFont, sans-serif;
  --mono:        "JetBrains Mono", ui-monospace, monospace;
  --radius:      6px;
  --radius-lg:   10px;
}

/* ── Global ── */
html, body, .stApp {
  background: var(--bg) !important;
  font-family: var(--sans) !important;
  color: var(--ink) !important;
}
#MainMenu, footer, header { display: none !important; }
.stDeployButton { display: none !important; }
.block-container { padding: 0 !important; max-width: 100% !important; }
[data-testid="column"] { padding: 0 !important; }

/* ── Sidebar ── */
[data-testid="stSidebar"] {
  background: var(--bg-card) !important;
  border-right: 1px solid var(--rule) !important;
}
[data-testid="stSidebar"] > div,
[data-testid="stSidebarContent"] { padding: 0 !important; gap: 0 !important; }
[data-testid="stSidebar"] .stSelectbox label,
[data-testid="stSidebar"] .stTextInput label { display: none !important; }
[data-testid="stSidebar"] .stSelectbox [data-baseweb="select"] > div,
[data-testid="stSidebar"] .stTextInput input {
  background: var(--bg) !important;
  border: 1px solid var(--rule) !important;
  border-radius: var(--radius) !important;
  font-family: var(--mono) !important;
  font-size: 12px !important;
  color: var(--ink) !important;
}
[data-testid="stSidebar"] .stButton button {
  background: var(--bg) !important;
  border: 1px solid var(--rule) !important;
  color: var(--ink) !important;
  border-radius: var(--radius) !important;
  font-size: 12px !important;
  font-family: var(--sans) !important;
  width: 100% !important;
  text-align: left !important;
  padding: 8px 12px !important;
  transition: all .15s !important;
}
[data-testid="stSidebar"] .stButton button:hover {
  border-color: var(--ink-mute) !important;
  background: var(--bg-sunk) !important;
}

/* ── Main chat area ── */
.stChatInput > div {
  background: var(--bg-card) !important;
  border: 1px solid var(--rule) !important;
  border-radius: var(--radius-lg) !important;
}
.stChatInput textarea {
  font-family: var(--sans) !important;
  font-size: 14px !important;
  color: var(--ink) !important;
  background: transparent !important;
}
.stChatInput textarea::placeholder { color: var(--ink-faint) !important; }
.stChatInput [data-testid="stChatInputSubmitButton"] button,
.stChatInput button[kind="primaryFormSubmit"] {
  background: var(--ink) !important;
  border-radius: var(--radius) !important;
  color: var(--bg) !important;
}

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: var(--rule); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: var(--ink-faint); }

/* ── Custom components ── */

/* Brand */
.brand-header {
  padding: 20px 22px 16px;
  border-bottom: 1px solid var(--rule);
}
.brand { display: flex; align-items: center; gap: 11px; }
.brand-mark {
  width: 24px; height: 24px;
  border: 1.5px solid var(--ink);
  border-radius: 4px;
  position: relative;
  background: var(--bg);
  flex-shrink: 0;
}
.brand-mark::before {
  content: "";
  position: absolute;
  left: 4px; right: 4px; top: 7px;
  height: 1.5px; background: var(--ink);
}
.brand-mark::after {
  content: "";
  position: absolute;
  left: 4px; right: 9px; top: 12px;
  height: 1.5px; background: var(--ink);
}
.brand-dot {
  position: absolute;
  right: 3px; top: 3px;
  width: 5px; height: 5px;
  background: var(--ok);
  border-radius: 50%;
  box-shadow: 0 0 0 2px var(--bg-card);
}
.brand-name {
  font-family: var(--serif);
  font-size: 21px;
  line-height: 1;
  letter-spacing: -.01em;
  color: var(--ink);
}
.brand-name em { font-style: italic; color: var(--ink-soft); }
.brand-tag {
  font-family: var(--mono);
  font-size: 9.5px;
  letter-spacing: .05em;
  text-transform: uppercase;
  color: var(--ink-mute);
  margin-top: 3px;
}

/* Rail sections */
.rail-section {
  padding: 15px 20px;
  border-bottom: 1px solid var(--rule);
}
.section-label {
  font-family: var(--mono);
  font-size: 9.5px;
  letter-spacing: .08em;
  text-transform: uppercase;
  color: var(--ink-mute);
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}
.section-label .num { color: var(--ink-faint); }

/* Status */
.status-grid {
  display: flex;
  flex-direction: column;
  gap: 7px;
  font-family: var(--mono);
  font-size: 11px;
}
.status-row { display: flex; justify-content: space-between; align-items: center; }
.status-key { color: var(--ink-mute); }
.status-val { color: var(--ink); display: flex; align-items: center; gap: 6px; }
.pulse {
  width: 6px; height: 6px;
  border-radius: 50%;
  background: var(--ok);
  flex-shrink: 0;
  animation: pulse 2s infinite;
}
.pulse.bad { background: var(--bad); animation: none; }
@keyframes pulse {
  0%   { box-shadow: 0 0 0 0 oklch(0.55 0.12 155 / .4); }
  70%  { box-shadow: 0 0 0 5px oklch(0.55 0.12 155 / 0); }
  100% { box-shadow: 0 0 0 0 oklch(0.55 0.12 155 / 0); }
}

/* Corpus list */
.corpus-list { display: flex; flex-direction: column; }
.corpus-item {
  padding: 7px 0;
  border-top: 1px solid var(--rule-soft);
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  gap: 8px;
}
.corpus-item:first-child { border-top: none; padding-top: 0; }
.corpus-name {
  font-size: 12px;
  color: var(--ink);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  flex: 1;
}
.corpus-meta { font-family: var(--mono); font-size: 10px; color: var(--ink-mute); flex-shrink: 0; }

/* Chat header */
.chat-header {
  padding: 13px 28px;
  border-bottom: 1px solid var(--rule);
  background: var(--bg);
  position: sticky; top: 0; z-index: 10;
}
.crumb {
  font-family: var(--mono);
  font-size: 10px;
  letter-spacing: .06em;
  text-transform: uppercase;
  color: var(--ink-mute);
  display: flex;
  align-items: center;
  gap: 7px;
}
.crumb .sep { color: var(--ink-faint); }
.crumb .here { color: var(--ink); }

/* Welcome */
.welcome { padding: 32px 0 20px; }
.welcome-eyebrow {
  font-family: var(--mono);
  font-size: 10px;
  letter-spacing: .1em;
  text-transform: uppercase;
  color: var(--ink-mute);
  margin-bottom: 14px;
}
.welcome-title {
  font-family: var(--serif);
  font-size: 40px;
  line-height: 1.07;
  letter-spacing: -.015em;
  margin: 0 0 12px;
  color: var(--ink);
}
.welcome-title em { color: var(--accent); font-style: italic; }
.welcome-sub {
  font-size: 14.5px;
  color: var(--ink-soft);
  line-height: 1.55;
  max-width: 480px;
  margin: 0;
}
.suggest-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
  margin-top: 22px;
}
.suggest-btn {
  text-align: left;
  padding: 13px 15px;
  background: var(--bg-card);
  border: 1px solid var(--rule);
  border-radius: var(--radius-lg);
  cursor: pointer;
  transition: all .18s;
  width: 100%;
  font-family: var(--sans);
}
.suggest-btn:hover { border-color: var(--ink); background: var(--bg); transform: translateY(-1px); }
.suggest-cat {
  font-family: var(--mono);
  font-size: 9px;
  letter-spacing: .08em;
  text-transform: uppercase;
  color: var(--accent);
  margin-bottom: 5px;
}
.suggest-q { font-size: 12.5px; line-height: 1.4; color: var(--ink); }

/* Messages */
.msg {
  margin: 22px 0;
  animation: msgIn .35s cubic-bezier(.2,.8,.2,1);
}
@keyframes msgIn {
  from { opacity: 0; transform: translateY(6px); }
  to   { opacity: 1; transform: translateY(0); }
}
.msg-role {
  font-family: var(--mono);
  font-size: 9.5px;
  letter-spacing: .1em;
  text-transform: uppercase;
  color: var(--ink-mute);
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 9px;
}
.role-dot { width: 6px; height: 6px; border-radius: 50%; background: var(--ink-faint); flex-shrink: 0; }
.msg-ts { margin-left: auto; color: var(--ink-faint); }
.msg.user .role-dot { background: var(--ink); }
.msg.assistant .role-dot { background: var(--accent); }
.msg-body { font-size: 14.5px; line-height: 1.65; color: var(--ink); }
.msg.user .msg-body {
  font-family: var(--serif);
  font-size: 21px;
  line-height: 1.3;
  letter-spacing: -.005em;
}
.msg-body p { margin: 0 0 8px; }
.msg-body p:last-child { margin-bottom: 0; }

/* Confidence bar */
.conf-block {
  margin-top: 14px;
  padding: 10px 14px;
  background: var(--bg-card);
  border: 1px solid var(--rule);
  border-radius: var(--radius-lg);
  display: grid;
  grid-template-columns: auto 1fr auto;
  align-items: center;
  gap: 12px;
  font-family: var(--mono);
  font-size: 11px;
}
.conf-label { color: var(--ink-mute); letter-spacing: .04em; text-transform: uppercase; }
.conf-track { height: 4px; background: var(--bg-sunk); border-radius: 2px; overflow: hidden; }
.conf-fill { height: 100%; background: var(--accent); border-radius: 2px; }
.conf-fill.warn { background: var(--bad); }
.conf-val { color: var(--ink); font-weight: 600; }

/* Sources panel */
.sources-panel {
  border-left: 1px solid var(--rule);
  background: var(--bg-card);
  min-height: 100vh;
}
.sources-head {
  padding: 17px 20px 14px;
  border-bottom: 1px solid var(--rule);
  position: sticky; top: 0;
  background: var(--bg-card);
  z-index: 5;
}
.sources-title { font-family: var(--serif); font-size: 20px; margin: 0 0 2px; color: var(--ink); }
.sources-sub {
  font-family: var(--mono);
  font-size: 10px;
  color: var(--ink-mute);
  letter-spacing: .04em;
  text-transform: uppercase;
}
.sources-empty { padding: 36px 24px; text-align: center; }
.sources-empty-icon {
  width: 48px; height: 48px;
  margin: 0 auto 14px;
  border: 1px solid var(--rule);
  border-radius: 8px;
  background: var(--bg);
  position: relative;
}
.sources-empty-icon::before {
  content: "";
  position: absolute;
  left: 11px; right: 11px; top: 17px;
  height: 1px; background: var(--ink-faint);
}
.sources-empty-icon::after {
  content: "";
  position: absolute;
  left: 11px; right: 20px; top: 24px;
  height: 1px; background: var(--ink-faint);
}
.sources-empty p { font-size: 13px; color: var(--ink-soft); line-height: 1.5; max-width: 200px; margin: 0 auto; }
.sources-empty-hint {
  margin-top: 10px;
  font-family: var(--mono);
  font-size: 10px;
  color: var(--ink-faint);
  letter-spacing: .04em;
  text-transform: uppercase;
}

/* Source card */
.source-card {
  padding: 14px 20px;
  border-bottom: 1px solid var(--rule-soft);
  transition: background .15s;
}
.source-card:hover { background: var(--bg); }
.source-card-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 5px;
}
.src-pin {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 22px; height: 18px;
  padding: 0 6px;
  border-radius: 3px;
  background: var(--accent-soft);
  color: var(--accent-ink);
  font-family: var(--mono);
  font-size: 10px;
  font-weight: 600;
}
.src-score { font-family: var(--mono); font-size: 10px; color: var(--ink-mute); }
.src-name { font-size: 12.5px; font-weight: 500; color: var(--ink); margin: 4px 0 6px; }
.src-snippet {
  font-family: var(--serif);
  font-size: 13px;
  font-style: italic;
  color: var(--ink-soft);
  line-height: 1.45;
  margin-bottom: 7px;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.src-snippet::before { content: "« "; color: var(--ink-faint); }
.src-snippet::after  { content: " »"; color: var(--ink-faint); }
.src-bar-wrap { height: 3px; background: var(--bg-sunk); border-radius: 2px; margin-bottom: 6px; overflow: hidden; }
.src-bar-fill { height: 100%; background: var(--accent); border-radius: 2px; }
.src-meta { font-family: var(--mono); font-size: 10px; color: var(--ink-mute); display: flex; gap: 10px; }

/* Privacy ribbon */
.privacy {
  font-family: var(--mono);
  font-size: 10px;
  color: var(--ink-mute);
  letter-spacing: .04em;
  text-align: center;
  padding: 6px 0 12px;
}

/* Chat column wrapper */
.chat-col-inner {
  max-width: 740px;
  margin: 0 auto;
  padding: 0 28px 8px;
}

/* Provider indicator in sidebar */
.provider-info {
  display: flex;
  align-items: center;
  gap: 7px;
  font-family: var(--mono);
  font-size: 11px;
  color: var(--ink-soft);
  padding: 6px 0 0;
}
.pdot { width: 5px; height: 5px; border-radius: 50%; background: var(--ink-faint); flex-shrink: 0; }
.pdot.local { background: var(--ok); }
</style>
""", unsafe_allow_html=True)

# ── Pipeline cache ────────────────────────────────────────────────────────────
@st.cache_resource(show_spinner="Chargement du pipeline RAG…")
def _get_pipeline(provider: str, model: str) -> RAGPipeline:
    cfg.AI_PROVIDER = provider
    cfg.MODEL_NAME = model
    pipeline = RAGPipeline(provider_name=provider)
    pipeline.initialize()
    return pipeline

# ── Health check (30 s TTL) ───────────────────────────────────────────────────
def _is_healthy(pipeline: RAGPipeline, provider: str, model: str) -> bool:
    key = f"_health_{provider}_{model}"
    cached = st.session_state.get(key)
    if cached and time.monotonic() - cached["ts"] < 30:
        return cached["ok"]
    ok = pipeline.provider_status()["healthy"]
    st.session_state[key] = {"ok": ok, "ts": time.monotonic()}
    return ok

# ── Provider help ─────────────────────────────────────────────────────────────
def _provider_help(provider: str, model: str) -> str:
    if provider == "ollama":
        return (f"**Ollama** ne répond pas. Vérifiez :\n"
                f"1. L'app Ollama Desktop est ouverte, ou `ollama serve` tourne\n"
                f"2. Le modèle est téléchargé : `ollama pull {model}`")
    if provider == "lmstudio":
        return "**LM Studio** ne répond pas. Ouvrez-le, chargez un modèle et démarrez le serveur local."
    return f"Le fournisseur **{provider}** est inaccessible. Vérifiez votre clé API dans `.env`."

# ── Corpus scanner ────────────────────────────────────────────────────────────
def _list_corpus() -> list[dict]:
    docs_dir = cfg.DOCUMENTS_DIR
    exts = {".pdf", ".docx", ".txt", ".md"}
    files = []
    for f in sorted(docs_dir.iterdir()):
        if f.is_file() and f.suffix.lower() in exts:
            size_kb = f.stat().st_size // 1024
            files.append({"name": f.name, "ext": f.suffix[1:].upper(), "size": f"{size_kb} Ko"})
    return files

# ── HTML helpers ──────────────────────────────────────────────────────────────
def _e(text: str) -> str:
    return _html.escape(str(text))

def render_brand() -> None:
    st.markdown("""
    <div class="brand-header">
      <div class="brand">
        <div class="brand-mark"><span class="brand-dot"></span></div>
        <div>
          <div class="brand-name">Local <em>HR</em></div>
          <div class="brand-tag">RAG · 100% local · privé</div>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

def render_status(provider: str, model: str, chunks: int, healthy: bool) -> None:
    pulse_cls = "pulse" if healthy else "pulse bad"
    status_text = "connecté" if healthy else "hors ligne"
    st.markdown(f"""
    <div class="rail-section">
      <div class="section-label"><span>État du pipeline</span></div>
      <div class="status-grid">
        <div class="status-row">
          <span class="status-key">Statut</span>
          <span class="status-val"><span class="{pulse_cls}"></span>{status_text}</span>
        </div>
        <div class="status-row">
          <span class="status-key">Fournisseur</span>
          <span class="status-val">{_e(provider)}</span>
        </div>
        <div class="status-row">
          <span class="status-key">Modèle</span>
          <span class="status-val">{_e(model)}</span>
        </div>
        <div class="status-row">
          <span class="status-key">Chunks indexés</span>
          <span class="status-val">{chunks:,}</span>
        </div>
        <div class="status-row">
          <span class="status-key">Embeddings</span>
          <span class="status-val">all-MiniLM-L6-v2</span>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

def render_corpus(files: list[dict]) -> None:
    if not files:
        st.markdown("""
        <div class="rail-section">
          <div class="section-label"><span>Corpus indexé</span><span class="num">vide</span></div>
          <div style="font-size:12px;color:var(--ink-mute)">Déposez des fichiers dans <code>documents/</code>.</div>
        </div>
        """, unsafe_allow_html=True)
        return
    items = "".join(
        f'<div class="corpus-item">'
        f'<span class="corpus-name" title="{_e(f["name"])}">{_e(f["name"])}</span>'
        f'<span class="corpus-meta">{_e(f["ext"])} · {_e(f["size"])}</span>'
        f'</div>'
        for f in files
    )
    st.markdown(f"""
    <div class="rail-section">
      <div class="section-label">
        <span>Corpus indexé</span>
        <span class="num">{len(files)} fichier{"s" if len(files) > 1 else ""}</span>
      </div>
      <div class="corpus-list">{items}</div>
    </div>
    """, unsafe_allow_html=True)

def render_chat_header(provider: str, model: str) -> None:
    st.markdown(f"""
    <div class="chat-header">
      <div class="crumb">
        <span>Espace</span><span class="sep">/</span>
        <span>Ressources humaines</span><span class="sep">/</span>
        <span class="here">Conversation</span>
        <span class="sep">·</span>
        <span>{_e(provider)} / {_e(model)}</span>
      </div>
    </div>
    """, unsafe_allow_html=True)

def render_welcome() -> str | None:
    """Render welcome state with suggestion buttons. Returns chosen suggestion or None."""
    suggestions = [
        ("Congés",      "Combien de jours de congés pour un mariage ?"),
        ("Télétravail", "Quelles sont les règles du télétravail ?"),
        ("Contrat",     "Comment fonctionne la période d'essai CDI cadre ?"),
        ("Rémunération","Quelle est la grille salariale pour les cadres ?"),
    ]
    btns = "".join(
        f'<div class="suggest-cat">{_e(cat)}</div><div class="suggest-q">{_e(q)}</div>'
        for cat, q in suggestions
    )
    st.markdown("""
    <div class="welcome">
      <div class="welcome-eyebrow">— Bonjour</div>
      <h1 class="welcome-title">Posez une question.<br/><em>Citez un règlement.</em></h1>
      <p class="welcome-sub">
        Cet assistant répond uniquement depuis vos documents RH locaux.
        Chaque réponse est sourcée et auditable. Aucune donnée ne quitte votre machine.
      </p>
    </div>
    """, unsafe_allow_html=True)

    cols = st.columns(2, gap="small")
    chosen = None
    for i, (cat, q) in enumerate(suggestions):
        with cols[i % 2]:
            if st.button(f"**{cat}**\n{q}", key=f"sug_{i}", use_container_width=True):
                chosen = q
    return chosen

def render_user_msg(text: str, ts: str) -> None:
    st.markdown(f"""
    <div class="msg user">
      <div class="msg-role">
        <span class="role-dot"></span>Vous<span class="msg-ts">{_e(ts)}</span>
      </div>
      <div class="msg-body">{_e(text)}</div>
    </div>
    """, unsafe_allow_html=True)

def render_assistant_msg(text: str, ts: str, confidence: float, sources: list) -> None:
    # Render markdown-like content safely
    body = _e(text).replace("\n\n", "</p><p>").replace("\n", "<br/>")
    pct = int(confidence * 100)
    color_cls = "conf-fill warn" if confidence < 0.4 else "conf-fill"
    sources_html = ""
    if sources:
        pins = " ".join(
            f'<span style="display:inline-flex;align-items:center;justify-content:center;'
            f'min-width:18px;height:15px;padding:0 4px;margin:0 1px;border-radius:3px;'
            f'background:var(--accent-soft);color:var(--accent-ink);font-family:var(--mono);'
            f'font-size:9px;font-weight:600;vertical-align:1px;">{i+1}</span>'
            for i in range(len(sources))
        )
        sources_html = f'<div style="margin-top:8px;font-size:13px;color:var(--ink-mute)">Sources citées : {pins}</div>'

    st.markdown(f"""
    <div class="msg assistant">
      <div class="msg-role">
        <span class="role-dot"></span>Assistant<span class="msg-ts">{_e(ts)}</span>
      </div>
      <div class="msg-body"><p>{body}</p></div>
      {sources_html}
      <div class="conf-block">
        <span class="conf-label">Confiance</span>
        <div class="conf-track"><div class="{color_cls}" style="width:{pct}%"></div></div>
        <span class="conf-val">{pct}%</span>
      </div>
    </div>
    """, unsafe_allow_html=True)

def render_sources_panel(sources: list, query: str) -> None:
    if not sources:
        st.markdown("""
        <div class="sources-panel">
          <div class="sources-head">
            <div class="sources-title">Sources</div>
            <div class="sources-sub">aucune requête active</div>
          </div>
          <div class="sources-empty">
            <div class="sources-empty-icon"></div>
            <p>Posez une question — les extraits cités apparaîtront ici, classés par pertinence.</p>
            <div class="sources-empty-hint">— RAG · top-K=4</div>
          </div>
        </div>
        """, unsafe_allow_html=True)
        return

    q_short = (query[:30] + "…") if len(query) > 30 else query
    n = len(sources)
    cards = ""
    for i, src in enumerate(sources):
        pct = int(src["score"] * 100)
        snippet = src.get("text", "")[:200]
        cards += f"""
        <div class="source-card">
          <div class="source-card-head">
            <span class="src-pin">{i+1}</span>
            <span class="src-score">{pct}% pertinence</span>
          </div>
          <div class="src-name">{_e(src['source'])}</div>
          <div class="src-snippet">{_e(snippet)}</div>
          <div class="src-bar-wrap"><div class="src-bar-fill" style="width:{pct}%"></div></div>
          <div class="src-meta">
            <span>chunk #{_e(str(src['chunk_index']))}</span>
            <span>cosine {src['score']:.2f}</span>
          </div>
        </div>
        """

    st.markdown(f"""
    <div class="sources-panel">
      <div class="sources-head">
        <div class="sources-title">Sources</div>
        <div class="sources-sub">{n} extrait{"s" if n > 1 else ""} · « {_e(q_short)} »</div>
      </div>
      {cards}
    </div>
    """, unsafe_allow_html=True)

# ── Session state ─────────────────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []  # [{role, content, ts, sources?, confidence?}]
if "provider" not in st.session_state:
    st.session_state.provider = cfg.AI_PROVIDER
if "model" not in st.session_state:
    st.session_state.model = cfg.MODEL_NAME

PROVIDER_LOCAL = {"ollama", "lmstudio"}
PROVIDER_OPTIONS = ["ollama", "lmstudio", "openai", "claude", "mistral"]

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    render_brand()

    # Provider section
    st.markdown("""
    <div class="rail-section" style="padding-bottom:10px">
      <div class="section-label"><span>Fournisseur IA</span></div>
    </div>
    """, unsafe_allow_html=True)

    provider_choice = st.selectbox(
        "provider",
        options=PROVIDER_OPTIONS,
        index=PROVIDER_OPTIONS.index(st.session_state.provider)
              if st.session_state.provider in PROVIDER_OPTIONS else 0,
        label_visibility="collapsed",
        key="provider_select",
    )
    is_local = provider_choice in PROVIDER_LOCAL
    dot_cls  = "pdot local" if is_local else "pdot"
    mode_txt = "Mode local — 100% privé" if is_local else "Cloud — clé API requise"
    st.markdown(
        f'<div class="provider-info"><span class="{dot_cls}"></span>{mode_txt}</div>',
        unsafe_allow_html=True,
    )
    st.markdown('<div style="margin-top:10px;font-size:11px;color:var(--ink-mute);font-family:var(--mono)">Modèle</div>', unsafe_allow_html=True)
    model_input = st.text_input("model", value=st.session_state.model, label_visibility="collapsed", key="model_input")
    st.markdown('<div style="height:6px"></div>', unsafe_allow_html=True)

    # Update state when provider/model change
    if provider_choice != st.session_state.provider or model_input != st.session_state.model:
        st.session_state.provider = provider_choice
        st.session_state.model = model_input

    # Status section — shown after first use
    if st.session_state.get("pipeline_loaded"):
        try:
            _p = _get_pipeline(provider_choice, model_input)
            n_chunks = _p._vector_store.count() if _p._vector_store else 0
            healthy  = _is_healthy(_p, provider_choice, model_input)
            render_status(provider_choice, model_input, n_chunks, healthy)
            if not healthy:
                st.warning(_provider_help(provider_choice, model_input))
        except Exception:
            render_status(provider_choice, model_input, 0, False)
    else:
        st.markdown("""
        <div class="rail-section">
          <div class="section-label"><span>État du pipeline</span></div>
          <div style="font-family:var(--mono);font-size:11px;color:var(--ink-mute)">
            Posez une question pour initialiser.
          </div>
        </div>
        """, unsafe_allow_html=True)

    # Corpus
    corpus = _list_corpus()
    render_corpus(corpus)

    # Reindex button
    st.markdown('<div class="rail-section" style="border-bottom:none">', unsafe_allow_html=True)
    if st.button("↻  Réindexer les documents", use_container_width=True, key="reindex_btn"):
        _get_pipeline.clear()
        with st.spinner("Réindexation en cours…"):
            try:
                pipeline = _get_pipeline(provider_choice, model_input)
                n = pipeline.reindex()
                st.session_state["pipeline_loaded"] = True
                st.success(f"{n} chunk(s) réindexé(s).")
                st.rerun()
            except Exception as exc:
                st.error(str(exc))

    if st.session_state.messages and st.button("🗑  Effacer la conversation", use_container_width=True, key="clear_btn"):
        st.session_state.messages = []
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

# ── Main area: chat column + sources column ───────────────────────────────────
col_chat, col_sources = st.columns([3, 2], gap="none")

# ── Sources column (render first so it's always visible) ─────────────────────
with col_sources:
    last_assistant = next(
        (m for m in reversed(st.session_state.messages) if m["role"] == "assistant"),
        None,
    )
    last_user = next(
        (m for m in reversed(st.session_state.messages) if m["role"] == "user"),
        None,
    )
    render_sources_panel(
        last_assistant.get("sources", []) if last_assistant else [],
        last_user["content"] if last_user else "",
    )

# ── Chat column ───────────────────────────────────────────────────────────────
with col_chat:
    render_chat_header(provider_choice, model_input)

    st.markdown('<div class="chat-col-inner">', unsafe_allow_html=True)

    # Welcome state or message history
    if not st.session_state.messages:
        suggestion = render_welcome()
    else:
        suggestion = None
        for msg in st.session_state.messages:
            if msg["role"] == "user":
                render_user_msg(msg["content"], msg.get("ts", ""))
            else:
                render_assistant_msg(
                    msg["content"],
                    msg.get("ts", ""),
                    msg.get("confidence", 0.0),
                    msg.get("sources", []),
                )

    st.markdown("</div>", unsafe_allow_html=True)

    # Privacy ribbon
    st.markdown("""
    <div class="privacy">
      🔒 AUCUNE DONNÉE NE QUITTE VOTRE MACHINE · TRAITEMENT 100% LOCAL
    </div>
    """, unsafe_allow_html=True)

# ── Chat input (pinned bottom) ────────────────────────────────────────────────
question = st.chat_input("Posez votre question RH… (réponses uniquement depuis vos documents)")

# Handle suggestion click as a question
if suggestion:
    question = suggestion

if question:
    ts = time.strftime("%H:%M")
    st.session_state.messages.append({"role": "user", "content": question, "ts": ts})

    # Load / reuse pipeline
    try:
        with st.spinner("Initialisation du pipeline…"):
            pipeline = _get_pipeline(provider_choice, model_input)
            st.session_state["pipeline_loaded"] = True
    except Exception as exc:
        st.error(f"Impossible d'initialiser le pipeline : {exc}")
        st.stop()

    # Provider health check
    if not _is_healthy(pipeline, provider_choice, model_input):
        st.warning(f"⚠️ **{provider_choice}** n'est pas joignable. "
                   + _provider_help(provider_choice, model_input))

    # Build history for multi-turn
    history = [
        Message(role=m["role"], content=m["content"])
        for m in st.session_state.messages[:-1]
        if m["role"] in ("user", "assistant")
    ]

    with st.spinner("Recherche dans les documents…"):
        result = pipeline.query(question, chat_history=history)

    if result.success:
        st.session_state.messages.append({
            "role": "assistant",
            "content": result.answer,
            "ts": time.strftime("%H:%M"),
            "sources": result.sources,
            "confidence": result.confidence,
        })
    else:
        st.session_state.messages.append({
            "role": "assistant",
            "content": f"❌ Erreur : {result.error}",
            "ts": time.strftime("%H:%M"),
            "sources": [],
            "confidence": 0.0,
        })

    st.rerun()
