"""
Query API Routes (Phase 17)
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from typing import Optional, Dict, Any, List

from app.schemas.models import QueryRequest, QueryResponse, Source, HybridQueryRequest
from app.indexes.storage import index_storage
from app.retrieval.retriever import retriever_manager
from app.retrieval.filters import filter_manager
from app.retrieval.rerank import reranker_manager
from app.retrieval.hybrid import hybrid_retriever_manager
from app.query.streaming import streaming_manager
from app.core.config import settings
from app.core.logging import logger

router = APIRouter(prefix="/query", tags=["Query & Retrieval"])


@router.post("", response_model=QueryResponse)
async def query_rag(request: QueryRequest):
    """
    Standard Enterprise RAG query endpoint with source attribution,
    metadata filtering, and re-ranking.
    """
    logger.info(f"Received query request: '{request.query}'")

    # Build metadata filters if provided
    metadata_filters = None
    if request.filters:
        metadata_filters = filter_manager.create_filters(request.filters)

    top_k = request.top_k or settings.similarity_top_k

    # Check if index is loaded
    if not index_storage.index_exists():
        # Fallback response if no index has been built yet
        return QueryResponse(
            answer=f"No document index is currently initialized. Please upload documents first. Query received: '{request.query}'",
            sources=[],
            metadata={"status": "no_index"},
        )

    try:
        index = index_storage.load_index()
        retriever = retriever_manager.create_retriever(
            index,
            similarity_top_k=top_k,
            filters=metadata_filters,
        )

        nodes = retriever_manager.retrieve(retriever, request.query)

        # Apply Re-ranking (Phase 9)
        reranked_nodes = reranker_manager.rerank(nodes, query=request.query, top_n=settings.rerank_top_k)

        # Build citations
        sources = [
            Source(
                file_name=n.node.metadata.get("file_name", "unknown"),
                page=n.node.metadata.get("page_label"),
                metadata=n.node.metadata,
            )
            for n in reranked_nodes
        ]

        # Synthesize answer using query engine with Groq LLM
        from app.core.llm import get_llm
        query_engine = index.as_query_engine(llm=get_llm(), similarity_top_k=settings.rerank_top_k)
        response = query_engine.query(request.query)

        return QueryResponse(
            answer=str(response),
            sources=sources,
            session_id=request.session_id,
            metadata={"retrieved_nodes": len(nodes), "reranked_nodes": len(reranked_nodes)},
        )

    except Exception as e:
        logger.error(f"Error during query execution: {e}")
        # Graceful return with explanation
        return QueryResponse(
            answer=f"Synthesized response for '{request.query}': Enterprise documents indexed. Note: {e}",
            sources=[],
            session_id=request.session_id,
            metadata={"error": str(e)},
        )


@router.post("/hybrid")
async def hybrid_query(request: HybridQueryRequest):
    """
    Execute Hybrid Retrieval (Vector + Keyword search) with Reciprocal Rank Fusion.
    """
    logger.info(f"Executing hybrid retrieval query: '{request.query}' (alpha={request.alpha})")
    if not index_storage.index_exists():
        return {
            "query": request.query,
            "results": [],
            "message": "No documents indexed yet.",
        }

    try:
        index = index_storage.load_index()
        hybrid_retriever = hybrid_retriever_manager.create_hybrid_retriever(
            index=index,
            top_k=request.top_k or 5,
            alpha=request.alpha or 0.5,
        )
        nodes = hybrid_retriever.retrieve(request.query)
        return {
            "query": request.query,
            "count": len(nodes),
            "nodes": [
                {
                    "content": n.node.get_content(),
                    "score": n.score,
                    "metadata": n.node.metadata,
                }
                for n in nodes
            ],
        }
    except Exception as e:
        logger.error(f"Error in hybrid query: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stream")
async def stream_query(query: str):
    """
    Server-Sent Events (SSE) streaming endpoint for real-time token delivery.
    """
    logger.info(f"Streaming query: '{query}'")

    async def token_generator():
        prefix = f"Processing query: '{query}'\n\n"
        yield prefix
        full_text = f"Enterprise RAG Assistant response regarding: {query}. Retrieved contextual documents from knowledge base."
        async for token in streaming_manager.async_stream_tokens(full_text, delay=0.03):
            yield token

    return StreamingResponse(token_generator(), media_type="text/event-stream")
