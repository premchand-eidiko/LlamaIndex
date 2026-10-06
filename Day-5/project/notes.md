# Enterprise RAG Assistant — Technical Learning Notes

These notes describe the code that exists in this repository. They are a study guide, not a claim that every capability is exposed by the UI. In particular, document filtering and router-query mode exist in backend code, while the current browser sends `file_name: null` and omits `mode`.

## A. Project Mental Model

### What is this project?

In simple terms, this is a local web page where a user uploads documents and asks questions about their contents. The backend prepares an index from those files, finds relevant text when a question arrives, asks an LLM to answer using that retrieved text, and returns the answer with the source excerpts.

Technically, it is a static HTML/CSS/JavaScript frontend calling a FastAPI application. LlamaIndex performs document loading, node splitting, local index persistence, retrieval, query/chat engine orchestration, and source-node handling. Hugging Face models make embeddings and reranking scores; Groq serves the configured LLM. SQLite persists chat records and transcripts.

### Mental model

```text
Source files
    ↓
Read and split into nodes
    ↓
Create embeddings and local VectorStoreIndex
    ↓
Persist index files
    ↓
Question → transform (HyDE) → vector + BM25 retrieval
    ↓
Fuse candidates → rerank → provide context to Groq
    ↓
Answer + source node excerpts
```

| Mental-model stage | Actual implementation |
|---|---|
| Source files | `backend/data/documents/`; upload/list/delete routes in `backend/app/api/documents.py` |
| Read files | `SimpleDirectoryReader` in `backend/app/services/ingestion.py` |
| Split into nodes | `SentenceSplitter` and `splitter.get_nodes_from_documents()` in `services/ingestion.py` |
| Embeddings/index | `Settings.embed_model` and `VectorStoreIndex(nodes)` in `services/ingestion.py` |
| Persist/reload | `storage_context.persist()` in ingestion and `get_index()` in `services/rag.py` |
| Retrieval | `build_hybrid_retriever()` and `build_transformed_retriever()` in `services/rag.py` |
| Rerank/context/generation | `build_reranker()`, `RetrieverQueryEngine`, and `ContextChatEngine` in `services/rag.py` |
| History | `backend/data/chat_history.db`, accessed through `services/chat_history.py` |
| Browser | `frontend/index.html`, `frontend/app.js`, and `frontend/style.css` |

Important distinction: persisted SQLite messages are used to render old transcript turns, but the backend does not rebuild a new LlamaIndex `ContextChatEngine` from those turns after a process restart.

## B. Complete Project Structure

```text
project/
├── .gitignore
├── PROJECT_ARCHITECTURE.md
├── README.md                       # Generated repository guide
├── notes.md                        # This learning guide
├── backend/
│   ├── .env                        # Local settings/secrets; value not documented
│   ├── requirements.txt
│   ├── venv/                       # Local Python environment; ignored
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
│   │   ├── ingestion/              # Empty directory in current tree
│   │   ├── rag/                    # Empty directory in current tree
│   │   └── retrieval/              # Empty directory in current tree
│   ├── data/
│   │   ├── chat_history.db
│   │   ├── documents/
│   │   │   ├── finance_sample.txt
│   │   │   └── security_operations.txt
│   │   └── storage/                 # Generated LlamaIndex JSON files
│   │       ├── default__vector_store.json
│   │       ├── docstore.json
│   │       ├── graph_store.json
│   │       ├── image__vector_store.json
│   │       └── index_store.json
│   └── tests/                       # Directory present; no test modules found
└── frontend/
    ├── app.js
    ├── index.html
    └── style.css
```

`backend/app/ingestion`, `backend/app/rag`, and `backend/app/retrieval` are empty directories. The executable implementations with those concepts in their names live in `backend/app/services/`. The root `.gitignore` excludes `.env`, `venv/`, and Python bytecode. Its `data/storage/*` and `data/documents/*` rules point at repository-root `data/`, not `backend/data/`, so they do not ignore the current backend artifacts. This mismatch is visible in Git status and is an existing issue; it is not changed by this documentation task.

### `main.py`

#### Purpose
Creates the FastAPI application entry point and connects routes.

#### Called By
Uvicorn imports `app.main` and retrieves the module variable `app`.

#### Receives
ASGI startup/shutdown lifecycle events and HTTP requests that match its registered routes.

#### Internal Processing
1. Imports chat, conversation, and document routers.
2. Defines an async lifespan context that calls `initialize_database()` at startup.
3. Instantiates `FastAPI` with title, description, version, and lifespan.
4. Adds permissive CORS middleware (`allow_origins=["*"]`, credentials enabled, all methods/headers).
5. Includes the three routers.
6. Defines `GET /` and `GET /health`.

#### Produces
A FastAPI `app` object and JSON responses for health/root requests.

#### Sends To
Uvicorn serves the application; registered routers receive matching requests.

#### Important Classes
`FastAPI`, `CORSMiddleware` are framework classes configured in this file.

#### Important Functions
- `lifespan(app)`: initializes SQLite before serving requests; it yields control to FastAPI after startup work.
- `root()`: returns a short service-running message for `GET /`.
- `health()`: returns `{"status":"healthy"}` for `GET /health`.

#### Dependency Flow
```text
Uvicorn
↓
backend/app/main.py
↓
api/chat.py, api/conversations.py, api/documents.py
```

#### Beginner Explanation
This is the backend’s wiring panel. It creates the web app, prepares its database, and tells FastAPI which modules own which URLs.

### `config.py`

#### Purpose
Centralizes filesystem locations and environment/model settings.

#### Called By
Imported by `main` dependencies and services, particularly ingestion, RAG, and chat-history modules.

#### Receives
Environment variables read from `backend/.env` by `load_dotenv()` and values already present in the process environment.

#### Internal Processing
- Computes `BASE_DIR` from the location of this file (the `backend` folder).
- Defines `DATA_DIR`, `DOCUMENTS_DIR`, `STORAGE_DIR`, and `CHAT_DATABASE` paths.
- Defines defaults for model names, chunk settings, and retrieval settings.
- Creates data, documents, and storage directories at import time.
- Raises `ValueError` if `GROQ_API_KEY` is absent.

#### Produces
Path objects and configuration constants.

#### Sends To
`services/ingestion.py`, `services/rag.py`, and `services/chat_history.py` use these constants.

#### Important Classes
`pathlib.Path` is used for platform-aware path construction.

#### Important Functions
- `load_dotenv(ENV_FILE)`: imports environment variables from the local `.env` file into the process environment. It returns no application object.
- Directory `mkdir(...)` calls: ensure the expected data paths exist at import time.

#### Dependency Flow
```text
backend/.env + OS environment
↓
backend/app/config.py
↓
backend/app/services/* and backend/app/api/*
```

#### Beginner Explanation
Instead of hard-coding model names and data paths throughout the app, this module gives every other module a shared set of settings. Importing it also checks that the required Groq key exists.

### `api/documents.py`

#### Purpose
Implements HTTP operations for listing, uploading, and deleting source documents.

#### Called By
The browser calls its routes from `frontend/app.js`; FastAPI dispatches requests to this router.

#### Receives
- `GET /api/documents`: no body.
- `POST /api/documents/upload`: multipart field named `file`.
- `DELETE /api/documents?path=<relative path>`: required query parameter `path`.

#### Internal Processing
- Listing: recursively scans `DOCUMENTS_DIR`; includes files with supported extensions and returns filename, relative path, byte size, and extension.
- Upload: validates filename/extension, strips directory components using `Path(...).name`, reads bytes asynchronously, writes the file to the documents directory, calls `ingest_documents()`, then `reset_index()`.
- Delete: resolves the requested path and checks it remains within the document root; validates the file; unlinks it; rebuilds the index; removes matching source excerpts from SQLite; clears the in-process RAG cache.

#### Produces
JSON document lists, upload/delete confirmations, or HTTP errors.

#### Sends To
The frontend refreshes its document list after successful upload/deletion. Ingestion writes the new local index consumed by `services/rag.py`.

#### Important Classes
- `APIRouter`: owns the `/api/documents` route prefix.
- `UploadFile`: represents multipart upload input.
- `HTTPException`: turns validation/failure conditions into HTTP error responses.

