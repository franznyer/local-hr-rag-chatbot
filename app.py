"""
Local HR RAG Chatbot — Streamlit UI entry point.
Run with: streamlit run app.py
"""
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

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="HR RAG Chatbot",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Pipeline cache — keyed on (provider, model_name).
# To invalidate, call _get_pipeline.clear() before re-calling.
# ---------------------------------------------------------------------------
@st.cache_resource(show_spinner="Chargement du pipeline RAG…")
def _get_pipeline(provider: str, model_name: str) -> RAGPipeline:
    cfg.AI_PROVIDER = provider
    cfg.MODEL_NAME = model_name
    pipeline = RAGPipeline(provider_name=provider)
    pipeline.initialize()
    return pipeline


# ---------------------------------------------------------------------------
# Contextual help when a provider is unreachable
# ---------------------------------------------------------------------------
def _provider_help(provider: str, model: str) -> str:
    if provider == "ollama":
        return (
            f"**Ollama** ne répond pas sur `{cfg.OLLAMA_BASE_URL}`.\n\n"
            f"Vérifiez que :\n"
            f"1. Ollama est installé → https://ollama.ai\n"
            f"2. Le service tourne : `ollama serve`\n"
            f"3. Le modèle est téléchargé : `ollama pull {model}`\n"
            f"4. Aucun pare-feu ne bloque le port 11434"
        )
    if provider == "lmstudio":
        return (
            f"**LM Studio** ne répond pas sur `{cfg.LMSTUDIO_BASE_URL}`.\n\n"
            f"Vérifiez que :\n"
            f"1. LM Studio est ouvert\n"
            f"2. Un modèle GGUF est chargé\n"
            f'3. Le serveur local est démarré (onglet "Local Server" → Start)'
        )
    return (
        f"Le fournisseur **{provider}** est inaccessible.\n"
        f"Vérifiez votre clé API dans `.env`."
    )


# ---------------------------------------------------------------------------
# Health check with 30 s TTL to avoid an HTTP request on every re-render
# ---------------------------------------------------------------------------
def _is_healthy(pipeline: RAGPipeline, provider: str, model: str) -> bool:
    cache_key = f"_health_{provider}_{model}"
    cached = st.session_state.get(cache_key)
    if cached and time.monotonic() - cached["ts"] < 30:
        return cached["ok"]
    ok = pipeline.provider_status()["healthy"]
    st.session_state[cache_key] = {"ok": ok, "ts": time.monotonic()}
    return ok


# ---------------------------------------------------------------------------
# Session state initialisation
# ---------------------------------------------------------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []

PROVIDER_OPTIONS = ["ollama", "lmstudio", "openai", "claude", "mistral"]

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
with st.sidebar:
    st.title("⚙️ Configuration")

    provider_choice = st.selectbox(
        "Fournisseur IA",
        options=PROVIDER_OPTIONS,
        index=PROVIDER_OPTIONS.index(cfg.AI_PROVIDER)
        if cfg.AI_PROVIDER in PROVIDER_OPTIONS
        else 0,
        help="Sélectionnez le fournisseur IA à utiliser.",
    )

    model_override = st.text_input(
        "Modèle",
        value=cfg.MODEL_NAME,
        help="Nom du modèle (ex : llama3, gpt-4o, claude-sonnet-4-6).",
    )

    st.divider()

    # Réindexation — clear the cache then rebuild
    if st.button("🔄 Réindexer les documents", use_container_width=True):
        _get_pipeline.clear()
        with st.spinner("Réindexation en cours…"):
            pipeline = _get_pipeline(provider_choice, model_override)
            n = pipeline.reindex()
        st.session_state["pipeline_loaded"] = True
        st.success(f"{n} chunk(s) réindexé(s).")
        st.rerun()

    st.divider()
    st.caption("💡 Modes 100% locaux : **ollama** ou **lmstudio**")

    # Provider status — shown only after the pipeline has been used at least once
    if st.session_state.get("pipeline_loaded"):
        try:
            _pipeline = _get_pipeline(provider_choice, model_override)
            n_chunks = (
                _pipeline._vector_store.count()
                if _pipeline._vector_store
                else 0
            )
            healthy = _is_healthy(_pipeline, provider_choice, model_override)
            icon = "🟢" if healthy else "🔴"
            st.markdown(
                f"{icon} **{provider_choice}** / `{model_override}`  \n"
                f"📄 {n_chunks} chunks indexés"
            )
            if not healthy:
                st.warning(_provider_help(provider_choice, model_override))
        except Exception:
            pass

