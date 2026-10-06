# Enterprise RAG Assistant

A browser-based document question-answering application built with FastAPI, LlamaIndex, Groq, Hugging Face models, and SQLite. Upload supported files, index their contents locally, ask questions over the full document collection, and browse saved conversation transcripts.

> **Implementation note:** The current frontend searches all indexed documents. The backend accepts an optional `file_name` filter, but the UI does not currently provide a document selector. SQLite restores visible chat transcripts; the LlamaIndex chat-engine memory itself is cached only in the running backend process.

## What It Does

The application ingests files from `backend/data/documents/`, splits their loaded content into sentence-aware nodes, creates embeddings, and persists a LlamaIndex `VectorStoreIndex` under `backend/data/storage/`. A question is processed through HyDE query transformation, vector plus BM25 retrieval fused using reciprocal-rank fusion, a sentence-transformer reranker, and Groq generation. A separate `mode="query"` backend path uses a router to choose document question-answering or summary generation.

FastAPI provides document, chat, and conversation endpoints. The plain HTML/CSS/JavaScript frontend calls those APIs. SQLite stores conversation titles, messages, source excerpts, and timestamps.

### Why These Components

- **RAG** supplies document excerpts to generation so the model can answer from the indexed collection instead of relying only on its trained knowledge.
- **LlamaIndex** provides document loading, node parsing, index persistence, retrievers, query engines, and chat engines used by this implementation.
- **FastAPI** exposes typed HTTP endpoints and serves request validation through Pydantic schemas.
- **Groq** hosts the configured LLM used for query transformation, routing, and answer generation.

## Features Present in the Code

- Upload `.pdf`, `.txt`, `.md`, `.csv`, and `.docx` files.
- List supported files present in the documents directory.
- Delete a document and rebuild the index from remaining files; deleting the last supported file clears index storage.
- Full-collection conversational questions through `ContextChatEngine` in the current UI.
- Optional backend document filter through `file_name` when calling chat/query functions directly.
- Vector and BM25 retrieval combined with `QueryFusionRetriever` in `reciprocal_rerank` mode.
- HyDE query transformation and `SentenceTransformerRerank` post-processing.
- Backend query mode with a `RouterQueryEngine` that selects document QA or document summary.
- Answers returned with source file names and source text excerpts.
- Persistent chat metadata, transcripts, rename/delete operations, and a first-message default title in SQLite.

**Not exposed by the current frontend:** a document selector, mode selector for router queries, and reset-chat action. The frontend sends `file_name: null` and omits `mode`, so Pydantic uses its default `chat` mode.

## Technology Stack

| Technology | Role in this project |
|---|---|
| Python (project virtual environment uses Python 3.11.9) | Backend implementation |
| FastAPI + Uvicorn | HTTP API and ASGI server |
| Pydantic | Chat request/response validation |
| LlamaIndex | Document loading, chunking integration, indexing, retrieval, query/chat engines |
| Groq LlamaIndex integration | Hosted LLM configured by `LLM_MODEL` |
| `BAAI/bge-small-en-v1.5` | Default Hugging Face embedding model |
| `BAAI/bge-reranker-base` | Default sentence-transformer reranker model |
| LlamaIndex default local storage | Persisted vector store, document store, index metadata under JSON files |
| SQLite | Persistent conversation and message records |
| HTML, CSS, JavaScript | Static browser frontend |

The project does **not** configure a separate hosted vector database. LlamaIndex uses its default local storage context. `requirements.txt` also includes reader-related packages such as `pypdf`, `docx2txt`, and `pandas`.

## Architecture

```text
Browser user
    │
    ├── static HTML/CSS layout
    └── frontend/app.js ───────────────┐
                                       │ HTTP / JSON or multipart
                                       ▼
                                FastAPI app.main:app
                                       │
                  ┌────────────────────┼────────────────────┐
                  ▼                    ▼                    ▼
          api/documents.py       api/chat.py      api/conversations.py
                  │                    │                    │
         services/ingestion.py  services/rag.py   services/chat_history.py
                  │                    │                    │
                  ▼                    ├── local VectorStoreIndex
        data/documents/                ├── vector + BM25 fusion   SQLite
                                       ├── HyDE + reranker       chats/messages
                                       ├── Groq LLM
                                       └── response + sources
                  └────────────────────┴────────────────────┘
                                       ▼
                                frontend/app.js
```

