"""
Diagnostic script — run before launching the app.

Usage:
    python scripts/check_setup.py
    python scripts/check_setup.py --provider ollama --model llama3
"""
import argparse
import importlib
import sys
from pathlib import Path

# Make src/ importable
sys.path.insert(0, str(Path(__file__).parent.parent))


# ---------------------------------------------------------------------------
# Colours (no external dependency)
# ---------------------------------------------------------------------------
def _green(s): return f"\033[92m{s}\033[0m"
def _red(s):   return f"\033[91m{s}\033[0m"
def _yellow(s): return f"\033[93m{s}\033[0m"
def _bold(s):  return f"\033[1m{s}\033[0m"

OK   = _green("  ✓")
FAIL = _red("  ✗")
WARN = _yellow("  !")


# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------

def check_python_version() -> bool:
    major, minor = sys.version_info[:2]
    ok = (major, minor) >= (3, 10)
    label = f"Python {major}.{minor}"
    print(f"{OK if ok else FAIL}  {label}" + ("" if ok else " — Python 3.10+ requis"))
    return ok


def check_package(package: str, install_hint: str = "") -> bool:
    try:
        importlib.import_module(package)
        print(f"{OK}  {package}")
        return True
    except ImportError:
        hint = f" → pip install {install_hint or package}"
        print(f"{FAIL}  {package}{hint}")
        return False


def check_documents_dir() -> bool:
    docs_dir = Path(__file__).parent.parent / "documents"
    if not docs_dir.exists():
        print(f"{FAIL}  Dossier /documents absent")
        return False
    files = [f for f in docs_dir.rglob("*") if f.is_file()
             and f.suffix.lower() in (".pdf", ".docx", ".txt", ".md")]
    if not files:
        print(f"{WARN}  /documents existe mais aucun document supporté trouvé")
        print("       Ajoutez des fichiers PDF, DOCX, TXT ou Markdown.")
        return False
    print(f"{OK}  /documents → {len(files)} fichier(s) trouvé(s)")
    return True


def check_env_file() -> bool:
    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        print(f"{OK}  Fichier .env présent")
        return True
    print(f"{WARN}  Fichier .env absent")
    print("       Lancez : cp .env.example .env  puis éditez-le.")
    return False


def check_embedding_model(model_name: str = "all-MiniLM-L6-v2") -> bool:
    try:
        from sentence_transformers import SentenceTransformer
        print(f"     Téléchargement/chargement du modèle d'embedding '{model_name}'…")
        SentenceTransformer(model_name)
        print(f"{OK}  Modèle d'embedding '{model_name}' disponible")
        return True
    except Exception as exc:
        print(f"{FAIL}  Modèle d'embedding indisponible : {exc}")
        print(f"       Vérifiez votre connexion internet pour le premier téléchargement.")
        return False


def check_ollama(model: str, base_url: str = "http://localhost:11434") -> bool:
    import requests
    try:
        resp = requests.get(f"{base_url}/api/tags", timeout=5)
        resp.raise_for_status()
        models = [m["name"] for m in resp.json().get("models", [])]
        print(f"{OK}  Ollama tourne sur {base_url}")

        # Check if the requested model is pulled
        model_base = model.split(":")[0]
        matched = [m for m in models if m.split(":")[0] == model_base]
        if matched:
            print(f"{OK}  Modèle '{model}' disponible dans Ollama")
            return True
        else:
            print(f"{WARN}  Modèle '{model}' non trouvé dans Ollama")
            print(f"       Lancez : ollama pull {model}")
            if models:
                print(f"       Modèles disponibles : {', '.join(models)}")
            return False
    except requests.exceptions.ConnectionError:
        print(f"{FAIL}  Ollama ne répond pas sur {base_url}")
        print("       Lancez : ollama serve")
        return False
    except Exception as exc:
        print(f"{FAIL}  Ollama — erreur inattendue : {exc}")
        return False