#### Important Functions
- `list_documents()`: no parameters; returns `{"count": n, "documents": [...]}`.
- `upload_document(file)`: receives `UploadFile`; writes it, indexes all documents, clears RAG caches, and returns a message plus `file_name`.
- `delete_document(path)`: receives a required relative path query; removes source and rebuilds index; returns message and filename. It raises 400 for a path escaping the root, 404 for missing/unsupported files, and 500 for rebuild errors.

#### Dependency Flow
```text
frontend/app.js
↓
backend/app/api/documents.py
↓
services/ingestion.py + services/rag.py + services/chat_history.py
```

#### Beginner Explanation
This module is the document-library HTTP boundary. It handles file paths and request validation, then delegates the heavy work of rebuilding retrieval data to ingestion.

### `api/chat.py`

#### Purpose
Handles submitted user questions and temporary engine-reset requests.

#### Called By
The browser’s submit handler calls `POST /api/chat`. `POST /api/chat/reset` exists but the current UI does not call it.

#### Receives
A `ChatRequest` with `message`, `session_id`, optional `file_name`, and optional `mode`.

#### Internal Processing
1. Rejects blank messages with HTTP 400.
2. Finds the SQLite conversation or creates it using the first line of the first prompt as a title (up to 50 characters).
3. If a title is still `New Chat` and there are no messages, changes the title from the prompt.
4. Stores the user message.
5. For `mode == "chat"`, calls `chat_question()`; otherwise it calls `ask_question()`.
6. Stores returned answer and source list as an assistant message.
7. Returns result through a `ChatResponse` response model.
8. Converts exceptions occurring inside the RAG try block to HTTP 500 with exception text.

#### Produces
`{"answer": ..., "sources": [...]}` or an HTTP error.

#### Sends To
The frontend appends the answer and sources; SQLite retains the transcript.

#### Important Classes
`APIRouter`, `HTTPException`, `ChatRequest`, and `ChatResponse`.

#### Important Functions
- `chat(request)`: receives validated chat data; calls SQLite helpers and an RAG function; returns answer/sources.
- `reset_chat(request)`: receives the same ChatRequest schema, calls `reset_chat_session(session_id)`, and returns a reset message. It clears in-process chat-engine instances; it does not delete SQLite history.

#### Dependency Flow
```text
frontend/app.js
↓
backend/app/api/chat.py
↓
services/chat_history.py + services/rag.py
```

#### Beginner Explanation
This is the question coordinator: store what the user asked, ask the RAG service for a response, save the result, and send it back to the browser.

### `api/conversations.py`

#### Purpose
Provides CRUD-style HTTP actions for conversation metadata and transcript retrieval.

#### Called By
The sidebar interactions in `frontend/app.js` call these endpoints.

#### Receives
A chat id in route paths; rename also receives JSON with a `title` string.

#### Internal Processing
Creates UUIDs for new chats; delegates all persistence to `chat_history.py`; strips and limits renamed title text to 80 characters.

#### Produces
Conversation records, message lists, or success messages.

#### Sends To
The frontend lists, opens, renames, and removes sidebar conversations.

#### Important Classes
- `APIRouter`: route prefix is `/api/conversations`.
- `RenameConversationRequest(BaseModel)`: validates the JSON body’s `title` field.

#### Important Functions
- `get_conversations()`: calls `list_chats()` and wraps rows in `conversations`.
- `new_conversation()`: creates a UUID and inserts a chat titled `New Chat`.
- `get_conversation(chat_id)`: checks chat existence and returns metadata/messages; 404 if absent.
- `rename_conversation(chat_id, request)`: validates nonempty title and existing id, stores up to 80 chars.
- `remove_conversation(chat_id)`: validates existence, deletes messages/chat, returns confirmation.

#### Dependency Flow
```text
frontend/app.js
↓
backend/app/api/conversations.py
↓
backend/app/services/chat_history.py
↓
SQLite
```

#### Beginner Explanation
This module gives the UI URLs for starting, reopening, renaming, and deleting conversation records. It does not itself write SQL.

### `schemas/chat.py`

#### Purpose
Defines and validates the JSON contract for chat requests/responses.

#### Called By
FastAPI uses these Pydantic models for the `/api/chat` request and response.

#### Receives
JSON body values supplied to `POST /api/chat` or `/api/chat/reset`.

#### Internal Processing
Pydantic validates field types and the allowed literal values for `mode`.

#### Produces
Typed `ChatRequest`, `Source`, and `ChatResponse` objects; FastAPI serializes response models to JSON.

#### Sends To
`api/chat.py` receives request objects; response objects go to the browser.

#### Important Classes
- `ChatRequest`: `message: str`, `session_id: str`, `file_name: Optional[str] = None`, `mode: Literal["chat", "query"] = "chat"`.
- `Source`: `file_name: str`, `text: str`.
- `ChatResponse`: `answer: str`, `sources: list[Source]`.

#### Important Functions
No custom functions are defined. Pydantic supplies parsing and serialization behavior.

#### Dependency Flow
```text
JSON request
↓
backend/app/schemas/chat.py
↓
backend/app/api/chat.py
```

#### Beginner Explanation
These are the form definitions for data entering and leaving the chat endpoint. They make the accepted shape explicit and reject incompatible values.

### `services/ingestion.py`

#### Purpose
Turns source files into a new persisted LlamaIndex vector index.

#### Called By
`upload_document()` and `delete_document()` in `api/documents.py`.

#### Receives
The shared `DOCUMENTS_DIR`, model settings, and chunk configuration from `config.py`.

#### Internal Processing
1. Configures `Settings.llm` using `Groq(model=LLM_MODEL, api_key=...)` and `Settings.embed_model` using `HuggingFaceEmbedding`.
2. Builds one module-level `SentenceSplitter` with `CHUNK_SIZE` and `CHUNK_OVERLAP`.
3. Checks recursively for supported file extensions; if none exist, clears `STORAGE_DIR` and returns `None`.
4. Uses `SimpleDirectoryReader(input_dir=..., recursive=True).load_data()`.
5. Converts loaded Document objects into nodes with `splitter.get_nodes_from_documents()`.
6. Builds `VectorStoreIndex(nodes)`. LlamaIndex uses the configured embedding model for vector embeddings.
7. Persists into a temporary staging folder under `DATA_DIR`.
8. Renames the old index storage to a backup, moves staging into `STORAGE_DIR`, restores backup if the move fails, then removes backup/staging leftovers.

#### Produces
A `VectorStoreIndex` on success, or `None` for no supported/loaded files. It persists storage as a side effect.

#### Sends To
`api/documents.py` resets RAG cache after ingestion; later `services/rag.py` reloads from persistent storage.

#### Important Classes
- `SimpleDirectoryReader`: loads files recursively into LlamaIndex Documents.
- `SentenceSplitter`: creates sentence-aware overlapping nodes.
- `HuggingFaceEmbedding`: configured local embedding implementation.
- `Groq`: LlamaIndex LLM integration.
- `VectorStoreIndex`: index abstraction holding nodes and vectors.

#### Important Functions
- `clear_index_storage()`: recursively removes the persisted index directory.
- `ingest_documents()`: has no explicit parameters; reads configured documents and returns index or `None`.

#### Dependency Flow
```text
api/documents.py
↓
services/ingestion.py
↓
SimpleDirectoryReader → SentenceSplitter → VectorStoreIndex
↓
data/storage/
```

#### Beginner Explanation
This file is the document preparation assembly line. It reads files, divides them into searchable chunks, converts those chunks into vectors, and saves the index so later questions can use it.

### `services/rag.py`

#### Purpose
Implements index loading, retrieval construction, query transformation, reranking, answer generation, source extraction, and chat-engine caching.

#### Called By
`api/chat.py` calls `chat_question()`, `ask_question()`, and `reset_chat_session()`.

#### Receives
Question text, session id for chat, and optional `file_name` from the API layer; model and retrieval settings from `config.py`.

