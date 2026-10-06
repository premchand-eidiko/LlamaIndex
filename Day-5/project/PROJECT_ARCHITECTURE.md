# Enterprise RAG Assistant Architecture

## 1. High-level application flow

```text
Browser / Frontend
    │
    ▼
HTML + JavaScript UI
    │
    │  - sends chat questions
    │  - uploads documents
    │  - shows chat history
    │  - shows uploaded files
    ▼
FastAPI backend
    │
    ├── /api/documents
    │      - upload documents
    │      - list uploaded documents
    │      - delete a document and rebuild the index
    │
    ├── /api/chat
    │      - ask question
    │      - send question into RAG
    │
    └── /api/conversations
           - create new chat
           - load old chats
           - continue previous conversation
            - rename or delete a chat

    │
    ▼
App services
    │
    ├── ingestion.py
    │      Document ingestion + embedding creation
    │
    ├── rag.py
    │      Query transformation + retrieval + reranking + Groq answer generation
    │
    └── chat_history.py
           Persistent SQLite chat storage

    │
    ▼
LlamaIndex + storage
    │
    ├── data/documents/
    │      original uploaded files
    │
    ├── data/storage/
    │      vector index + metadata
    │
    └── data/chat_history.db
          chat and message history
```

---

## 2. Project structure

```text
project/
├── backend/
│   ├── .env
│   ├── requirements.txt
│   ├── venv/
│   └── app/
│       ├── __init__.py
│       ├── main.py
│       ├── config.py
│       ├── api/
│       │   ├── __init__.py
│       │   ├── chat.py
│       │   ├── conversations.py
│       │   └── documents.py
│       ├── schemas/
│       │   ├── __init__.py
│       │   └── chat.py
│       ├── services/
│       │   ├── __init__.py
│       │   ├── chat_history.py
│       │   ├── ingestion.py
│       │   └── rag.py
│       └── data/
│           ├── documents/
│           ├── storage/
│           └── chat_history.db
│
├── frontend/
│   ├── index.html
│   ├── style.css
│   └── app.js
│
├── PROJECT_ARCHITECTURE.md
└── .gitignore
```

---

## 3. File-by-file responsibility

### backend/app/main.py

This is the application entry point. It starts the FastAPI service, enables CORS for browser access, and registers the routers.

Data flow:
- browser sends request to /api/chat or /api/documents
- main.py routes the request to the correct API module
- API module performs logic and returns a response to the frontend

Output:
- an app instance that serves the APIs
- routing to chat, conversations, and documents endpoints

### backend/app/config.py

This file acts as the central configuration center for the whole backend.

Responsibilities:
- defines the base backend directory
- points to data/documents and data/storage
- loads environment variables from .env
- reads LLM, embedding, and reranker settings
- creates required folders if missing
- validates critical settings such as GROQ_API_KEY

Output:
- configuration values used by ingestion, retrieval, and chat logic

### backend/app/api/documents.py

This file handles everything related to the document library.

Responsibilities:
- list all uploaded supported files
- save uploaded files inside data/documents/
- rebuild the LlamaIndex vector store after upload
- delete an uploaded file and rebuild the index from remaining files
- return document metadata to the frontend

Data flow:
- frontend uploads a file
- documents.py saves it to disk
- ingest_documents() builds the index
- reset_index() clears memory cache
- frontend refreshes the document list
- frontend document deletion removes the source and its indexed nodes

### backend/app/api/chat.py

This is the main chat endpoint.

Responsibilities:
- validate incoming message
- ensure the conversation exists in SQLite
- store the user message
- call rag.py logic to generate an answer
- save the assistant answer back to SQLite
- return the answer and source information to the frontend

Data flow:
- frontend POST /api/chat
- chat.py validates request and session id
- rag.py creates answer
- chat.py writes answer to chat_history.db
- frontend displays the result

### backend/app/api/conversations.py

This file makes chat history persistent and visible.

Responsibilities:
- list all conversations
- create a new conversation
- fetch one conversation with its messages
- rename a conversation
- delete a conversation

Data flow:
- frontend asks for /api/conversations
- conversations.py reads SQLite via chat_history.py
- frontend can display previous chats and reopen them
- first message supplies the default title; users can later rename or delete chats

### backend/app/services/chat_history.py

This file is the database layer for the application.

Responsibilities:
- create SQLite connection
- initialize tables
- create new chats
- list chats
- fetch chat messages
- insert user and assistant messages
- update chat titles and timestamps
- delete conversations

Data flow:
- chat.py and conversations.py call this file
- chat_history.py writes or reads rows from data/chat_history.db
- the frontend receives persisted chat metadata and message history

### backend/app/services/ingestion.py

This is the data ingestion layer.

