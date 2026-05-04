"""
Local HR RAG Chatbot — Streamlit UI entry point.
Run with: streamlit run app.py
"""
import logging
import sys
from pathlib import Path

import streamlit as st

# Make sure `src/` is importable when running from project root
sys.path.insert(0, str(Path(__file__).parent))

import src.config as cfg
from src.providers.base import Message
from src.rag_pipeline import RAGPipeline

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
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
# Sidebar — configuration
# ---------------------------------------------------------------------------
with st.sidebar:
    st.title("⚙️ Configuration")

    provider_choice = st.selectbox(
        "Fournisseur IA",
        options=["ollama", "lmstudio", "openai", "claude", "mistral"],
        index=["ollama", "lmstudio", "openai", "claude", "mistral"].index(
            cfg.AI_PROVIDER if cfg.AI_PROVIDER in ["ollama", "lmstudio", "openai", "claude", "mistral"]
            else "ollama"
        ),
        help="Sélectionnez le fournisseur IA à utiliser.",
    )

    model_override = st.text_input(
        "Modèle",
        value=cfg.MODEL_NAME,
        help="Nom du modèle (ex: llama3, gpt-4o, claude-sonnet-4-6).",
    )

    st.divider()

    if st.button("🔄 Réindexer les documents", use_container_width=True):
        with st.spinner("Réindexation en cours…"):
            pipeline = _get_pipeline(provider_choice, model_override, force_reload=True)
            n = pipeline.reindex()
        st.success(f"{n} chunk(s) réindexé(s).")

    st.divider()
    st.caption("💡 Modes 100% locaux : **ollama** ou **lmstudio**")

    # Status block
    if "pipeline" in st.session_state:
        status = st.session_state.pipeline.provider_status()
        health_icon = "🟢" if status["healthy"] else "🔴"
        st.markdown(
            f"{health_icon} **{status['provider']}** / `{status['model']}`  \n"
            f"📄 {status['indexed_chunks']} chunks indexés"
        )

# ---------------------------------------------------------------------------
# Pipeline cache (one per provider+model combination)
# ---------------------------------------------------------------------------
@st.cache_resource(show_spinner="Chargement du pipeline RAG…")
def _get_pipeline(provider: str, model_name: str, force_reload: bool = False) -> RAGPipeline:
    cfg.AI_PROVIDER = provider
    cfg.MODEL_NAME = model_name

    pipeline = RAGPipeline(provider_name=provider)
    pipeline.initialize()
    return pipeline


# ---------------------------------------------------------------------------
# Session state
# ---------------------------------------------------------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []  # List[dict] with role/content/sources/confidence

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
            color = "green" if confidence >= 0.6 else "orange" if confidence >= 0.4 else "red"
            st.markdown(
                f"<small>Indice de confiance : <span style='color:{color}'>"
                f"{'★' * round(confidence * 5)}{'☆' * (5 - round(confidence * 5))} "
                f"({confidence:.0%})</span></small>",
                unsafe_allow_html=True,
            )

# Chat input
if question := st.chat_input("Posez votre question RH…"):
    # Show user message immediately
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    # Load / reuse pipeline
    with st.spinner("Recherche dans les documents RH…"):
        try:
            pipeline = _get_pipeline(provider_choice, model_override)
        except Exception as exc:
            st.error(f"Erreur d'initialisation du pipeline : {exc}")
            st.stop()

    # Build chat history for context (assistant messages only carry content)
    history = [
        Message(role=m["role"], content=m["content"])
        for m in st.session_state.messages[:-1]  # exclude the current question
        if m["role"] in ("user", "assistant")
    ]

    with st.spinner("Génération de la réponse…"):
        result = pipeline.query(question, chat_history=history)

    if result.success:
        answer = result.answer
        sources = result.sources
        confidence = result.confidence
        error = None
    else:
        answer = f"❌ Erreur : {result.error}"
        sources = []
        confidence = 0.0
        error = result.error

    # Display assistant response
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
            color = "green" if confidence >= 0.6 else "orange" if confidence >= 0.4 else "red"
            st.markdown(
                f"<small>Indice de confiance : <span style='color:{color}'>"
                f"{'★' * round(confidence * 5)}{'☆' * (5 - round(confidence * 5))} "
                f"({confidence:.0%})</span></small>",
                unsafe_allow_html=True,
            )

    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": answer,
            "sources": sources,
            "confidence": confidence,
        }
    )

# Footer
st.divider()
col1, col2 = st.columns([3, 1])
with col1:
    if st.session_state.messages:
        if st.button("🗑️ Effacer l'historique"):
            st.session_state.messages = []
            st.rerun()
with col2:
    st.caption("Local HR RAG Chatbot v1.0")
