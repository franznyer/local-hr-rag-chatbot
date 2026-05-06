#!/usr/bin/env bash
# run.sh — Lanceur Linux
# Usage : bash run.sh

cd "$(dirname "$0")"

echo ""
echo "======================================================="
echo "  Local HR RAG Chatbot"
echo "======================================================="
echo ""

if [ ! -f ".venv/bin/python" ]; then
  echo "→  Premier lancement : installation de l'environnement…"
  bash setup.sh
else
  echo "✓  Environnement virtuel prêt"
  .venv/bin/python -m pip install -r requirements.txt --quiet
fi

if [ ! -f ".env" ]; then
  cp .env.example .env
fi

if command -v ollama &>/dev/null; then
  if ! curl -s http://localhost:11434/api/tags >/dev/null 2>&1; then
    echo "→  Démarrage du serveur Ollama…"
    ollama serve &>/dev/null &
    sleep 2
  fi
fi

# Ouvrir le navigateur si xdg-open est disponible
(sleep 2 && xdg-open http://localhost:8501 2>/dev/null) &

echo "→  Lancement sur http://localhost:8501"
echo ""
.venv/bin/python -m streamlit run app.py \
  --server.headless true \
  --browser.gatherUsageStats false