Responsibilities:
- read files from data/documents/
- split documents into chunks
- create embeddings using the configured embedding model
- create a VectorStoreIndex
- persist the index into data/storage/

Data flow:
- uploaded file lands in data/documents/
- ingestion.py transforms it into nodes
- nodes become embeddings
- index is saved to storage
- RAG queries can later retrieve this content

### backend/app/services/rag.py

This is the core reasoning engine of the project.

Responsibilities:
- build the vector and BM25 retrievers
- apply metadata filtering
- use query transformation (HyDE)
- rerank relevant nodes
- answer direct questions using RouterQueryEngine
- handle conversational chat via ContextChatEngine
- return retrieved sources for the frontend

Data flow:
- user question enters rag.py
- query is transformed and relevant chunks are retrieved
- reranking chooses the best chunks
- Groq generates the final answer
- answer + sources are returned to chat.py and then to the frontend

### backend/app/schemas/chat.py

This file defines the request and response schema used by Pydantic.

Responsibilities:
- validate input JSON for chat requests
- define ChatRequest with message, session_id, file_name, mode
- define ChatResponse with answer and sources

Output:
- stable and validated API contracts between frontend and backend

### frontend/index.html

This is the UI structure.

Responsibilities:
- sidebar with new chat button
- conversation list
- document upload button
- complete uploaded-document list with per-file delete controls
- per-chat rename and delete controls
- chat area for messages
- text area for user input

Data flow:
- the browser loads the interface
- JavaScript calls the backend API
- the interface updates after each API response

### frontend/app.js

This is the frontend logic layer.

Responsibilities:
- call backend routes
- manage current chat session
- load conversation history from SQLite
- load uploaded documents from backend
- create a new chat
- open an old chat
- rename or delete a chat
- send messages to /api/chat
- display every uploaded document and delete selected files

Output:
- the UI changes after each user action
- previous chats remain available
- uploads are refreshed immediately

### frontend/style.css

This file defines the visual design of the application.

Responsibilities:
- layout for sidebar and chat panel
- styling of buttons, cards, lists, and message bubbles
- upload status states
- conversation list and document list styling

Output:
- a clean, presentation-friendly chat interface

---

## 4. Core request lifecycle

### Upload a document

```text
frontend/index.html
    ↓
frontend/app.js
    ↓
POST /api/documents/upload
    ↓
backend/app/api/documents.py
    ↓
app.services.ingestion.ingest_documents()
    ↓
SimpleDirectoryReader + SentenceSplitter
    ↓
VectorStoreIndex persisted to data/storage/
    ↓
frontend refreshes the document list
```

### Delete a document

```text
frontend/app.js
    ↓
DELETE /api/documents?path={relative_path}
    ↓
backend/app/api/documents.py removes the source file
    ↓
ingestion.py rebuilds the index from remaining documents
    ↓
old persisted node/vector/index data is replaced
    ↓
chat_history.py removes saved source excerpts for that file
    ↓
frontend refreshes the document list
```

### Ask a question

```text
frontend/app.js
    ↓
POST /api/chat
    ↓
backend/app/api/chat.py
    ↓
app.services.rag.chat_question() or ask_question()
    ↓
Hybrid retrieval + reranking + Groq generation
    ↓
answer + sources
    ↓
backend/app/services/chat_history.py writes message to SQLite
    ↓
frontend shows answer and retrieved sources
```

### Rename or delete a conversation

```text
frontend/app.js
    ↓
PATCH or DELETE /api/conversations/{chat_id}
    ↓
backend/app/api/conversations.py
    ↓
chat_history.py updates or removes SQLite rows
    ↓
frontend refreshes the conversation list
```

### Open an old conversation

```text
frontend/app.js
    ↓
GET /api/conversations/{chat_id}
    ↓
backend/app/api/conversations.py
    ↓
chat_history.py reads stored messages
    ↓
frontend renders old message history
```

---

## 5. Why this structure is presentation-friendly

This architecture separates the project into clear layers:

- frontend layer: browser interface
- API layer: HTTP endpoints
- service layer: business logic
- data layer: documents, vector index, and SQLite history

That separation helps explain the project in an interview or presentation as a real enterprise application rather than a collection of random Python scripts.

The important idea is:

- documents are processed once and stored
- the persisted LlamaIndex storage holds retrieval nodes, embeddings, and index metadata
- SQLite keeps the application conversation history
- the frontend simply renders the result of the backend logic

---

## 6. Presentation summary

> This project is an enterprise RAG assistant built with FastAPI, LlamaIndex, and Groq. Uploaded documents are ingested, embedded, and indexed for semantic retrieval. The backend exposes document, chat, and conversation APIs, while SQLite stores persistent chat history so users can resume previous conversations. The frontend calls these APIs, displays retrieved document sources, and keeps the user experience simple and presentation-ready.