#### Internal Processing
- Configures LlamaIndex global Settings with Groq and Hugging Face embeddings.
- `get_index()` lazily loads local storage and caches it as `_index`.
- `build_metadata_filters()` creates a LlamaIndex metadata filter only when a file name was provided.
- `get_filtered_nodes()` filters docstore nodes in Python for BM25 and summaries.
- `build_hybrid_retriever()` creates vector and BM25 retrievers, combines them with `QueryFusionRetriever(mode="reciprocal_rerank", num_queries=1)`.
- `build_transformed_retriever()` wraps that combination with `HyDEQueryTransform(include_original=True)` using `TransformRetriever`.
- `build_reranker()` returns `SentenceTransformerRerank` configured with reranker model and top_n.
- `build_document_query_engine()` connects transformed retrieval and reranking with `RetrieverQueryEngine`.
- `build_summary_query_engine()` creates a temporary `SummaryIndex` from selected nodes and a `tree_summarize` engine.
- `build_router_query_engine()` exposes document QA and summary as tools, then builds a `RouterQueryEngine` selected by `LLMSingleSelector`.
- `ask_question()` invokes the router and maps response source nodes to file names/text.
- `get_chat_engine()` creates/reuses a `ContextChatEngine` cached by `session_id:file_name`.
- `chat_question()` calls `.chat(question)` and returns answer/sources.
- `reset_index()` clears `_index` and all cached chat engines.
- `reset_chat_session()` removes only cache entries whose key starts with that session id.

#### Produces
Dictionaries with `answer` and `sources`; each source has `file_name` and node `text`.

#### Sends To
`api/chat.py`, which stores assistant output in SQLite and returns it to JavaScript.

#### Important Classes
`StorageContext`, `VectorStoreIndex`, `SummaryIndex`, `ContextChatEngine`, `QueryFusionRetriever`, `VectorIndexRetriever`, `BM25Retriever`, `TransformRetriever`, `HyDEQueryTransform`, `RetrieverQueryEngine`, `RouterQueryEngine`, `QueryEngineTool`, `LLMSingleSelector`, `MetadataFilter(s)`, and `SentenceTransformerRerank`.

#### Important Functions
- `get_index() -> VectorStoreIndex`: returns cached index or loads it from `STORAGE_DIR`; raises runtime errors if storage/index is missing or invalid.
- `reset_index() -> None`: clears index and chat-engine caches after index changes.
- `get_all_nodes()`: returns docstore values from the loaded index.
- `build_metadata_filters(file_name=None)`: returns `None` for all-doc mode, otherwise exact `file_name` equality filter.
- `get_filtered_nodes(file_name=None)`: returns all nodes or those matching node metadata.
- `build_hybrid_retriever(file_name=None)`: produces fusion retriever over vector/BM25 candidates.
- `build_transformed_retriever(file_name=None)`: adds HyDE transformation to the hybrid retriever.
- `build_reranker()`: makes configured reranking postprocessor.
- `build_document_query_engine(file_name=None)`: combines transformed retrieval with reranking.
- `build_summary_query_engine(file_name=None)`: summarizes selected/all nodes through `SummaryIndex`.
- `build_router_query_engine(file_name=None)`: creates document and summary tools, then a selector/router.
- `ask_question(question, file_name=None)`: uses router query path; returns answer and sources.
- `get_chat_engine(session_id, file_name=None)`: retrieves/builds a process-cached ContextChatEngine.
- `chat_question(question, session_id, file_name=None)`: runs conversational `.chat()`; returns answer and sources.
- `reset_chat_session(session_id)`: drops runtime engines for that session; does not clear SQLite.

#### Dependency Flow
```text
api/chat.py
↓
services/rag.py
├── data/storage/ (load index)
├── retrievers → reranker → Groq answer generation
└── returns answer + sources
↓
api/chat.py → SQLite + frontend JSON
```

#### Beginner Explanation
This is the actual RAG brain of the backend. It finds chunks that may answer the question, improves their order, supplies them to the model, and formats the answer plus evidence.

### `services/chat_history.py`

#### Purpose
Provides SQLite persistence functions for conversations and messages.

#### Called By
`main.py` initializes it; chat and conversation API modules call its functions.

#### Receives
Chat ids, titles, role/content, source objects, and document names.

#### Internal Processing
- `get_connection()` opens SQLite at `CHAT_DATABASE` and returns rows by column name.
- `initialize_database()` creates `chats` and `messages` tables if absent.
- CRUD functions execute parameterized SQL and commit writes.
- `add_message()` JSON-serializes sources and updates `chats.updated_at`.
- `get_chat_messages()` deserializes source JSON, using an empty list if JSON parsing fails.
- `remove_document_sources()` filters a deleted file's excerpts from stored source arrays.
- `delete_chat()` explicitly deletes messages and then chat record.

#### Produces
Python dictionaries/lists for query results; write helpers return `None`.

#### Sends To
API routes turn results into HTTP JSON or confirmations.

#### Important Classes
`sqlite3.Connection`, `sqlite3.Row` and Python `datetime`/`json` utilities.

#### Important Functions
- `get_connection()`: opens configured SQLite DB and sets `row_factory`; returns a connection.
- `initialize_database()`: creates tables; called at backend startup.
- `create_chat(chat_id, title="New Chat")`: inserts a timestamped chat.
- `list_chats()`: returns chats newest-updated first.
- `get_chat(chat_id)`: returns metadata dict or `None`.
- `get_chat_messages(chat_id)`: returns messages oldest-first with parsed sources.
- `add_message(chat_id, role, content, sources=None)`: inserts a message and refreshes activity time.
- `update_chat_title(chat_id, title)`: updates title.
- `remove_document_sources(file_name)`: removes saved source items matching that basename; preserves message text.
- `delete_chat(chat_id)`: deletes messages and chat metadata.

#### Dependency Flow
```text
api/chat.py + api/conversations.py + main.py
↓
services/chat_history.py
↓
backend/data/chat_history.db
```

#### Beginner Explanation
This module is the database access layer. It keeps SQL out of the HTTP route code and translates database rows into data the APIs can return.

### `frontend/index.html`

#### Purpose
Defines the visible application structure.

#### Called By
The browser loads this file as the entry page.

#### Receives
Browser HTML parsing and links to `style.css` and `app.js`.

#### Internal Processing
Defines logo, new-chat button, conversation list, upload control, document list, chat header, messages section, and message form.

#### Produces
DOM elements with ids referenced by JavaScript.

#### Sends To
`frontend/app.js` finds these elements and attaches event listeners; `style.css` styles them.

#### Important Classes
No application classes.

#### Important Functions
No JavaScript functions; HTML provides structure and browser form controls.

#### Dependency Flow
```text
Browser
↓
frontend/index.html
├── frontend/style.css
└── frontend/app.js
```

#### Beginner Explanation
HTML is the page skeleton. It declares controls and placeholders; JavaScript gives them behavior and CSS controls appearance.

### `frontend/app.js`

#### Purpose
Implements browser-side state, API calls, event handling, and rendering.

#### Called By
The browser executes it after loading `index.html`; UI events call its functions.

#### Receives
Click, form-submit, keyboard, and file-input events; JSON and HTTP status from the backend.

#### Internal Processing
- Uses hard-coded `API_BASE_URL = http://127.0.0.1:8000`.
- Creates an initial random session id; a New Chat action obtains an id from backend.
- Calls document and conversation list APIs at load.
- Sends chat JSON with `file_name: null` and no `mode`.
- Uploads `FormData` with a `file` field and client-checks the extension.
- Renders transcript, answer, retrieved sources, upload status, and chat/document controls.
- Escapes rendered text with `escapeHtml()`.

#### Produces
DOM updates and HTTP calls. No persistent browser storage is used for current session id.

#### Sends To
FastAPI routes; API responses are appended to the relevant UI elements.

#### Important Classes
None; plain JavaScript functions and DOM APIs are used.

