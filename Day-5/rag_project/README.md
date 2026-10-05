# Enterprise RAG Platform (Groq + LlamaIndex + FastAPI)

A complete, full-scale Enterprise Retrieval-Augmented Generation (RAG) platform with a modular **FastAPI Backend** and a glassmorphic **Web Frontend**, powered by **Groq** for high-speed LLM inference and **LlamaIndex** for advanced orchestration.

---

## 📁 Project Architecture

```
rag_project/
├── backend/                  # Full 20-Phase Enterprise RAG FastAPI Platform
│   ├── app/
│   │   ├── api/              # Modular API Routes (Ingestion, Query, Chat, Graph, Admin)
│   │   ├── chat/             # Conversational RAG Engine & Memory Buffer
│   │   ├── core/             # Config, Logging, Exceptions, LLM Factory (Groq/OpenAI), Evaluation
│   │   ├── graph/            # GraphRAG & Knowledge Graph Triplet Extractor
│   │   ├── indexes/          # VectorStoreIndex & StorageContext Persistence
│   │   ├── ingestion/        # Document Loaders, Token-aware Parsers, Metadata Extractor
│   │   ├── query/            # Router, Multi-Doc, HyDE Query Transformation, Streaming
│   │   ├── retrieval/        # Vector, Filter, Hybrid (RRF), Re-ranking, Recursive Retrieval
│   │   ├── schemas/          # Pydantic v2 Models
│   │   └── main.py           # Master FastAPI Application with Lifecycle & Middleware
│   ├── data/                 # Persistent storage (docstore, vector_store, index_store, documents)
│   ├── tests/                # Comprehensive test suite covering all 20 phases
│   ├── .env.example          # Environment template with GROQ_API_KEY support
│   └── requirements.txt      # Python dependencies
│
└── frontend/                 # Interactive Glassmorphic Web UI
    ├── css/style.css         # Dark glassmorphic design system
    ├── js/app.js             # Client API handler, session manager, & Canvas Graph renderer
    ├── index.html            # Single Page Application
    └── server.py             # Lightweight local frontend server (Port 3000)
```

---

## ⚡ How to Run in Separate Terminals

### Step 1: Configure your Groq API Key

```bash
cd backend
cp .env.example .env
```

Open `backend/.env` in your text editor and paste your **Groq API Key**:
```env
GROQ_API_KEY=gsk_your_actual_groq_api_key_here
GROQ_MODEL=llama-3.3-70b-versatile
```

---

### Step 2: Terminal 1 — Start the Backend

In your **first terminal**:

```bash
cd backend
pip install -r requirements.txt
python -m app.main
```

The backend server will start on:
- API Server: **`http://localhost:8000`**
- Interactive Swagger API Documentation: **`http://localhost:8000/docs`**

---

### Step 3: Terminal 2 — Start the Frontend

In your **second terminal**:

```bash
cd frontend
python server.py
```

The frontend web application will start on:
- Web UI: 👉 **`http://localhost:3000`**

---

## 🧪 Verifying All 20 Backend Phases

You can run the full automated verification suite at any time:

```bash
cd backend
python tests/test_all_phases.py
```

All 20 phases will execute sequentially and report verification metrics (Hit Rate, MRR, Faithfulness, Routing, Traversal, and API endpoints).
