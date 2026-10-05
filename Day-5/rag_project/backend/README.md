# Enterprise RAG Assistant (Full 20-Phase Implementation)

A production-grade, enterprise-ready Retrieval-Augmented Generation (RAG) platform built with **LlamaIndex**, **FastAPI**, and **Docker**.

---

## 🏗️ 20-Phase Architecture & Implementation Overview

| Phase | Component / Capability | Implementation File | Verification Test |
| :--- | :--- | :--- | :--- |
| **Phase 1** | Project Setup & Config | `app/core/config.py` | `test_all_phases.py` |
| **Phase 2** | Document Ingestion Pipeline | `app/ingestion/loaders.py`, `pipeline.py` | `tests/test_ingestion.py` |
| **Phase 3** | Nodes & Metadata Enrichment | `app/ingestion/parsers.py`, `metadata.py` | `tests/test_ingestion.py` |
| **Phase 4** | Embeddings & VectorStoreIndex | `app/indexes/vector.py` | `tests/test_embeddings.py` |
| **Phase 5** | StorageContext & Persistence | `app/indexes/storage.py` | `tests/test_storage.py` |
| **Phase 6** | Vector Retrieval Layer | `app/retrieval/retriever.py` | `tests/test_retrieval.py` |
| **Phase 7** | Metadata Filtering | `app/retrieval/filters.py` | `tests/test_filters.py` |
| **Phase 8** | Hybrid Retrieval & RRF | `app/retrieval/hybrid.py` | `tests/test_hybrid.py` |
| **Phase 9** | Node Re-ranking & Cutoffs | `app/retrieval/rerank.py` | `tests/test_rerank.py` |
| **Phase 10** | Query Transformation & HyDE | `app/query/transform.py` | `tests/test_transform.py` |
| **Phase 11** | Recursive Retrieval (Parent/Child) | `app/retrieval/recursive.py` | `tests/test_recursive.py` |
| **Phase 12** | Router Query Engine | `app/query/router.py` | `tests/test_router.py` |
| **Phase 13** | Multi-Document Querying | `app/query/multi_doc.py` | `tests/test_multi_doc.py` |
| **Phase 14** | GraphRAG & Knowledge Graph | `app/graph/knowledge_graph.py` | `tests/test_graph.py` |
| **Phase 15** | Conversational RAG & Memory | `app/chat/engine.py` | `tests/test_chat.py` |
| **Phase 16** | Streaming Token Responses | `app/query/streaming.py` | `tests/test_streaming.py` |
| **Phase 17** | Modular FastAPI Platform | `app/main.py`, `app/api/` | `tests/test_api.py` |
| **Phase 18** | RAG Evaluation Framework | `app/core/evaluation.py` | `tests/test_evaluation.py` |
| **Phase 19** | Structured Logging & Errors | `app/core/logging.py`, `exceptions.py`| `tests/test_logging_errors.py` |
| **Phase 20** | Docker & Container Integration | `Dockerfile`, `docker-compose.yml` | `tests/test_docker_integration.py` |

---

## 🚀 Quickstart

### 1. Local Environment Setup

```bash
# Navigate to enterprise_rag directory
cd enterprise_rag

# Install all dependencies
pip install -r requirements.txt

# Configure your environment
cp .env.example .env
# Edit .env and supply your OPENAI_API_KEY
```

### 2. Run the Server Locally

```bash
python -m app.main
```
The interactive Swagger API documentation will be available at:
👉 **`http://localhost:8000/docs`**

---

## 🐳 Docker Deployment (Phase 20)

### Using Docker Directly:

```bash
# Build the Docker image
docker build -t enterprise-rag:latest .

# Run the container with persistent volumes
docker run -d \
  --name enterprise_rag_app \
  -p 8000:8000 \
  -e OPENAI_API_KEY="your-api-key" \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/logs:/app/logs \
  enterprise-rag:latest
```

### Using Docker Compose:

```bash
# Start service in the background
docker compose up -d

# View live container logs
docker compose logs -f

# Check health status
docker compose ps

# Stop container
docker compose down
```

---

## 📡 API Reference & Endpoints

### 1. Document Ingestion
- `POST /api/v1/documents/upload`
  - Upload file (`multipart/form-data`) with optional `department`, `category`, and `access_level`.
- `GET /api/v1/documents`
  - List all stored files with sizes and modification timestamps.

### 2. Retrieval & Querying
- `POST /api/v1/query`
  - Standard RAG query with source citations, similarity score filtering, and metadata filters.
- `POST /api/v1/query/hybrid`
  - Hybrid retrieval combining dense vector similarity with sparse lexical matching using Reciprocal Rank Fusion (RRF).
- `GET /api/v1/query/stream?query=...`
  - Server-Sent Events (SSE) streaming endpoint returning token chunks in real-time.

### 3. Conversational RAG
- `POST /api/v1/chat`
  - Multi-turn conversation with memory buffer (`session_id`), pronoun resolution, and contextual citations.
- `GET /api/v1/chat/sessions/{session_id}`
  - Retrieve dialogue history for a session.
- `DELETE /api/v1/chat/sessions/{session_id}`
  - Reset and clear dialogue memory for a session.

### 4. GraphRAG & Knowledge Graph
- `POST /api/v1/graph/explore`
  - Explore multi-hop relationship networks for an entity (`entity`, `max_depth`).
- `GET /api/v1/graph/triplets`
  - List all extracted entity-relation triplets.

### 5. System & Health
- `GET /health`
  - System health check, index load status, and document counts.
- `DELETE /admin/clear`
  - Clear all persistent vector stores, document stores, and raw files.

---

## 🧪 Running the Verification Test Suite

To verify all 20 phases at once with automated assertions:

```bash
python tests/test_all_phases.py
```

To run individual phase tests:

```bash
python tests/test_ingestion.py          # Phase 2 & 3
python tests/test_embeddings.py         # Phase 4
python tests/test_storage.py            # Phase 5
python tests/test_retrieval.py          # Phase 6
python tests/test_filters.py            # Phase 7
python tests/test_hybrid.py             # Phase 8
python tests/test_rerank.py             # Phase 9
python tests/test_transform.py          # Phase 10
python tests/test_recursive.py          # Phase 11
python tests/test_router.py             # Phase 12
python tests/test_multi_doc.py          # Phase 13
python tests/test_graph.py              # Phase 14
python tests/test_chat.py               # Phase 15
python tests/test_streaming.py          # Phase 16
python tests/test_api.py                # Phase 17
python tests/test_evaluation.py         # Phase 18
python tests/test_logging_errors.py     # Phase 19
python tests/test_docker_integration.py # Phase 20
```

---

## 🛡️ License

MIT License - Production ready for enterprise deployment.
