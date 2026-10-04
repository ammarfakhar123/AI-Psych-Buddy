# AI Psych Buddy 💙

A 24/7 conversational **mental-wellness and self-reflection** web app built with Django and a real
**Retrieval-Augmented Generation (RAG)** pipeline.

> AI Psych Buddy is designed solely for wellness support and self-reflection. It does not replace
> professional medical advice, therapy, or emergency crisis care.

It does **not** diagnose, prescribe, or provide treatment. See [Safety limitations](#12-safety-limitations).

---

## 1. Project overview

Users can chat with a supportive AI companion ("Buddy"), track their mood, and try guided CBT-style
reflections, grounding and breathing exercises. The chatbot answers using a curated wellness
**knowledge base** (retrieved with embeddings + a vector database), personalised with the user's name
and recent mood check-ins, and protected by a **safety layer** that handles crisis messages.

## 2. Features

| Area | What it does |
|---|---|
| AI chat | Supportive replies from an LLM, grounded in retrieved wellness documents ("sources used" chips shown) |
| RAG | Chunking → Sentence-Transformers embeddings → ChromaDB → top-k retrieval with relevance threshold |
| Safety | Crisis/self-harm detection *before* the LLM, fixed calm crisis response, configurable resources, output screening |
| Prompt engineering | Role, boundaries, response format and context blocks in `apps/ai_assistant/prompts.py` |
| Personalisation | Name, focus areas and recent mood summary injected into the prompt |
| Mood tracker | Daily check-in, week/month Chart.js graph, history, neutral (non-clinical) wording |
| CBT reflection | 6-step guided exercise, stored per user, optional AI feedback |
| Grounding | Interactive 5-4-3-2-1 and other exercises (seeded automatically) |
| Breathing | Animated Inhale/Hold/Exhale timer with selectable patterns |
| Suggestions | Dashboard "AI Wellness Suggestions" from mood + latest conversation |
| Accounts | Register, login, logout, profile, change password; all data is private per user |
| History | Create, continue, view and delete conversations |

## 3. Technology stack

* **Backend:** Python, Django 5, Django REST Framework (chat endpoint)
* **Frontend:** HTML, CSS, JavaScript, Bootstrap 5, Bootstrap Icons, Chart.js (no React/Next/Flutter)
* **Database:** SQLite (dev), PostgreSQL-ready via `DATABASE_URL`
* **LLM:** any OpenAI-compatible API through the `openai` SDK (OpenAI, Groq, OpenRouter, Gemini's OpenAI endpoint, Ollama, ...)
* **RAG:** Sentence-Transformers (`all-MiniLM-L6-v2`) + ChromaDB (local, persistent)

## 4. Architecture

```
User message
   │
   ▼
Safety check (safety.py) ── high risk ──► fixed calm crisis response (LLM is never called)
   │ ok / elevated
   ▼
Query processing (retriever.process_query)
   ▼
Retriever (ChromaDB + embeddings) ──► relevant wellness chunks (only if close enough)
   ▼
Prompt = system prompt + user context (name, mood summary) + retrieved knowledge + chat history
   ▼
LLM (llm_client.py, env-configurable)
   ▼
Output screening (no diagnosis / medication / "I'm a human")
   ▼
Reply + sources + exercise suggestions → saved to the database
```

Key modules in `apps/ai_assistant/`:

* `prompts.py` – all prompt text
* `safety.py` – risk detection, crisis response, output screening
* `llm_client.py` – provider-agnostic wrapper with friendly error handling
* `rag/` – `chunking.py`, `embeddings.py`, `vector_store.py`, `ingest.py`, `retriever.py`
* `pipeline.py` – ties everything together (read this first to understand the flow)
* `suggestions.py` – rule-based exercise suggestions

## 5. Installation

Requires **Python 3.11–3.13** (sentence-transformers/torch may not yet support newer versions).

```bash
python -m venv venv
venv\Scripts\activate            # Windows   (macOS/Linux: source venv/bin/activate)
pip install -r requirements.txt
copy .env.example .env           # then edit .env (macOS/Linux: cp .env.example .env)
python manage.py migrate
python ingest_knowledge.py
python manage.py runserver
```

Open http://127.0.0.1:8000

## 6. Environment variables

Set in `.env` (never commit it). See `.env.example` for all options.

| Variable | Purpose |
|---|---|
| `DJANGO_SECRET_KEY` | Django secret (use a long random value) |
| `DJANGO_DEBUG` | `True` for development, `False` in production |
| `DATABASE_URL` | `sqlite:///db.sqlite3` or e.g. `postgres://user:pass@host:5432/db` |
| `LLM_API_KEY` | Your LLM provider key (**required for AI replies**) |
| `LLM_MODEL` | Model name, e.g. `gpt-4o-mini`, `llama-3.1-8b-instant`, `gemini-2.0-flash` |
| `LLM_BASE_URL` | Blank for OpenAI, otherwise the provider's OpenAI-compatible URL |
| `EMBEDDING_BACKEND` | `sentence-transformers` (default) or `hashing` (lightweight fallback) |
| `RAG_TOP_K`, `RAG_MAX_DISTANCE` | How many chunks to retrieve / how strict relevance is |
| `CRISIS_RESOURCES` | JSON list of crisis resources shown on high-risk messages |

To switch providers, change only `LLM_API_KEY`, `LLM_MODEL` and `LLM_BASE_URL`.

## 7. Database setup

```bash
python manage.py migrate
python manage.py createsuperuser   # optional, for /admin/
```

Migrations also seed the grounding exercises. For PostgreSQL: `pip install "psycopg[binary]"` and set
`DATABASE_URL`.

## 8. RAG setup

Embeddings are created locally. On first use `sentence-transformers` downloads the
`all-MiniLM-L6-v2` model (~90 MB, internet required once). If it can't be loaded, ingestion
automatically falls back to the lightweight `hashing` backend, and the retriever uses whichever backend
built the index.

## 9. Knowledge-base ingestion

Documents live in `knowledge_base/<category>/*.md` (categories: cbt, grounding, breathing,
stress_management, sleep, self_reflection). Add or edit files, then rebuild the index:

```bash
python ingest_knowledge.py                    # full rebuild
python ingest_knowledge.py --backend hashing  # no model download
```

The script reads documents, splits them into heading-aware chunks, embeds them, and stores text +
metadata (category, source, title, section) in ChromaDB under `vector_store/`.

The sample documents are **educational wellness resources** written for this demo. They contain no
citations or medical research claims. Review/replace them with vetted material for real use.

## 10. Running the project

```bash
python manage.py runserver
python manage.py test        # run the automated tests
```

Without an `LLM_API_KEY` the whole app works, and the chat shows: *"I'm having trouble connecting to the
AI service right now. Please try again in a moment."* Crisis messages still get the safe fixed response.

## 11. Project structure

```
config/                settings, root urls
apps/accounts/         auth + profile
apps/chat/             conversations, messages, chat API
apps/mood/             mood tracking + chart data
apps/exercises/        CBT, grounding, breathing
apps/dashboard/        landing + dashboard
apps/ai_assistant/     prompts, safety, LLM client, RAG, pipeline, tests
knowledge_base/        wellness documents
vector_store/          ChromaDB files (generated)
templates/  static/    HTML, CSS, JS
ingest_knowledge.py    build the vector index
```

## 12. Safety limitations

* Not a medical device. No diagnosis, medication advice, or treatment.
* Crisis detection is **keyword/pattern based** and can miss indirect language or flag harmless text.
  It is a first safety net, not a clinical tool.
* LLMs can make mistakes. Replies are screened for diagnosis/medication wording, but not perfectly.
* Crisis resources are generic by default: **configure `CRISIS_RESOURCES` for your country** before
  sharing the app.
* Chats are stored unencrypted in the database. Do not deploy publicly without a privacy review,
  HTTPS, and proper data-protection practices.

## Netlify secrets scanning

`RAG_MAX_DISTANCE` is a non-sensitive retrieval relevance threshold, not a credential.
Its numeric value can also occur in CSS and default configuration, causing false positives
when Netlify scans environment variable values. The repository's `netlify.toml` excludes
only this key using `SECRETS_SCAN_OMIT_KEYS`; scanning remains enabled for other secrets
and all repository and build-output files.

This exclusion preserves the configured retrieval behavior without changing the threshold
or exempting entire files. Existing build command and publish directory settings in the
Netlify UI remain unchanged. Redeploy after this configuration change is merged.

## 13. Future improvements

* ML-based risk classifier and human-review workflow
* Streaming responses, conversation summaries for long-term memory
* Hybrid retrieval (BM25 + vectors), re-ranking, admin UI for uploading documents
* Country-specific crisis resources by locale, multilingual support
* Email verification, rate limiting, PostgreSQL + Docker deployment