#### Important Functions
- `loadConversations()`: GET list then calls `renderConversationList()`.
- `renderConversationList(conversations)`: builds each row with open/rename/delete controls.
- `openConversation(chatId)`: GETs conversation, changes `sessionId`, restores visible transcript.
- `createNewConversation()`: POSTs new chat, updates active id, renders welcome state.
- `renameConversation(conversation)`: prompts for title and PATCHes it.
- `deleteConversation(conversation)`: confirms, DELETEs; if active, creates a new chat.
- `loadDocuments()`: GETs document list.
- `renderDocuments(documents)` / `addDocument(documentInfo)`: render every file and a trash control.
- `deleteDocument(documentInfo)`: confirms and DELETEs using its relative path query.
- Chat form submit handler: POST `/api/chat`, then displays result and refreshes conversations.
- `addUserMessage()`, `addAssistantMessage()`: create safe rendered message/source elements.
- `showUploadStatus()`: sets upload status text and CSS state.
- `renderWelcomeState()`: clears transcript view and focuses input.
- `createSessionId()`: uses `crypto.randomUUID()` when available; otherwise timestamp/random fallback.
- `escapeHtml(value)`: inserts value as `textContent` in a temporary element and returns escaped HTML.

#### Dependency Flow
```text
frontend/index.html events
↓
frontend/app.js
↓ HTTP fetch
backend APIs
↓ JSON response
frontend/app.js updates DOM
```

#### Beginner Explanation
This is the interaction layer. It translates button clicks and typed questions into web requests, then turns returned JSON into visible rows and messages.

### `frontend/style.css`

#### Purpose
Styles layout and interaction states.

#### Called By
Loaded by `index.html` through `<link rel="stylesheet">`.

#### Receives
HTML classes/ids and viewport size.

#### Internal Processing
Styles sidebar, chat panel, conversation/document rows, buttons, message bubbles, sources, typing indicator, and mobile layout. At widths at or below 768px it hides `.sidebar`.

#### Produces
Visual appearance only; it has no API/data output.

#### Sends To
Browser rendering engine.

#### Important Classes
Selectors such as `.sidebar`, `.conversation-item`, `.document-item`, `.message`, `.sources`, `.typing` map styles to DOM nodes.

#### Important Functions
CSS `@keyframes typing` animates dots; the media query changes layout at mobile widths.

#### Dependency Flow
```text
frontend/index.html class/id attributes
↓
frontend/style.css
↓
Browser rendering
```

#### Beginner Explanation
CSS controls the visual presentation and responsive behavior; it does not fetch files or implement business logic.

### `requirements.txt`, `.env`, `.gitignore`, and data files

- `backend/requirements.txt`: package names installed with pip. It includes FastAPI, Uvicorn, multipart parsing, dotenv, Pydantic, LlamaIndex, Groq integration, Hugging Face embeddings, BM25 integration, PDF/DOCX/CSV reader packages, and sentence-transformers.
- `backend/.env`: local runtime values loaded by config. Never publish actual secret values.
- Root `.gitignore`: ignores venv, `.env`, and Python bytecode. Its document/storage patterns currently do not match `backend/data/` because they are relative to the repository root.
- `backend/data/documents/`: current sample input files.
- `backend/data/storage/`: generated local index structures.
- `backend/data/chat_history.db`: SQLite persistent application transcript.
- `PROJECT_ARCHITECTURE.md`: a pre-existing high-level overview; verify it against code if it conflicts with these notes.

## C. Document Ingestion

```text
file upload
↓
api/documents.py writes bytes into data/documents/
↓
services/ingestion.py checks supported extensions
↓
SimpleDirectoryReader(recursive=True).load_data()
↓
LlamaIndex Document objects
↓
SentenceSplitter(chunk_size=512, chunk_overlap=50 by default)
↓
Node objects carrying text and loader metadata
↓
VectorStoreIndex(nodes), using Settings.embed_model
↓
persist to staging directory
↓
replace data/storage/
```

1. **Raw file:** Upload route strips client directories from the supplied name and saves only the basename.
2. **Loading:** LlamaIndex `SimpleDirectoryReader` scans recursively. The upload API accepts PDF, TXT, MD, CSV, DOCX. The reader itself is initialized without a `required_exts` argument; its own default reader support determines what can be read if files are manually placed in the directory.
3. **Document objects:** Loaded objects carry source content and metadata. The RAG code later expects `file_name` metadata.
4. **Node parsing:** `SentenceSplitter` uses configured chunk size and overlap. It produces several nodes from larger documents, retaining metadata on nodes.
5. **Embedding:** `VectorStoreIndex(nodes)` embeds nodes through global `Settings.embed_model`, set to `HuggingFaceEmbedding(EMBEDDING_MODEL)`.
6. **Persistence:** The index storage context writes JSON and related files to a temporary staging directory; directory replacement avoids exposing a partially written new index if persistence succeeds but final rename fails.
7. **Reload:** `services/rag.py:get_index()` lazily recreates the index object from persisted local state.

No separate external vector database is configured. The vector store in this project is LlamaIndex local/default storage.

## D. Retrieval System

### Vector retriever

- Implemented in `services/rag.py:build_hybrid_retriever()` as `VectorIndexRetriever`.
- Receives the loaded `VectorStoreIndex`, `similarity_top_k=HYBRID_TOP_K`, and optional LlamaIndex metadata filters.
- Finds nodes by semantic embedding similarity.
- Produces scored node candidates for fusion.

### BM25 retriever

- Constructed with `BM25Retriever.from_defaults(nodes=bm25_nodes, similarity_top_k=HYBRID_TOP_K)`.
- `bm25_nodes` comes from `get_filtered_nodes(file_name)`.
- Ranks text using term-frequency/inverse-document-frequency-style lexical relevance; exact terms and names can be strong signals.
- Produces scored node candidates.

### Fusion

`QueryFusionRetriever` combines vector and BM25 retrievers, configured with `mode="reciprocal_rerank"`, `num_queries=1`, `use_async=False`, and `similarity_top_k=HYBRID_TOP_K`. Despite the config name, `num_queries=1` means this code does not ask fusion to generate a bundle of multiple paraphrased query variants. The mode combines rankings from the two retriever sources.

Hybrid retrieval is useful here because semantic similarity helps with paraphrases while BM25 can preserve exact word matches. The fusion stage offers candidate nodes to the next transform/rerank stage. It is not a guarantee that every relevant chunk is found.

## E. Query Transformation / HyDE

`build_transformed_retriever()` creates:

```text
question
↓
HyDEQueryTransform(include_original=True)
↓
TransformRetriever
↓
hybrid retriever
```

HyDE (Hypothetical Document Embeddings) uses the configured LlamaIndex LLM (`Settings.llm`, Groq integration) to create a hypothetical answer/document-like representation of the question. `include_original=True` retains the original query alongside the transform according to the LlamaIndex transform behavior. The transformed bundle is passed to the wrapped hybrid retriever. Both chat-engine and document QA retrievers are built using this transformed retriever.

Why it is used: a question can have different wording from the source passage; a hypothetical answer-like text can make semantic retrieval more aligned with how the relevant passage is phrased. This is an extra model-dependent transformation, not a separate persisted document and not the final answer.

## F. Metadata Filtering

### Where metadata comes from

`SimpleDirectoryReader` produces metadata for loaded files, including a `file_name` expected by the project. Nodes carry that metadata when `SentenceSplitter` creates chunks.

### Backend-specific selection

- `build_metadata_filters(file_name)` returns `None` if no filename is provided; otherwise constructs a `MetadataFilters` containing exact key/value `file_name == supplied_name`.
- The vector retriever receives that metadata filter.
- `get_filtered_nodes(file_name)` separately filters docstore node metadata in Python for BM25 and summary nodes.

### Current browser behavior

There is no selector in `frontend/index.html`; `frontend/app.js` sends `file_name: null` for all chat requests. Therefore current UI questions search across the complete index. Direct API callers can supply `file_name`, but must match the stored metadata filename. The backend’s document-list `path` is a relative path, but the filter uses only `file_name`, not that relative path.

## G. Reranking

```text
vector + BM25 candidates
↓
SentenceTransformerRerank
↓
up to RERANK_TOP_N candidates
↓
query/chat engine context builder
↓
LLM
```

- `build_reranker()` in `services/rag.py` creates `SentenceTransformerRerank(model=RERANKER_MODEL, top_n=RERANK_TOP_N)`.
- It is registered as a node postprocessor in both `RetrieverQueryEngine.from_args(...)` and `ContextChatEngine.from_defaults(...)`.
- Conceptually, a reranker evaluates each candidate’s relevance to the current query using a cross-encoder-like model. It reorders and keeps the top N; it does not add new source content.
- Retrieval and reranking solve different steps: retrievers cheaply find candidates; reranker improves order among those candidates before context is used.
- Default configured reranker is `BAAI/bge-reranker-base`; top N default is 5.

