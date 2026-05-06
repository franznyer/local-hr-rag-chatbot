#!/usr/bin/env bash
# run.command — Lanceur macOS (double-clic dans le Finder)
# Place ce fichier à la racine du projet, puis : chmod +x run.command

# Se positionner dans le dossier du script, quel que soit l'endroit depuis lequel il est ouvert
cd "$(dirname "$0")"

echo ""
echo "======================================================="
echo "  Local HR RAG Chatbot"
echo "======================================================="
echo ""

# ── 1. Venv — installer si absent, sinon juste mettre à jour ─
if [ ! -f ".venv/bin/python" ]; then
  echo "→  Premier lancement : installation de l'environnement…"
  bash setup.sh
else
  echo "✓  Environnement virtuel prêt"
  # Mise à jour silencieuse des dépendances si requirements.txt a changé
  .venv/bin/python -m pip install -r requirements.txt --quiet
fi

# ── 2. Fichier .env ──────────────────────────────────────────
if [ ! -f ".env" ]; then
  cp .env.example .env
  echo "✓  Fichier .env créé — vérifiez la configuration si besoin"
fi

# ── 3. Ollama ────────────────────────────────────────────────
if command -v ollama &>/dev/null; then
  # Démarrer le serveur s'il ne tourne pas déjà
  if ! curl -s http://localhost:11434/api/tags >/dev/null 2>&1; then
    echo "→  Démarrage du serveur Ollama en arrière-plan…"
    ollama serve &>/dev/null &
    sleep 2
  else
    echo "✓  Serveur Ollama déjà actif"
  fi

  # Vérifier que le modèle configuré est disponible
  MODEL=$(grep -E '^MODEL_NAME=' .env 2>/dev/null | cut -d= -f2 | tr -d ' "')
  MODEL=${MODEL:-llama3.2}
  if ! ollama list 2>/dev/null | awk '{print $1}' | grep -qxF "$MODEL"; then
    echo "→  Modèle '$MODEL' non trouvé — téléchargement…"
    ollama pull "$MODEL" || echo "⚠️   Échec. Relancez : ollama pull $MODEL"
  fi
fi

# ── 4. Ouvrir le navigateur après 2 secondes ─────────────────
(sleep 2 && open http://localhost:8501) &

# ── 5. Lancer l'application ──────────────────────────────────
echo ""
echo "→  Lancement de l'application sur http://localhost:8501"
echo "   Fermez cette fenêtre pour arrêter l'application."
echo ""

.venv/bin/python -m streamlit run app.py \
  --server.headless true \
  --browser.gatherUsageStats false
