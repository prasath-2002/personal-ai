# Personal AI

A local, single-user assistant with a FastAPI backend, Next.js chat interface, SQLite conversation storage and document retrieval.

## Available features

- Streaming conversations using `mock`, OpenAI or Groq; Tamil, English and Tanglish prompts.
- Saved conversations, rename/delete, mobile chat selection and restoring the last selected chat.
- Markdown chat export and clearing messages while retaining attachments.
- PDF/TXT uploads, duplicate detection, a configurable 10 MB default limit, per-chat document search and deletion.
- Local semantic embeddings using `sentence-transformers/all-MiniLM-L6-v2`.
- Structured streaming errors and retries. Only completed user/assistant turns are stored atomically.
- Provider status, connection settings, database health check, regression tests and GitHub Actions checks.
- Docker Compose with persistent database and embedding-cache volumes.

## Run locally (PowerShell)

Use Python 3.14 and Node.js 22 or later. Existing `.env` files should be kept; copy the examples only for a fresh setup.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

In a second terminal:

```powershell
cd frontend
npm ci
Copy-Item .env.example .env.local
npm run dev
```

Open http://localhost:3000. API documentation is at http://localhost:8000/docs.
The frontend defaults to `http://localhost:8000` if `NEXT_PUBLIC_API_URL` is absent.

`LLM_PROVIDER=mock` is an offline integration demo, not a real AI model. For real responses, set `LLM_PROVIDER` to `groq` or `openai`, and supply that provider's API key and model ID in the backend `.env`. Restart the backend after changes. API keys are never sent to the frontend. The settings panel reports configuration presence, not provider credential validity.

## Document questions

Attach a PDF or UTF-8 TXT file, then ask a question in that chat. The first document operation may download the embedding model; subsequent operations use its local cache. Scanned/image-only PDFs require OCR before upload. The current embedding model works best with English documents; retrieval quality for Tamil requires a multilingual embedding model and reindexing in a future update.

Extracted text and vectors persist in SQLite. New upload originals are temporary and removed after processing. Old files already present under `data/uploads` are not automatically removed. Removing an attachment deletes its stored text and vectors; deleting a conversation also deletes its messages and attachments.

Chat requests with a real provider send recent history and relevant document excerpts to that provider. Storage is local, but inference is external. This app has no user authentication and is intended for localhost use. Public hosting needs authentication and HTTPS first.

## Tests and build

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
cd frontend
npm run lint
npm run build
```

Backend tests use temporary databases, mock chat responses and deterministic embedding substitutes; they make no provider requests or model downloads. For CI-only installs, `requirements-test.txt` omits the large local inference stack. The full runtime dependency snapshot remains in `requirements.txt`.

`/chat/stream` returns SSE frames containing JSON with `type: delta`, `type: done` or `type: error`. Clients must require `done` before treating a turn as complete. A connection loss after server persistence can still make a retry ambiguous; there is no request-id deduplication yet.

## Docker

With Docker installed and a backend `.env` present:

```powershell
docker compose up --build
```

Open http://localhost:3000. Both ports bind to loopback. Container storage uses the `personal-ai-data` named volume, separate from the local `data` folder. The embedding model cache has its own named volume. `docker compose down` preserves both; `down -v` removes them. The frontend API URL is set at build time.

## Configuration

| Variable | Default / purpose |
| --- | --- |
| `LLM_PROVIDER` | `mock`; choose `mock`, `openai`, `groq` |
| `OPENAI_API_KEY`, `OPENAI_MODEL` | Required for OpenAI |
| `GROQ_API_KEY`, `GROQ_MODEL` | Required for Groq |
| `DATA_DIR` | Project `data` directory |
| `MAX_UPLOAD_MB` | `10` |
| `CORS_ORIGINS` | localhost and 127.0.0.1 on port 3000 |
| `NEXT_PUBLIC_API_URL` | Browser-accessible backend URL |

The existing database schema is migrated on startup without clearing saved chats.

## Future work

Cross-chat user preference memory, an explicit tool/agent system, multilingual embedding migration, request-id deduplication, authentication, production monitoring and cloud deployment remain future work. CI checks are included; no cloud deployment or paid resources are provisioned.