## H. Query Engine, Chat Engine, Router

### `RetrieverQueryEngine`

Built by `build_document_query_engine()`. It receives a transformed hybrid retriever, Groq LLM and reranker postprocessor. It is the document-QA tool used under the router’s query mode.

### `SummaryIndex` query engine

`build_summary_query_engine()` loads all or filtered nodes, builds an in-memory `SummaryIndex(nodes)`, then calls `.as_query_engine(response_mode="tree_summarize", llm=Settings.llm)`. It is reconstructed when the router is built; this summary index is not the persisted vector index.

### `RouterQueryEngine`

Built by `build_router_query_engine()` with two tools:

1. `document_qa`: intended for a specific question answerable from documents.
2. `document_summary`: intended for overview, summary, key points, or broad explanation.

`LLMSingleSelector` selects a tool using descriptions and the configured LLM. `ask_question()` calls `router.query(question)`, then formats the response and its source nodes. The router path is selected only when `ChatRequest.mode` is `query`.

### `ContextChatEngine`

`get_chat_engine()` creates a chat engine with transformed retriever, LLM, reranker, and system prompt requiring document-grounded answers and an explicit not-found response when retrieved context lacks information. `_chat_engines` caches engines by `session_id:file_name-or-__all__`. `chat_question()` calls `.chat(question)`.

This cache is temporary process state. SQLite messages are not passed into `ContextChatEngine.from_defaults()` when a cache miss occurs. The current frontend defaults to chat mode and uses this engine.

## I. Chat Memory

Two distinct stores exist:

### Durable application transcript

`data/chat_history.db` contains chat metadata, user/assistant message text, timestamps, and JSON source excerpts. A reload of the browser calls `GET /api/conversations`, and selecting a conversation calls `GET /api/conversations/{chat_id}`. The JavaScript renders messages from that response.

### Temporary LlamaIndex conversational context

`services/rag.py` keeps ContextChatEngine objects in `_chat_engines`. They exist only in the backend process. `reset_chat_session()` and `reset_index()` delete these objects. They are not serialized into SQLite.

```text
New Chat click → POST /api/conversations → UUID + SQLite chats row
Question → POST /api/chat → SQLite user message → ContextChatEngine.chat()
Answer → SQLite assistant message + sources
Restart → SQLite transcript remains and can render
         → cached ContextChatEngine is gone; transcript is not rehydrated into it
```

Thus the phrase “chat history persists” is accurate for transcript display, but should not be interpreted as full durable LlamaIndex memory reconstruction.

## J. Frontend ↔ Backend

| User action | JavaScript | HTTP endpoint | Backend result | Browser update |
|---|---|---|---|---|
| Page load document list | `loadDocuments()` | `GET /api/documents` | document metadata | `renderDocuments()` |
| Page load chat list | `loadConversations()` | `GET /api/conversations` | chat summaries | `renderConversationList()` |
| New Chat | `createNewConversation()` | `POST /api/conversations` | UUID/title | `sessionId` changes; welcome panel shown |
| Open previous chat | `openConversation(id)` | `GET /api/conversations/{id}` | conversation + messages | `renderConversationMessages()` |
| Rename chat | `renameConversation()` | `PATCH /api/conversations/{id}` | changed title | reload list |
| Delete chat | `deleteConversation()` | `DELETE /api/conversations/{id}` | delete confirmation | reload; creates a new chat if active one was deleted |
| Upload file | `change` handler | `POST /api/documents/upload` | indexed filename | status message; reload documents |
| Delete file | `deleteDocument()` | `DELETE /api/documents?path=...` | deletion confirmation | status message; reload documents |
| Select document | No current control | None | N/A | UI always supplies `file_name: null` |
| Search all documents | Chat submit | `POST /api/chat` | answer + sources | show assistant answer and sources |
| Reset chat engine | No current control | `POST /api/chat/reset` exists | reset message | not called by current UI |

## K. API Request/Response Reference

### System routes

| Method/path | Request | Response |
|---|---|---|
| `GET /` | none | `{"message":"Enterprise RAG Assistant API is running."}` |
| `GET /health` | none | `{"status":"healthy"}` |

### Documents

#### `GET /api/documents`
No request body. Returns `{"count": n, "documents": [{"file_name":"...","path":"relative/path","size":123,"extension":".txt"}]}`. It recursively scans the configured documents directory.

#### `POST /api/documents/upload`
Multipart/form-data with a `file` field. Success returns a message and `file_name`. It accepts `.pdf`, `.txt`, `.md`, `.csv`, `.docx` case-insensitively. Missing filename or unsupported suffix yields 400; errors inside save/ingestion yield 500.

#### `DELETE /api/documents?path=finance_sample.txt`
Required relative path query. Success returns message and `file_name`. Traversal outside document root yields 400; missing file or unsupported extension yields 404; index-rebuild failure yields 500 after source deletion and index clearing.

### Chat

#### `POST /api/chat`
Request schema:

```json
{
  "message": "What is the policy?",
  "session_id": "client-chat-id",
  "file_name": null,
  "mode": "chat"
}
```

`file_name` may be omitted/null. `mode` may be `chat` or `query`, default `chat`. Success response follows `ChatResponse`:

```json
{
  "answer": "...",
  "sources": [{"file_name": "finance_sample.txt", "text": "..."}]
}
```

Frontend omits `mode` and uses null `file_name`. A blank message produces 400. A RAG exception produces 500 detail. User message insertion happens before the RAG try/except, so a failed request can leave a user-only database turn.

#### `POST /api/chat/reset`
Request body is also `ChatRequest` (therefore requires `message` and `session_id` even though reset only uses session id). Returns `{"message":"Chat session reset."}` and drops cached engines for that session. SQLite rows remain. The browser does not invoke it.

### Conversations

- `GET /api/conversations`: `{"conversations":[chat records...]}`.
- `POST /api/conversations`: returns `{"chat_id":"uuid","title":"New Chat"}`.
- `GET /api/conversations/{chat_id}`: returns `{"conversation": chat, "messages": [...]}` or 404.
- `PATCH /api/conversations/{chat_id}`: JSON `{"title":"Review Notes"}`; trims, rejects empty title (400), caps stored value at 80 chars; 404 for unknown chat.
- `DELETE /api/conversations/{chat_id}`: removes messages and chat, then returns `{"message":"Conversation deleted."}`; 404 for unknown chat.

## L. Data Flow at Each Stage

| Stage | Example shape |
|---|---|
| Raw source | File bytes at `data/documents/handbook.pdf` |
| LlamaIndex Document | Text plus loader metadata such as file name/path |
| Node | One chunk of document text with inherited metadata |
| Embedded node | Node plus a numeric vector produced by BGE embedding model |
| Indexed node | Node/vector represented in LlamaIndex storage |
| Candidate | Scored node from vector or BM25 retriever |
| Fused candidate | Candidate ranked from retriever combination |
| Reranked candidate | Candidate ordered/selected by BGE reranker |
| Chat/query context | Context built by LlamaIndex engine from selected node text |
| Output | Answer string plus source node file name/text |
| Persisted message | SQLite row with role/content and JSON text for sources |

The exact vector values and internal LlamaIndex serialization are generated at runtime; this guide does not invent specific embeddings or scoring outputs.

## M. Why These Technologies

- **Python:** backend ecosystem and direct support from FastAPI, LlamaIndex, and Hugging Face integration.
- **FastAPI:** concise route registration, async upload/chat endpoints, and Pydantic request/response integration.
- **LlamaIndex:** avoids hand-building document readers, node structures, vector indexing, retrievers, and engine orchestration.
- **Groq LLM integration:** remote model calls through the configured Groq API key/model; model choice is environment-configurable.
- **Hugging Face embedding model:** locally loaded embedding model turns nodes and retrieval queries into vectors.
- **Default local LlamaIndex vector store:** persists with the index files under `data/storage/`, useful for a compact project without an external vector service.
- **BM25:** lexical retrieval path complements semantic vector search for exact words.
- **Reranker:** second-pass candidate ordering by a relevance model.
- **SQLite:** simple file-based database appropriate for one local application process and persistent chat rows.
- **HTML:** defines page structure and native controls.
- **CSS:** handles appearance, layout, and mobile breakpoint.
- **JavaScript:** handles events, HTTP fetch, session id, safe text rendering, and UI updates.