- `backend/app/main.py` creates the FastAPI app, initializes SQLite during lifespan startup, configures CORS, and includes API routers.
- `backend/app/api/` maps HTTP operations to services.
- `backend/app/services/ingestion.py` converts files into nodes and persists an index.
- `backend/app/services/rag.py` loads the index and implements the retrieval and generation paths.
- `backend/app/services/chat_history.py` handles SQLite reads/writes.
- `frontend/` renders the chat, document list, uploads, and conversation controls.

## Project Structure

```text
project/
├── .gitignore
├── PROJECT_ARCHITECTURE.md          # Existing architecture notes; not this README's source of truth
├── README.md
├── notes.md
├── backend/
│   ├── .env                         # Local secrets/configuration; do not commit
│   ├── requirements.txt
│   ├── venv/                        # Local environment; ignored by git
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── api/
│   │   │   ├── chat.py
│   │   │   ├── conversations.py
│   │   │   └── documents.py
│   │   ├── schemas/
│   │   │   └── chat.py
│   │   ├── services/
│   │   │   ├── chat_history.py
│   │   │   ├── ingestion.py
│   │   │   └── rag.py
│   │   ├── ingestion/               # Present but empty
│   │   ├── rag/                     # Present but empty
│   │   └── retrieval/               # Present but empty
│   ├── data/
│   │   ├── chat_history.db
│   │   ├── documents/               # Current sample files are local data
│   │   └── storage/                 # Generated LlamaIndex JSON storage
│   └── tests/                       # Present but contains no test modules
└── frontend/
    ├── index.html
    ├── style.css
    └── app.js
```

### Important Files

| File | Receives / called by | Work and result |
|---|---|---|
| `backend/app/main.py` | Uvicorn imports `app` | Initializes SQLite at startup, registers routers, serves health routes |
| `backend/app/config.py` | Imported by backend modules | Loads `.env`, establishes paths and model/chunk/retrieval settings, checks `GROQ_API_KEY` |
| `backend/app/api/documents.py` | Frontend HTTP calls | Lists/uploads/deletes files; calls ingestion and index reset; returns JSON |
| `backend/app/api/chat.py` | `POST /api/chat` | Validates input, persists user/assistant messages, calls `services/rag.py`, returns answer/sources |
| `backend/app/api/conversations.py` | Frontend HTTP calls | Creates, lists, loads, renames, and deletes conversations |
| `backend/app/schemas/chat.py` | Chat endpoint | Defines `ChatRequest`, `Source`, and `ChatResponse` |
| `backend/app/services/ingestion.py` | Upload/delete API | Reads supported files, parses nodes, creates embeddings/index, stages replacement of persisted index files |
| `backend/app/services/rag.py` | Chat API | Loads index; builds retrieval/query/chat engines; returns answer and source dictionaries |
| `backend/app/services/chat_history.py` | Chat/conversation APIs | Creates SQLite schema and manages chats/messages/source JSON |
| `frontend/index.html` | Browser | Defines sidebar, document upload/list, conversation area, message form |
| `frontend/app.js` | Browser events | Calls APIs, manages active chat id, renders messages and source excerpts |
| `frontend/style.css` | HTML | Defines layout, lists, controls, messages, and mobile styles |

The empty `app/ingestion`, `app/rag`, and `app/retrieval` folders are not active implementation locations; corresponding code currently lives under `app/services/`.

## Application Flows

### Upload a Document

```text
Select a file in frontend/index.html
    ↓
frontend/app.js validates the extension and sends multipart/form-data
    ↓
POST /api/documents/upload → api/documents.py
    ↓
Save under backend/data/documents/<basename>
    ↓
ingest_documents() → SimpleDirectoryReader(recursive=True)
    ↓
LlamaIndex Document objects → SentenceSplitter nodes
    ↓
VectorStoreIndex creates embeddings using Settings.embed_model
    ↓
Persist into a temporary staging directory, replace data/storage/
    ↓
reset_index() clears cached RAG index/chat engines
    ↓
Return JSON; frontend reloads GET /api/documents
```

