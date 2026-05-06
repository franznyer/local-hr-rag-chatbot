@echo off
REM run.bat — Lanceur Windows (double-clic)
cd /d "%~dp0"

echo.
echo =======================================================
echo   Local HR RAG Chatbot
echo =======================================================
echo.

REM ── Venv ─────────────────────────────────────────────────
IF NOT EXIST ".venv\Scripts\python.exe" (
    echo ^> Premier lancement : installation de l'environnement...
    python -m venv .venv
    .venv\Scripts\python -m pip install --upgrade pip --quiet
    .venv\Scripts\python -m pip install -r requirements.txt
) ELSE (
    echo OK  Environnement virtuel pret
    .venv\Scripts\python -m pip install -r requirements.txt --quiet
)

REM ── .env ─────────────────────────────────────────────────
IF NOT EXIST ".env" (
    copy .env.example .env >nul
    echo OK  Fichier .env cree
)

REM ── Ouvrir le navigateur apres 3 secondes ────────────────
start "" /b cmd /c "timeout /t 3 >nul && start http://localhost:8501"

REM ── Lancer l'app ─────────────────────────────────────────
echo.
echo ^> Lancement sur http://localhost:8501
echo    Fermez cette fenetre pour arreter l'application.
echo.
.venv\Scripts\python -m streamlit run app.py --server.headless true --browser.gatherUsageStats false
pause