Alternatives that are not used include PostgreSQL, Redis, a hosted vector database, React, and a separate frontend build tool. They could be introduced later if the deployment or scale requires them.

## N. Important Programming Concepts

- **Modules/imports:** API modules import service functions; `main.py` imports routers; config values flow by imports.
- **Functions:** operations such as `ingest_documents()` encapsulate one task and return objects/data.
- **Type hints:** used in parameters and schema fields; examples include `Optional[str]`, `VectorStoreIndex | None`, and route argument types.
- **Pydantic models:** `ChatRequest`, `ChatResponse`, `Source`, and `RenameConversationRequest` validate API data.
- **Async/await:** FastAPI endpoints use `async def`; file reads use `await file.read()`. RAG calls themselves are synchronous in the code.
- **Decorators:** `@router.get`, `@router.post`, `@router.patch`, and `@router.delete` register URL handlers.
- **Exceptions:** `HTTPException` expresses HTTP error statuses; broad `except Exception` catches chat/upload/delete failures and maps them to 500 in those paths.
- **Environment variables:** `dotenv` loads local `.env`; `os.getenv()` chooses settings and defaults.
- **Filesystem handling:** `Path`, `.resolve()`, `.is_relative_to()`, `unlink()`, and directory rename operations manage documents/storage.
- **SQL and transactions:** `sqlite3` parameter placeholders (`?`) keep values separate from SQL strings; mutations call `commit()`.
- **JSON serialization:** source arrays are written with `json.dumps()` and reconstructed with `json.loads()`.
- **HTTP client:** browser `fetch()` sends JSON and multipart requests.
- **DOM manipulation:** JavaScript creates elements, sets `textContent` for safe escaping helper, and appends them.

## O. End-to-End Trace: Upload and Ask About a Handbook

The scenario asks about a PDF; the repository supports PDF upload, but its current checked-in sample documents are `finance_sample.txt` and `security_operations.txt`.

1. Browser displays upload controls from `frontend/index.html`.
2. User chooses a `.pdf`; the `change` handler in `frontend/app.js` checks extension.
3. JavaScript puts the file into `FormData` under key `file`.
4. It sends `POST http://127.0.0.1:8000/api/documents/upload`.
5. FastAPI dispatches to `api/documents.py:upload_document(file)`.
6. The route sanitizes to basename and writes bytes under `backend/data/documents/`.
7. It calls `services/ingestion.py:ingest_documents()`.
8. `SimpleDirectoryReader` scans the directory recursively and returns Document objects.
9. `SentenceSplitter` turns each Document into nodes using configured chunk size/overlap.
10. `VectorStoreIndex(nodes)` uses the configured Hugging Face embedding model and creates local index storage.
11. Persisted files replace `backend/data/storage/`; API calls `reset_index()` to invalidate runtime cache.
12. The browser reloads document list and shows the file.
13. User submits a question; JS sends `message`, `session_id`, `file_name: null`, omitting `mode`.
14. `ChatRequest` defaults mode to `chat`; the API ensures a SQLite chat row, sets first-message title if needed, and stores user message.
15. `chat_question()` calls `get_chat_engine()` for that session.
16. `get_index()` loads persisted index on demand.
17. No metadata filter applies because `file_name` is null; retrieval spans the full index.
18. HyDE transform wraps vector+BM25 hybrid retrieval; fusion mode is reciprocal rerank.
19. `SentenceTransformerRerank` retains/ranks top nodes.
20. `ContextChatEngine` uses selected context and Groq to answer; the system prompt tells it to report when information is not found in retrieved documents.
21. RAG code extracts source node `file_name` metadata and `node.text`.
22. Chat API saves assistant text/source list in SQLite and returns `ChatResponse`.
23. JavaScript renders answer and retrieved source snippets.

No frontend-selected `handbook.pdf` filter is involved in this trace because the current page has no document selector. To exercise exact file filtering, an API caller must pass matching `file_name`.

## P. End-to-End Trace: New Chat, Restart, Reopen

1. The New Chat button fires `createNewConversation()`.
2. JavaScript sends `POST /api/conversations`.
3. The route makes UUID, inserts `chats` row titled `New Chat`, returns id/title.
4. Browser sets `sessionId` to that id.
5. On first submitted question, `/api/chat` finds that row and assigns a title from prompt if still empty history/`New Chat`.
6. `add_message()` stores user text; RAG processes question; another `add_message()` stores assistant answer/source JSON.
7. User restarts backend: SQLite file remains, but `_chat_engines` Python dictionary is recreated empty.
8. Browser initial load calls `GET /api/conversations`; sidebar receives metadata.
9. User clicks a chat; `GET /api/conversations/{id}` reads transcript rows.
10. JavaScript renders those stored turns.
11. On a subsequent question, if no process cache exists, `get_chat_engine()` constructs a new ContextChatEngine without passing the saved turns.

Therefore transcript visibility survives restart. Context continuity inside LlamaIndex does not fully survive unless the same engine remains in process. This is a verified implementation limitation, not a database issue.

## Q. Why the Architecture Is Split

- **API layer:** HTTP-specific validation/status and request-to-service coordination.
- **Schema layer:** establishes the JSON contract separately from business logic.
- **Service layer:** ingestion, RAG, and persistence can be called by routes without embedding all logic in endpoint functions.
- **RAG layer (currently `services/rag.py`):** centralizes retrieval and answer generation.
- **Storage layer:** source files, LlamaIndex persistence, and transcript database have distinct responsibilities.
- **Frontend:** static page can change or make requests without accessing SQLite or embedding models directly.

Putting every route, SQL query, retrieval component, and startup setting in `main.py` would make ownership and testability harder. Here `main.py` is already mostly composition/wiring, while route modules handle specific API concerns. Note that the conceptual `rag/`, `retrieval/`, `ingestion/` directories are currently empty; code is not yet split into these subpackages.

## R. Common Confusions

### Document vs Node
A Document is loader-level source content and metadata. A Node is a smaller parsed chunk created by `SentenceSplitter`; nodes are the retrieval/index units in this project.

### What is an embedding?
A numeric representation of text used for semantic similarity. Here the configured BGE embedding model is used when creating `VectorStoreIndex` and later for vector retrieval.

### What is an index?
A LlamaIndex structure that coordinates stored nodes and vector search. The project creates `VectorStoreIndex` during ingestion and reloads it using storage context after restart.

### What is a retriever?
A component that selects candidate nodes for a query. This code combines `VectorIndexRetriever` and `BM25Retriever`.

### What is hybrid retrieval?
Using more than one retrieval signal. Here vector semantic search plus BM25 lexical search feed `QueryFusionRetriever`.

### What is BM25?
A lexical ranking algorithm based on term occurrence and document statistics. In this project it is initialized over docstore nodes.

### What is reranking?
A second model-based ranking pass over already retrieved candidates. It cannot recover a relevant node that retrieval never returned.

### What is metadata filtering?
Restricting matching nodes by metadata. `file_name` equality is supported in the backend; current frontend passes null and has no selector.

### What is HyDE?
Query transformation using a hypothetical answer/document-like text to alter retrieval input. `HyDEQueryTransform(include_original=True)` wraps the hybrid retriever.

### Query Engine vs Chat Engine
Query engines answer a query and return a response, used for document QA and summary in router mode. The `ContextChatEngine` has conversational `.chat()` behavior and is the default browser path.

### What is RouterQueryEngine?
An engine that uses a selector to choose among query-engine tools. Here the tools are document QA and summary; the API invokes it only when mode is `query`.

### What is chat memory?
The ContextChatEngine's current internal conversation state. In this project engine instances are cached in `_chat_engines` while the backend process lives.

### What is persistent storage?
Data stored outside volatile process memory. Index JSON files and SQLite survive process restart on disk.