Supported extensions checked by the upload route and ingestion empty-directory check are `.pdf`, `.txt`, `.md`, `.csv`, and `.docx`. Upload stores only the basename in the documents directory, so same-named uploads overwrite the existing file.

### Ask a Question

The current browser submits `message`, `session_id`, and `file_name: null`; it omits `mode`, which defaults to `chat`.

```text
frontend/app.js → POST /api/chat
    ↓
ChatRequest validation in backend/app/schemas/chat.py
    ↓
api/chat.py creates/updates chat title and saves user message in SQLite
    ↓
services/rag.py: chat_question() → get_chat_engine()
    ↓
load persistent VectorStoreIndex if not already cached
    ↓
optional metadata filter (none in current UI)
    ↓
VectorIndexRetriever + BM25Retriever
    ↓
QueryFusionRetriever (reciprocal-rank fusion) inside TransformRetriever + HyDE
    ↓
SentenceTransformerRerank
    ↓
ContextChatEngine + Groq
    ↓
answer and response.source_nodes converted to {file_name, text}
    ↓
api/chat.py saves assistant message and sources in SQLite
    ↓
frontend renders answer/sources and refreshes conversation titles
```

The API can also accept `mode: "query"`. In that mode `ask_question()` builds a `RouterQueryEngine` with a document QA query engine and a summary query engine. The LLM selector chooses a tool based on tool descriptions. The current UI does not expose this mode.

### Conversation History

- `POST /api/conversations` generates a UUID chat id and inserts a `New Chat` row.
- The first chat message replaces that title with up to 50 characters from the first line, if it is still `New Chat` and has no prior messages.
- Each user and assistant message is stored in SQLite; source arrays are JSON strings.
- `GET /api/conversations` returns title and timestamps; `GET /api/conversations/{chat_id}` returns stored messages.
- On page load, the frontend loads conversation summaries. It does not automatically open the previous chat; selecting one fetches and renders its transcript.
- Transcript persistence and LlamaIndex conversational memory are separate. `_chat_engines` is a Python process cache; the backend does not convert saved SQLite messages into LlamaIndex chat history after restart.

## API Reference

