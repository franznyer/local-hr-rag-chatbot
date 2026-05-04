# Local HR RAG Chatbot 💼

> A fully local, privacy-first HR chatbot powered by Retrieval-Augmented Generation (RAG).  
> Ask questions about your HR documents — answers are grounded exclusively in your files.

---

## Overview

**Local HR RAG Chatbot** is a production-grade RAG application that lets HR teams (or any employee) query internal HR documents through a conversational interface — without sending a single byte of data to a third-party server.

| Feature | Detail |
|---|---|
| 100% local mode | Ollama or LM Studio — no internet required |
| Document support | PDF, DOCX, TXT, Markdown |
| Embeddings | `sentence-transformers` (local) |
| Vector database | ChromaDB (persisted on disk) |
| UI | Streamlit |
| AI providers | OpenAI, Claude, Mistral, Ollama, LM Studio |
| Anti-hallucination | Strict prompt — refuses to answer if information is absent |

---

## Architecture

```
local-hr-rag-chatbot/
│
├── app.py                    # Streamlit UI + entry point
├── requirements.txt
├── .env.example
│
├── documents/                # Drop your HR documents here
├── vectorstore/              # ChromaDB persisted index (auto-created)
│
└── src/
    ├── config.py             # Centralised configuration (env vars)
    ├── document_loader.py    # PDF / DOCX / TXT / MD ingestion
    ├── text_splitter.py      # Overlapping chunking
    ├── embeddings.py         # sentence-transformers wrapper
    ├── vector_store.py       # ChromaDB CRUD + similarity search
    ├── rag_pipeline.py       # Full RAG orchestration
    ├── prompts.py            # Strict HR prompt templates
    │
    └── providers/
        ├── base.py           # Abstract BaseProvider interface
        ├── openai_provider.py
        ├── claude_provider.py
        ├── mistral_provider.py
        ├── ollama_provider.py
        └── lmstudio_provider.py
```

---

## Quick Start

### Prerequisites

- Python 3.10+
- (For local mode) [Ollama](https://ollama.ai) or [LM Studio](https://lmstudio.ai) running locally

### 1 — Clone and install

```bash
git clone https://github.com/franznyer/local-hr-rag-chatbot.git
cd local-hr-rag-chatbot
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2 — Configure

```bash
cp .env.example .env
# Edit .env — at minimum set AI_PROVIDER and MODEL_NAME
```

### 3 — Add your documents

Drop PDF, DOCX, TXT or Markdown files into the `documents/` folder.  
Sample HR documents (French) are already included to let you test immediately.

### 4 — Launch

```bash
streamlit run app.py
```

The app opens at `http://localhost:8501`.  
Documents are indexed automatically on first launch.

---

## Supported AI Providers

| Provider | Mode | Requirement |
|---|---|---|
| **Ollama** | 100% local | `ollama serve` + model pulled |
| **LM Studio** | 100% local | LM Studio server running |
| **OpenAI** | Cloud | `OPENAI_API_KEY` in `.env` |
| **Claude** | Cloud | `ANTHROPIC_API_KEY` in `.env` |
| **Mistral** | Cloud | `MISTRAL_API_KEY` in `.env` |

### Using Ollama (recommended for privacy)

```bash
# Install Ollama: https://ollama.ai
ollama pull llama3          # or mistral, phi3, gemma2, etc.
ollama serve
```

Set in `.env`:
```
AI_PROVIDER=ollama
MODEL_NAME=llama3
```

### Using LM Studio

1. Download and open [LM Studio](https://lmstudio.ai)
2. Load any GGUF model
3. Start the local server (default port: 1234)

Set in `.env`:
```
AI_PROVIDER=lmstudio
MODEL_NAME=lmstudio-community/Meta-Llama-3-8B-Instruct-GGUF
```

---

## Configuration Reference

All settings are controlled via `.env`:

| Variable | Default | Description |
|---|---|---|
| `AI_PROVIDER` | `ollama` | Active provider |
| `MODEL_NAME` | `llama3` | Model identifier |
| `EMBEDDING_MODEL` | `all-MiniLM-L6-v2` | Local embedding model |
| `CHUNK_SIZE` | `512` | Words per chunk |
| `CHUNK_OVERLAP` | `64` | Overlap between chunks |
| `TOP_K_RESULTS` | `4` | Chunks retrieved per query |
| `MIN_RELEVANCE_SCORE` | `0.3` | Minimum cosine similarity |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama endpoint |
| `LMSTUDIO_BASE_URL` | `http://localhost:1234/v1` | LM Studio endpoint |

---

## RAG Pipeline

```
User question
     │
     ▼
Embed query (sentence-transformers, local)
     │
     ▼
Similarity search (ChromaDB, cosine)
     │
     ▼
Top-K chunks retrieved
     │
     ▼
Build structured prompt (strict anti-hallucination template)
     │
     ▼
AI Provider (Ollama / OpenAI / Claude / Mistral / LM Studio)
     │
     ▼
Structured answer + cited sources + confidence score
```

### Anti-hallucination strategy

- The system prompt **forbids** the model from inventing information.
- If the answer is not found in the retrieved chunks, the model replies with a standard refusal message.
- Every factual statement must be followed by a source citation in parentheses.

---

## Adding a New Provider

1. Create `src/providers/my_provider.py`
2. Inherit from `BaseProvider` and implement `complete()` and `health_check()`
3. Register the new key in `src/rag_pipeline.py` → `_build_provider()`
4. Add the new option to the Streamlit sidebar in `app.py`

---

## Sample Documents (included)

The `documents/` folder contains realistic French HR documents for demo purposes:

| File | Content |
|---|---|
| `politique_conges.md` | Leave and absence policy |
| `reglement_interieur.md` | Company internal rules |
| `guide_onboarding.md` | New employee onboarding guide |
| `politique_teletravail.md` | Remote work policy |
| `grille_remuneration.md` | Salary grid and compensation policy |

---

## Roadmap

- [ ] PDF upload via UI
- [ ] Multi-language support
- [ ] LLM-based re-ranking
- [ ] Docker / Docker Compose packaging
- [ ] REST API layer for SaaS deployment

---

## License

MIT

---

*Built with Python · ChromaDB · sentence-transformers · Streamlit*