### LlamaIndex storage vs chat-history storage
LlamaIndex storage contains index/docstore/vector structures used for retrieval. SQLite contains chat ids, titles, user/assistant text, timestamps, and source excerpts. They are not one shared database.

### Why does “All Documents” need no filter?
The backend interprets `file_name=None` as no filtering and searches all nodes. Current UI sends null and there is not an actual “All Documents” selector control.

### Why can retrieval return multiple nodes?
A document is split into chunks; several distinct passages may support an answer. The retrieval top-k config is 10 for hybrid candidate retrieval by default.

### Why rerank after retrieval?
Retrieval generates candidates using vector and lexical signals. The reranker performs a later relevance ordering and keeps top five by default.

### Why does the LLM not directly search documents?
The LLM call is separated from file access. LlamaIndex retrievers select document nodes and engines pass retrieved context to generation. The LLM does not traverse the files itself.

## S. Presentation Preparation

### 30-second explanation
“This project is a document-question-answering app built with FastAPI and LlamaIndex. It reads uploaded files, splits them into chunks, embeds and persists them locally, then uses combined vector and BM25 retrieval, HyDE, and reranking to prepare evidence for a Groq LLM. FastAPI returns an answer with source excerpts, and SQLite stores conversation transcripts.”

### 1-minute explanation
“The browser is a static HTML, CSS, and JavaScript frontend. It calls FastAPI routes for document upload/list/delete, chat, and conversations. On upload, the backend uses LlamaIndex’s directory reader and sentence splitter, creates a VectorStoreIndex using a Hugging Face embedding model, and persists it locally. For chat, the default ContextChatEngine uses a HyDE-transformed retriever that fuses vector and BM25 results, then reranks candidates before Groq generation. The answer and source nodes go to the browser and are also stored in SQLite. Chat transcripts can be reopened, renamed, and deleted. A limitation I would mention is that SQLite restores the visible transcript, but cached LlamaIndex chat memory is not reconstructed after a backend restart.”

### 3-minute explanation

1. Describe the problem: users need answers grounded in their own documents rather than manually searching each file.
2. Explain layers: static frontend, FastAPI routing, service modules, local file/index storage, SQLite chat records.
3. Explain ingestion: upload, validation, directory reader, sentence-aware nodes, BGE embeddings, VectorStoreIndex, staging persistence.
4. Explain query: request validation, chat record, HyDE transform, vector and BM25 candidates, reciprocal-rank fusion, reranker, context chat engine, Groq generation.
5. Explain evidence and persistence: source node text is returned and stored; chat transcript is saved separately from index.
6. Distinguish actual interface from backend capability: UI searches all documents in chat mode; optional filename filter and router summary mode are available to API callers but not exposed in current UI.
7. Mention tradeoffs and improvements: local storage and SQLite suit a learning project; consider memory rehydration, auth, restricted CORS, tests, and transactional/background ingestion for production.

### 5-minute technical explanation

Start with architecture and component responsibilities. Walk through upload route validation and basename handling. Explain `SimpleDirectoryReader` output, metadata-bearing Documents, `SentenceSplitter` nodes, global embedding configuration, `VectorStoreIndex`, and the temporary staging/rename persistence strategy. Then trace chat request through Pydantic and SQLite. Explain `get_index()` lazy load, optional `MetadataFilters`, Python node filtering for BM25, `VectorIndexRetriever`, `BM25Retriever`, `QueryFusionRetriever(mode="reciprocal_rerank")`, and HyDE transform. Explain reranker top N and the ChatEngine's system prompt. Contrast `ContextChatEngine` with router `RetrieverQueryEngine`/`SummaryIndex`, and describe `LLMSingleSelector` routing. End with source nodes, transcript persistence, known limitation of volatile engine cache, security/deployment gaps, and potential next steps.

### Architecture Explanation Script

“Users interact with a static web interface built from HTML, CSS, and JavaScript. The browser sends file and chat requests to FastAPI. When a file is uploaded, the documents API validates its extension and saves it under the backend data directory. The ingestion service loads all files with LlamaIndex, splits their text into overlapping sentence-aware nodes, embeds those nodes, and persists a local vector index.

When a question arrives, the chat API validates it and records the user turn in SQLite. The RAG service loads the persisted index, optionally applies a filename filter, and builds a retriever from vector search and BM25. HyDE transforms the retrieval input, fusion combines the candidate rankings, and a sentence-transformer reranker selects the strongest passages. The ContextChatEngine sends that context to the configured Groq model. The backend returns an answer plus source text and saves both to the conversation database.

The project also has a query mode with a router that can select document QA or summary, although the current frontend does not expose that mode. SQLite preserves transcripts for display, while the LlamaIndex chat-engine cache remains process-local. That distinction is one of the current limitations I would address next.”

## T. Interview Questions

### Beginner

**1. What problem does the app solve?**
- Expected answer: It lets a user ask questions about uploaded documents and see answer evidence without manually locating passages.
- Tests: Problem framing.

**2. What is RAG?**
- Expected answer: Retrieval-Augmented Generation retrieves relevant source text and supplies it to an LLM for grounded generation; this app retrieves LlamaIndex nodes before Groq answers.
- Tests: Basic system understanding.

**3. What is the difference between a Document and a Node here?**
- Expected answer: Reader returns a Document; SentenceSplitter breaks it into metadata-bearing chunk nodes used in indexing/retrieval.
- Tests: Ingestion understanding.

**4. Why is `ChatRequest` a Pydantic model?**
- Expected answer: FastAPI validates the incoming shape and field types before the chat function runs.
- Tests: API basics.

### Intermediate

**5. Why does this project combine vector and BM25 retrieval?**
- Expected answer: Semantic search handles conceptual similarity; BM25 helps exact terms. Fusion combines their rankings before reranking.
- Tests: Retrieval design.

**6. What does HyDE do in this code?**
- Expected answer: `HyDEQueryTransform(include_original=True)` transforms the query input before the hybrid retriever; the configured LLM participates in transformation.
- Tests: Query transformation knowledge.

**7. Why use a reranker after retrieval?**
- Expected answer: Retrievers find candidates efficiently; reranker scores query-candidate relevance and retains top N. It cannot recover missing candidates.
- Tests: Pipeline roles.

**8. What does the `file_name` filter do?**
- Expected answer: It adds an exact metadata filter for vector retrieval and also filters docstore nodes in Python for BM25/summary. Current UI passes null.
- Tests: Metadata flow and attention to implementation.

**9. What is the difference between ChatEngine and QueryEngine here?**
- Expected answer: Default `ContextChatEngine` handles conversational chat; `RetrieverQueryEngine` performs document QA in router mode, with `SummaryIndex` for summaries.
- Tests: LlamaIndex concepts.

**10. How are conversation titles assigned?**
- Expected answer: New chat starts titled “New Chat”; first prompt first line replaces it (max 50 chars). API rename can set up to 80 chars.
- Tests: Code-level flow.

### Advanced

**11. What happens to the index after upload?**
- Expected answer: Rebuilt from all documents and persisted to staging; storage is replaced; RAG process cache reset.
- Tests: Index lifecycle.

**12. How are the chat index and history persisted differently?**
- Expected answer: LlamaIndex local storage files contain retrieval data; SQLite contains chats/messages/sources. Chat-engine instances are cached in RAM only.
- Tests: Persistence boundaries.

**13. Does chat context survive backend restart?**
- Expected answer: The transcript survives and is renderable, but current code does not hydrate saved messages into a newly created ContextChatEngine.
- Tests: Distinguishing UI persistence from model memory.

**14. What is the router selecting?**
- Expected answer: An `LLMSingleSelector` selects between `document_qa` and `document_summary` tools from descriptions; `mode="query"` is needed to call it.
- Tests: Tool routing.

**15. Is `SIMILARITY_TOP_K` active?**
- Expected answer: It exists in config and is imported into `rag.py` but isn’t used; actual retriever top-k comes from `HYBRID_TOP_K`.
- Tests: Source inspection accuracy.

**16. Why use a temporary directory during index persistence?**
- Expected answer: It stages a complete index before replacing current storage and attempts to restore old storage if the staging rename fails.
- Tests: Data replacement behavior.