# ---------------------------------------------------------------------------
# Main chat UI
# ---------------------------------------------------------------------------
st.title("💼 HR RAG Chatbot")
st.caption("Assistant RH basé sur vos documents internes · Mode local · Confidentiel")

# Render chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("sources"):
            with st.expander("📄 Sources citées", expanded=False):
                for src in msg["sources"]:
                    st.markdown(
                        f"- **{src['source']}** (chunk #{src['chunk_index']}, "
                        f"pertinence : {src['score']:.0%})"
                    )
        if msg.get("confidence") is not None:
            confidence = msg["confidence"]
            color = (
                "green" if confidence >= 0.6
                else "orange" if confidence >= 0.4
                else "red"
            )
            st.markdown(
                f"<small>Indice de confiance : <span style='color:{color}'>"
                f"{'★' * round(confidence * 5)}{'☆' * (5 - round(confidence * 5))} "
                f"({confidence:.0%})</span></small>",
                unsafe_allow_html=True,
            )

# Chat input
if question := st.chat_input("Posez votre question RH…"):
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    # Load pipeline (from cache or first build)
    with st.spinner("Initialisation…"):
        try:
            pipeline = _get_pipeline(provider_choice, model_override)
            st.session_state["pipeline_loaded"] = True
        except Exception as exc:
            st.error(f"Impossible d'initialiser le pipeline : {exc}")
            st.stop()

    # Surface provider availability BEFORE trying to generate
    if not _is_healthy(pipeline, provider_choice, model_override):
        st.warning(
            f"⚠️ Le fournisseur **{provider_choice}** n'est pas joignable. "
            "Consultez la barre latérale pour les instructions."
        )

    history = [
        Message(role=m["role"], content=m["content"])
        for m in st.session_state.messages[:-1]
        if m["role"] in ("user", "assistant")
    ]

    with st.spinner("Génération de la réponse…"):
        result = pipeline.query(question, chat_history=history)

    if result.success:
        answer, sources, confidence, error = result.answer, result.sources, result.confidence, None
    else:
        answer = f"❌ Erreur : {result.error}"
        sources, confidence, error = [], 0.0, result.error

    with st.chat_message("assistant"):
        st.markdown(answer)
        if sources:
            with st.expander("📄 Sources citées", expanded=True):
                for src in sources:
                    st.markdown(
                        f"- **{src['source']}** (chunk #{src['chunk_index']}, "
                        f"pertinence : {src['score']:.0%})"
                    )
        if not error:
            color = (
                "green" if confidence >= 0.6
                else "orange" if confidence >= 0.4
                else "red"
            )
            st.markdown(
                f"<small>Indice de confiance : <span style='color:{color}'>"
                f"{'★' * round(confidence * 5)}{'☆' * (5 - round(confidence * 5))} "
                f"({confidence:.0%})</span></small>",
                unsafe_allow_html=True,
            )

    st.session_state.messages.append(
        {"role": "assistant", "content": answer, "sources": sources, "confidence": confidence}
    )

# Footer
st.divider()
col1, col2 = st.columns([3, 1])
with col1:
    if st.session_state.messages and st.button("🗑️ Effacer l'historique"):
        st.session_state.messages = []
        st.rerun()
with col2:
    st.caption("Local HR RAG Chatbot v1.0")
