# Enterprise RAG Assistant - Frontend Web UI

A modern, glassmorphic dark-mode web interface built for the Enterprise RAG Assistant.

## Features
- 💬 **Conversational Chat Workspace**: Multi-turn dialogue with memory buffer, session switching, and citation badges.
- 🔍 **Hybrid Search & Retrieval**: Dense vector search + Sparse keyword BM25 with Reciprocal Rank Fusion (RRF), department filters, and top-K tuning.
- 📄 **Document Management**: Drag-and-drop file ingestion (PDF, DOCX, TXT, CSV, JSON, MD) with real-time indexing status.
- 🕸️ **GraphRAG Explorer**: Interactive HTML5 Canvas Knowledge Graph visualizer and multi-hop relationship traversal.
- 📊 **Metrics & KPI Dashboard**: Live retrieval hit rate, MRR, and faithfulness indicators.

## Running the Frontend

In your terminal:
```bash
cd frontend
python server.py
```

Then open your browser at:
👉 **`http://localhost:3000`**

(It automatically connects to the backend API running on `http://localhost:8000`).