### Tricky Questions

**17. Does the current UI let a user select a document?**
- Expected answer: No. It sends `file_name: null` and searches the full index. Backend optional filtering exists for API callers.
- Tests: Avoiding README/UI assumptions.

**18. Does `mode="query"` run through the current frontend?**
- Expected answer: No; frontend omits `mode`, schema defaults it to `chat`.
- Tests: Frontend/backend contract.

**19. What happens if user upload has an existing basename?**
- Expected answer: Upload saves using basename directly, so it overwrites the existing file before rebuilding the full index.
- Tests: File lifecycle and collision awareness.

**20. What if indexing fails after deleting a document?**
- Expected answer: Source has already been unlinked; route clears index storage/cache and returns 500, leaving no queryable index until a successful rebuild.
- Tests: Error/transaction awareness.

**21. Is the app production-secure as configured?**
- Expected answer: No. CORS allows `*` with credentials, and there is no authentication/authorization or user partitioning. It is a local learning app configuration.
- Tests: Security judgment.

**22. Is `POST /api/chat/reset` a complete chat deletion?**
- Expected answer: No. It only removes cached LlamaIndex engines; SQLite transcript remains. To delete records use conversation DELETE.
- Tests: Similar-sounding operations.

**23. Does the LLM search the filesystem?**
- Expected answer: No. Reader/ingestion and retrievers supply selected node text; LLM generates from engine context.
- Tests: RAG separation.

**24. What would you improve first?**
- Expected answer: Restore ContextChatEngine memory from SQLite messages, expose a document filter/mode selector, tighten CORS/add auth, add tests, and make ingestion transactional/background for larger files.
- Tests: Prioritization grounded in code.

## U. Troubleshooting

### Backend does not start
```text
Problem → import/config or port error
Check → backend/.env, backend/venv, terminal output, port 8000
Fix → set GROQ_API_KEY; activate correct environment; stop existing server or choose a new port and update frontend API_BASE_URL
```

### Missing environment variable
`config.py` raises `ValueError` when `GROQ_API_KEY` is not loaded. Check that `.env` is at `backend/.env` and key is named exactly. Never paste secret values into logs/docs.

### Frontend cannot reach backend
Check hard-coded `API_BASE_URL` in `frontend/app.js`, server startup, browser origin, and CORS. Current backend permits all origins, so wrong host/port is more likely than restrictive CORS.

### Upload returns unsupported file error
Check suffix against `.pdf`, `.txt`, `.md`, `.csv`, `.docx`. The browser validates the same set, and backend validates it again.

### Upload fails or file missing from list
Check upload route response and `backend/data/documents/` permissions. Upload writes the basename, then reindexes. If ingestion fails after writing, the saved file can remain even though API returned an error; retry/rebuild after correcting the underlying problem.

### Document list appears empty
`GET /api/documents` scans configured `DOCUMENTS_DIR`. Ensure the frontend is connected to the intended backend and files are inside `backend/data/documents/` with supported suffixes.

### Query says no valid index / no documents
Upload a supported document to trigger `ingest_documents()`. Check `backend/data/storage/` and ingestion output. `get_index()` raises if there is no valid storage index.

### Wrong or no node is retrieved
Check that indexing completed, the uploaded text is extractable, `file_name` is null or matches actual metadata, and configured embedding/retrieval models loaded. Hybrid top K and reranker top N affect candidates/selection; neither guarantees relevance.

### Reranker/model fails
Check package installation and Hugging Face model access/cache. First load may download models and emit Hugging Face rate warnings. Reranker is `BAAI/bge-reranker-base` by default.

### Groq call fails
Check network, `GROQ_API_KEY`, and `LLM_MODEL` supported by account/integration. `/api/chat` returns a 500 detail for exceptions caught in RAG processing.

### Conversation does not appear
Check `/api/conversations`, backend SQLite path, browser network panel, and API origin. Database is `backend/data/chat_history.db`; lifespan initializes tables.

### Conversation opens but answer context seems reset after restart
This is expected from current memory design: the browser reloads SQLite transcript, but `ContextChatEngine` memory is a process cache and is not reconstructed from those messages.

### Port 8000 already in use
A prior Uvicorn server is listening. Stop that process or run a different port and change `API_BASE_URL` in `frontend/app.js` to match.

## V. Future Improvements

### Already Implemented

- Document upload/list/delete; index is rebuilt after upload/deletion.
- Local persistent LlamaIndex index.
- Vector/BM25 fusion, HyDE, reranking.
- Chat engine and backend router query path.
- SQLite conversation records/transcripts, rename/delete, transcript reload.
- Source excerpts included in API response and transcript.

### Possible Future Improvements (not currently implemented)

- Rehydrate `ContextChatEngine` from SQLite message history.
- Add UI document selection and query-mode selection.
- Authentication, authorization, multi-user boundaries, per-user documents.
- Narrow CORS and validate deployment configuration.
- Background ingestion, job status, progress reporting, cancellation.
- File size limits, MIME/content validation, duplicate-name strategy, rollback.
- API/service tests, retrieval evaluation datasets, tracing/observability and structured logs.
- Database migrations; PostgreSQL for shared multi-worker deployment; Redis only if a concrete cache/session need appears.
- Configurable external vector storage for scale; containerization and deployment automation (no Docker configuration currently exists).
- Streaming responses and richer citations.

## Project Flow Discovered

```text
Browser HTML/CSS/JS
↓
JavaScript fetch() to hard-coded http://127.0.0.1:8000
↓
FastAPI main.py registers routers; startup initializes SQLite tables
↓
Documents API writes/removes source files and returns file metadata
↓
Ingestion loads files with SimpleDirectoryReader
↓
SentenceSplitter makes overlapping nodes
↓
VectorStoreIndex creates embeddings and local persistent storage
↓
Chat API validates ChatRequest and stores user message
↓
RAG loads index and optionally filters node metadata by file_name
↓
HyDE TransformRetriever wraps vector + BM25 reciprocal-rank fusion
↓
SentenceTransformerRerank selects top nodes
↓
ContextChatEngine (default mode) or RouterQueryEngine (query mode)
↓
Groq generates response using engine context
↓
Answer + source file names/text return to FastAPI
↓
SQLite stores assistant turn and source JSON
↓
JavaScript renders answer, sources, transcript, and document/chat lists
```

## Important Findings

- Active code lives in `backend/app/services/`; sibling `ingestion/`, `rag/`, and `retrieval/` folders are empty.
- Current frontend has no per-document selector and always sends `file_name: null`; the optional backend filter remains usable by direct API clients.
- Current frontend always defaults to `chat`; RouterQueryEngine is backend-only because `mode` is omitted and defaults to `chat`.
- SQLite persists and restores visible transcript messages, but does not restore ContextChatEngine internal state after backend restart.
- `SIMILARITY_TOP_K` and `QueryBundle` are imported/configured but unused in active `rag.py`; `HYBRID_TOP_K` controls candidate counts.
- `conversationListCache` is assigned and used to render the current conversation list; it is not durable browser storage.
- Chat reset route exists but has no frontend button; reset only clears the in-memory engine cache.
- Uploads can overwrite same-basename files; failed ingestion may leave an uploaded file on disk.
- Deletion removes stored source excerpts by basename (`file_name`), not by relative path. Since upload currently writes to the documents root this is normally consistent for uploaded files, but manually maintained nested files with duplicate basenames can cause ambiguous citation cleanup.
- Document deletion happens before reindex; on rebuild failure, the index is cleared and unavailable until successful ingestion.
- SQLite connection setup declares a foreign key in schema but does not explicitly enable SQLite foreign-key enforcement; deletion manually removes message rows first.
- CORS is permissive (`*` plus credentials); no authentication/authorization or multi-user isolation exists.
- CSS hides the sidebar at the mobile breakpoint, so document/chat management controls are unavailable on narrow screens.
- `backend/tests/` exists but no test modules were found. No Docker files or standalone utility scripts were found in the inspected tree.
- Ingestion prints counts and storage location; no structured logging configuration is present.
- Root `PROJECT_ARCHITECTURE.md` predates or may not include every current detail; the docs here were based on source code.