def check_lmstudio(base_url: str = "http://localhost:1234/v1") -> bool:
    import requests
    try:
        resp = requests.get(f"{base_url}/models", timeout=5)
        resp.raise_for_status()
        models = resp.json().get("data", [])
        print(f"{OK}  LM Studio tourne sur {base_url}")
        if models:
            print(f"       Modèle chargé : {models[0].get('id', '?')}")
        else:
            print(f"{WARN}  LM Studio répond mais aucun modèle n'est chargé")
        return True
    except requests.exceptions.ConnectionError:
        print(f"{FAIL}  LM Studio ne répond pas sur {base_url}")
        print("       Ouvrez LM Studio, chargez un modèle et démarrez le serveur local.")
        return False
    except Exception as exc:
        print(f"{FAIL}  LM Studio — erreur : {exc}")
        return False


def check_cloud_provider(provider: str) -> bool:
    from dotenv import load_dotenv
    import os
    load_dotenv()

    key_map = {
        "openai": ("OPENAI_API_KEY", "openai"),
        "claude": ("ANTHROPIC_API_KEY", "anthropic"),
        "mistral": ("MISTRAL_API_KEY", "mistralai"),
    }
    env_var, pkg = key_map.get(provider, (None, None))
    if not env_var:
        return False

    key = os.getenv(env_var, "")
    if not key or key.startswith("sk-...") or key == "...":
        print(f"{FAIL}  {env_var} non définie dans .env")
        return False

    try:
        importlib.import_module(pkg)
        print(f"{OK}  {provider} — clé API présente et SDK installé")
        return True
    except ImportError:
        print(f"{FAIL}  SDK '{pkg}' non installé → pip install {pkg}")
        return False


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Vérification de l'installation HR RAG Chatbot")
    parser.add_argument("--provider", default=None, help="Fournisseur IA à tester (ollama, lmstudio, openai, claude, mistral)")
    parser.add_argument("--model", default=None, help="Nom du modèle")
    args = parser.parse_args()

    # Load config to get defaults
    try:
        from dotenv import load_dotenv
        load_dotenv()
        import os
        provider = args.provider or os.getenv("AI_PROVIDER", "ollama")
        model = args.model or os.getenv("MODEL_NAME", "llama3")
        embedding_model = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
        ollama_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        lmstudio_url = os.getenv("LMSTUDIO_BASE_URL", "http://localhost:1234/v1")
    except Exception:
        provider, model, embedding_model = "ollama", "llama3", "all-MiniLM-L6-v2"
        ollama_url, lmstudio_url = "http://localhost:11434", "http://localhost:1234/v1"

    print()
    print(_bold("=" * 55))
    print(_bold("  Diagnostic — Local HR RAG Chatbot"))
    print(_bold("=" * 55))

    all_ok = True

    # --- Environnement Python ---
    print(f"\n{_bold('[ Environnement Python ]')}")
    all_ok &= check_python_version()

    CORE_PACKAGES = [
        ("chromadb", "chromadb"),
        ("sentence_transformers", "sentence-transformers"),
        ("streamlit", "streamlit"),
        ("dotenv", "python-dotenv"),
        ("requests", "requests"),
        ("pymupdf", "pymupdf"),
        ("docx", "python-docx"),
    ]
    for pkg, install in CORE_PACKAGES:
        all_ok &= check_package(pkg, install)

    # --- Fichiers projet ---
    print(f"\n{_bold('[ Fichiers projet ]')}")
    check_env_file()
    all_ok &= check_documents_dir()

    # --- Modèle d'embedding ---
    print(f"\n{_bold('[ Modèle d\'embedding ]')}")
    all_ok &= check_embedding_model(embedding_model)

    # --- Fournisseur IA ---
    print(f"\n{_bold(f'[ Fournisseur IA : {provider} / {model} ]')}")
    if provider == "ollama":
        all_ok &= check_ollama(model, ollama_url)
    elif provider == "lmstudio":
        all_ok &= check_lmstudio(lmstudio_url)
    elif provider in ("openai", "claude", "mistral"):
        all_ok &= check_cloud_provider(provider)
    else:
        print(f"{WARN}  Fournisseur inconnu : {provider}")

    # --- Résumé ---
    print()
    print(_bold("=" * 55))
    if all_ok:
        print(_green(_bold("  Tout est prêt ! Lancez : streamlit run app.py")))
    else:
        print(_yellow(_bold("  Des problèmes ont été détectés. Corrigez-les ci-dessus.")))
    print(_bold("=" * 55))
    print()

    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