All routes are registered by `backend/app/main.py`. The browser's `API_BASE_URL` is hard-coded to `http://127.0.0.1:8000`.

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/` | Root service message |
| `GET` | `/health` | Health status |
| `GET` | `/api/documents` | List supported files |
| `POST` | `/api/documents/upload` | Upload and index a document (multipart field `file`) |
| `DELETE` | `/api/documents?path=...` | Delete a relative document path and rebuild index |
| `POST` | `/api/chat` | Answer a question and save conversation messages |
| `POST` | `/api/chat/reset` | Clear the in-memory LlamaIndex engine cache for a session |
| `GET` | `/api/conversations` | List conversations |
| `POST` | `/api/conversations` | Create a conversation |
| `GET` | `/api/conversations/{chat_id}` | Read metadata and messages |
| `PATCH` | `/api/conversations/{chat_id}` | Rename a conversation with JSON `{"title":"..."}` |
| `DELETE` | `/api/conversations/{chat_id}` | Delete chat and messages |

### Chat request

```json
{
  "message": "What is the remote work policy?",
  "session_id": "a-client-generated-chat-id",
  "file_name": null,
  "mode": "chat"
}
```

`file_name` is optional. `mode` is `chat` or `query` and defaults to `chat`. The response shape is:

```json
{
  "answer": "Answer generated from the retrieved context.",
  "sources": [
    {"file_name": "handbook.pdf", "text": "Retrieved node text..."}
  ]
}
```

### Document list response

```json
{
  "count": 1,
  "documents": [
    {"file_name": "handbook.pdf", "path": "handbook.pdf", "size": 1234, "extension": ".pdf"}
  ]
}
```

### Conversation responses

`POST /api/conversations` returns `{"chat_id":"<uuid>","title":"New Chat"}`. `GET /api/conversations` wraps records in `{"conversations":[...]}`. `GET /api/conversations/{chat_id}` returns `{"conversation":{...},"messages":[...]}`. A message includes `role`, `content`, `sources`, and `created_at`.

### Errors visible in code

- Chat rejects blank messages with HTTP 400.
- Upload rejects missing names and unsupported extensions with HTTP 400.
- Document deletion rejects paths outside the document root with HTTP 400 and missing/unsupported files with HTTP 404.
- Conversation read/rename/delete return HTTP 404 for unknown chat ids; rename returns HTTP 400 for an empty title.
- Exceptions inside upload, delete/reindex, and chat handling are returned as HTTP 500 details. The exception message is passed through.
- Missing `GROQ_API_KEY` raises `ValueError` during configuration import/startup.

## Storage

### Documents and index

- Original source files live in `backend/data/documents/`.
- `VectorStoreIndex` persists through LlamaIndex's default local storage context under `backend/data/storage/`. Current generated filenames include `docstore.json`, `index_store.json`, `default__vector_store.json`, `image__vector_store.json`, and `graph_store.json`.
- `get_index()` loads persisted state using `StorageContext.from_defaults(persist_dir=...)` and `load_index_from_storage()` on demand; a module-level `_index` caches it for the process.
- Ingestion creates a new index in a temporary directory and replaces the storage directory after persistence succeeds. Deleting the final supported document removes storage.
- These are local runtime data. The root `.gitignore` has `data/storage/*` and `data/documents/*` patterns, but they are rooted at repository-level `data/` and do not match `backend/data/`; backend data may therefore appear in Git status.

### SQLite conversations

`backend/data/chat_history.db` is initialized at FastAPI startup. `services/chat_history.py` creates:

- `chats`: `id` (text primary key), `title`, `created_at`, `updated_at`.
- `messages`: autoincrement `id`, `chat_id`, `role`, `content`, `sources` (JSON text), `created_at`.

There is a declared `messages.chat_id` foreign key to `chats.id`, but connection setup does not explicitly enable SQLite foreign-key enforcement. Chat deletion also explicitly deletes messages before the chat. Messages are ordered by row id when restored; chat list is ordered by `updated_at` descending.

## Configuration

Create `backend/.env` locally; never commit a real key. `backend/app/config.py` loads it with `python-dotenv`.

```dotenv
GROQ_API_KEY=your_key_here
LLM_MODEL=openai/gpt-oss-120b
EMBEDDING_MODEL=BAAI/bge-small-en-v1.5
RERANKER_MODEL=BAAI/bge-reranker-base
CHUNK_SIZE=512
CHUNK_OVERLAP=50
SIMILARITY_TOP_K=5
HYBRID_TOP_K=10
RERANK_TOP_N=5
```

| Variable | Default | Meaning / current use |
|---|---|---|
| `GROQ_API_KEY` | Required | Groq authentication; no secret value is documented here |
| `LLM_MODEL` | `openai/gpt-oss-120b` | Model passed to the LlamaIndex Groq integration |
| `EMBEDDING_MODEL` | `BAAI/bge-small-en-v1.5` | Hugging Face embeddings used for index/query vectors |
| `RERANKER_MODEL` | `BAAI/bge-reranker-base` | Model used by `SentenceTransformerRerank` |
| `CHUNK_SIZE` | `512` | `SentenceSplitter` chunk size |
| `CHUNK_OVERLAP` | `50` | `SentenceSplitter` overlap |
| `SIMILARITY_TOP_K` | `5` | Present in config and imported by `rag.py`, but currently unused there |
| `HYBRID_TOP_K` | `10` | Candidate count used by vector, BM25, and fusion retrievers |
| `RERANK_TOP_N` | `5` | Number of nodes retained by the reranker |

The embedding and reranker models are downloaded/loaded locally through Hugging Face packages and can require network access on first use. The LLM calls require network access to Groq.

## Installation and Running

The existing project has a local `backend/venv` (ignored by git); a fresh checkout needs its own environment. Python 3.11 is a known project environment version.

### 1. Configure the backend

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Create `backend/.env` with `GROQ_API_KEY=your_key_here`. The app creates the data directories in `config.py` and initializes the SQLite schema during startup. There is no separate migration or index-build command. Upload at least one supported document before asking a question; upload triggers indexing.

### 2. Start the backend

From `backend/`:

```bash
source venv/bin/activate
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Health check: `http://127.0.0.1:8000/health`. Interactive FastAPI docs are available at `/docs` through FastAPI's defaults.

### 3. Start the frontend

Open a second terminal:

```bash
cd frontend
python3 -m http.server 5500
```

Open `http://127.0.0.1:5500`. The frontend API origin is fixed to `http://127.0.0.1:8000`; changing backend host/port requires changing `frontend/app.js`.

No Dockerfile, compose file, frontend package manager, or automated test suite is present in the inspected project tree.

## Example Usage

1. Start the backend, then the static frontend.
2. Use **Upload Document** to choose a PDF, text, Markdown, CSV, or DOCX file. Wait for ingestion to complete.
3. Ask a question in the message box. The browser currently searches all indexed documents.
4. Read the answer and inspect the displayed retrieved source file names and excerpts.
5. Use **New Chat** to create a distinct chat id. The first prompt becomes its default title.
6. Select a conversation in the sidebar to reload its saved transcript; use its rename or trash controls to manage it.
7. Use the document trash control to remove a source file and rebuild the index.

There is no current UI action for selecting one document or switching to `mode="query"`. Those behaviors are available only to API callers that supply the appropriate request fields.

## Limitations and Future Improvements

### Current implementation limitations

- Saved conversation transcripts are restored for display, but saved messages are not hydrated into a new `ContextChatEngine` after backend restart. A reopened chat's in-memory context can therefore differ from its displayed transcript.
- The frontend always searches all documents; backend `file_name` filtering has no visible selector.
- The frontend omits `mode`, so Router Query Engine mode is not accessible through the UI.
- Uploads write to the basename directly; uploading another file with the same basename replaces the prior source.
- Source-excerpt cleanup matches `file_name` by basename, so manually maintained nested files with duplicate basenames are not distinguishable in saved citations.
- Upload errors are returned, but an upload that is saved and then fails ingestion is not rolled back from the documents directory.
- Deletion removes the source before rebuilding. If rebuilding fails, the route clears index storage and returns HTTP 500; there is then no usable index until successful re-ingestion.
- CORS allows every origin and credentials; this is permissive and should be restricted before deployment.
- No authentication, authorization, user separation, upload size limit, structured logging, or automated tests are present.
- Root `.gitignore` data-path patterns do not match `backend/data/`, so local document/index/database artifacts can appear in repository status.
- `SIMILARITY_TOP_K` is not used by the current retrieval implementation; `HYBRID_TOP_K` controls the retrieved candidate counts.
- On screens at or below 768px, CSS hides the entire sidebar, including upload/document and conversation controls.

### Possible future improvements (not implemented)

Add a UI document filter and query-mode switch; restore chat memory from SQLite messages; make uploads/rebuilds transactional or background jobs; add authentication and per-user data access; restrict CORS; introduce upload size/content validation; use structured logging and RAG evaluation; add automated API/index tests; consider a production vector database and database migrations when scale requires them.

## Interview and Presentation Summary

> This is a document-grounded question-answering application. FastAPI exposes APIs for uploads, chat, and conversation management. LlamaIndex loads documents, splits them into nodes, embeds them, and persists a local vector index. At question time, a HyDE transform feeds vector and BM25 retrievers whose results are fused and reranked before Groq generates an answer. The response includes source excerpts. SQLite stores conversation titles, messages, timestamps, and sources. One important design distinction is that the transcript is persistent but the ContextChatEngine cache is process-local, so history reconstruction after restart remains an improvement area.

Useful design choices to explain: layered API/service/schema organization; local persistence for a compact learning project; combining semantic and lexical retrieval; reranking retrieved candidates; keeping source excerpts with transcript messages. Be candid that the browser currently uses chat mode across all documents, while the router and document filter are backend-level capabilities.
