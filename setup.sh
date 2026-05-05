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

# ── 2. Créer le venv ───────────────────────────────────────
echo "→  Création de l'environnement virtuel .venv …"
"$PYTHON" -m venv .venv

# ── 3. Supprimer le marqueur EXTERNALLY-MANAGED (Homebrew/macOS) ──
# Ce fichier empêche pip de fonctionner dans le venv sur macOS + Homebrew.
# Sa suppression est sans danger car elle ne concerne que ce venv isolé.
find .venv/lib -name "EXTERNALLY-MANAGED" -delete 2>/dev/null && \
  echo "✓  Marqueur EXTERNALLY-MANAGED supprimé (macOS Homebrew)" || true

# ── 4. Installer les dépendances ───────────────────────────
echo "→  Installation des dépendances (2–5 min) …"
.venv/bin/python -m pip install --upgrade pip --quiet
.venv/bin/python -m pip install -r requirements.txt

# ── 5. Copier .env si absent ───────────────────────────────
if [ ! -f .env ]; then
  cp .env.example .env
  echo "✓  Fichier .env créé depuis .env.example"
else
  echo "✓  Fichier .env déjà présent"
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
