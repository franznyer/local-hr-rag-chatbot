#!/usr/bin/env bash
# setup.sh — Installation simplifiée pour macOS / Linux
# Usage : bash setup.sh

set -e

echo ""
echo "======================================================="
echo "  Installation — Local HR RAG Chatbot"
echo "======================================================="
echo ""

# ── 1. Vérifier Python 3.10+ ───────────────────────────────
PYTHON=$(command -v python3 || command -v python || true)
if [ -z "$PYTHON" ]; then
  echo "❌  Python 3 introuvable. Installez-le depuis https://www.python.org/"
  exit 1
fi

PY_VERSION=$("$PYTHON" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
PY_MAJOR=$("$PYTHON" -c "import sys; print(sys.version_info.major)")
PY_MINOR=$("$PYTHON" -c "import sys; print(sys.version_info.minor)")

if [ "$PY_MAJOR" -lt 3 ] || { [ "$PY_MAJOR" -eq 3 ] && [ "$PY_MINOR" -lt 10 ]; }; then
  echo "❌  Python $PY_VERSION détecté. Python 3.10+ requis."
  exit 1
fi
echo "✓  Python $PY_VERSION détecté"

# ── 2. Créer le venv si absent ─────────────────────────────
VENV_PYTHON=".venv/bin/python"
if [ ! -f "$VENV_PYTHON" ]; then
  echo "→  Création de l'environnement virtuel .venv …"
  "$PYTHON" -m venv .venv

  # Supprimer le marqueur EXTERNALLY-MANAGED (Homebrew macOS).
  # Sans danger : ne concerne que ce venv isolé, pas Python système.
  find .venv/lib -name "EXTERNALLY-MANAGED" -delete 2>/dev/null && \
    echo "✓  Marqueur EXTERNALLY-MANAGED supprimé (macOS Homebrew)" || true
else
  echo "✓  Environnement virtuel .venv existant — mise à jour des dépendances"
fi

# ── 3. Installer / mettre à jour les dépendances ───────────
# Toujours exécuté : garantit que toutes les dépendances de requirements.txt
# sont présentes, même après un ajout ou une installation partielle.
echo "→  Vérification des dépendances …"
.venv/bin/python -m pip install --upgrade pip --quiet
.venv/bin/python -m pip install -r requirements.txt --quiet

# ── 4. Copier .env si absent ───────────────────────────────
if [ ! -f .env ]; then
  cp .env.example .env
  echo "✓  Fichier .env créé depuis .env.example"
else
  echo "✓  Fichier .env déjà présent"
fi

# ── 5. Vérifier Ollama ─────────────────────────────────────
echo ""
echo "-------------------------------------------------------"
echo "  Vérification Ollama"
echo "-------------------------------------------------------"

if ! command -v ollama &>/dev/null; then
  echo "⚠️   Ollama non installé. Téléchargez-le sur https://ollama.ai"
else
  # Déterminer le modèle configuré dans .env
  MODEL=$(grep -E '^MODEL_NAME=' .env 2>/dev/null | cut -d= -f2 | tr -d ' "' || echo "llama3")
  MODEL=${MODEL:-llama3}

  # Vérifier si le modèle exact est déjà disponible (tag inclus)
  if ollama list 2>/dev/null | awk '{print $1}' | grep -qxF "$MODEL"; then
    echo "✓  Modèle '$MODEL' déjà téléchargé"
  else
    echo "→  Téléchargement du modèle '$MODEL' (peut prendre plusieurs minutes) …"
    echo "   Si le téléchargement échoue, relancez : ollama pull $MODEL"
    echo "   Ollama reprend automatiquement là où il s'est arrêté."
    ollama pull "$MODEL" || {
      echo ""
      echo "⚠️   Téléchargement interrompu. Relancez : ollama pull $MODEL"
      echo "   Modèle alternatif plus léger : ollama pull llama3.2"
    }
  fi

  # Vérifier si le serveur Ollama tourne
  if curl -s http://localhost:11434/api/tags >/dev/null 2>&1; then
    echo "✓  Serveur Ollama en cours d'exécution"
  else
    echo "⚠️   Serveur Ollama non démarré."
    echo "   Si vous utilisez l'app Ollama Desktop, ouvrez-la."
    echo "   Sinon lancez dans un terminal séparé : ollama serve"
  fi
fi

echo ""
echo "======================================================="
echo "  Installation terminée !"
echo "======================================================="
echo ""
echo "  Prochaines étapes :"
echo "  1. Activez le venv :    source .venv/bin/activate"
echo "  2. Vérifiez :           python scripts/check_setup.py"
echo "  3. Lancez l'app :       streamlit run app.py"
echo ""
