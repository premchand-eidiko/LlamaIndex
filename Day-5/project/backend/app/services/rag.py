from typing import Optional


from llama_index.core import (
    QueryBundle,
    StorageContext,
    SummaryIndex,
    VectorStoreIndex,
    load_index_from_storage,
)

from llama_index.core.chat_engine import (
    ContextChatEngine,
)

from llama_index.core.postprocessor import (
    SentenceTransformerRerank,
)

from llama_index.core.query_engine import (
    RetrieverQueryEngine,
    RouterQueryEngine,
)

from llama_index.core.retrievers import (
    QueryFusionRetriever,
    TransformRetriever,
    VectorIndexRetriever,
)

from llama_index.core.selectors import (
    LLMSingleSelector,
)

from llama_index.core.settings import Settings

from llama_index.core.tools import (
    QueryEngineTool,
)

from llama_index.core.vector_stores import (
    MetadataFilter,
    MetadataFilters,
)

from llama_index.embeddings.huggingface import (
    HuggingFaceEmbedding,
)

from llama_index.llms.groq import (
    Groq,
)

from llama_index.retrievers.bm25 import (
    BM25Retriever,
)


from llama_index.core.indices.query.query_transform import (
    HyDEQueryTransform,
)


from app.config import (
    EMBEDDING_MODEL,
    GROQ_API_KEY,
    HYBRID_TOP_K,
    LLM_MODEL,
    RERANKER_MODEL,
    RERANK_TOP_N,
    SIMILARITY_TOP_K,
    STORAGE_DIR,
)


# ==================================================
# LLM
# ==================================================

Settings.llm = Groq(
    model=LLM_MODEL,
    api_key=GROQ_API_KEY,
)


# ==================================================
# Embedding Model
# ==================================================

Settings.embed_model = HuggingFaceEmbedding(
    model_name=EMBEDDING_MODEL,
)


# ==================================================
# Global State
# ==================================================

_index: Optional[VectorStoreIndex] = None

_chat_engines = {}


# ==================================================
# Load Vector Index
# ==================================================

def get_index() -> VectorStoreIndex:

    global _index


    if _index is not None:

        return _index


    if not STORAGE_DIR.exists():

        raise RuntimeError(
            "Storage directory does not exist."
        )


    try:

        storage_context = (
            StorageContext.from_defaults(
                persist_dir=str(STORAGE_DIR)
            )
        )


        _index = load_index_from_storage(
            storage_context
        )


        return _index


    except Exception as exc:

        raise RuntimeError(
            "No valid RAG index found. "
            "Upload a document first."
        ) from exc


# ==================================================
# Reset
# ==================================================

def reset_index() -> None:

    global _index

    _index = None

    _chat_engines.clear()


# ==================================================
# Get All Nodes
# ==================================================

def get_all_nodes():

    index = get_index()

    return list(
        index.docstore.docs.values()
    )


# ==================================================
# Metadata Filter
# ==================================================

def build_metadata_filters(
    file_name: Optional[str] = None,
):

    if not file_name:

        return None


    return MetadataFilters(
        filters=[
            MetadataFilter(
                key="file_name",
                value=file_name,
            )
        ]
    )


# ==================================================
# Get Filtered Nodes
# ==================================================

def get_filtered_nodes(
    file_name: Optional[str] = None,
):

    nodes = get_all_nodes()


    if not file_name:

        return nodes


    filtered_nodes = []


    for node in nodes:

        node_file_name = node.metadata.get(
            "file_name"
        )


        if node_file_name == file_name:

            filtered_nodes.append(node)


    return filtered_nodes


# ==================================================
# Hybrid Retriever
# ==================================================

def build_hybrid_retriever(
    file_name: Optional[str] = None,
):

    index = get_index()


    # --------------------------------------------------
    # Metadata Filter
    # --------------------------------------------------

    filters = build_metadata_filters(
        file_name
    )


    # --------------------------------------------------
    # Vector Retriever
    # --------------------------------------------------

    vector_retriever = VectorIndexRetriever(
        index=index,

        similarity_top_k=HYBRID_TOP_K,

        filters=filters,
    )


    # --------------------------------------------------
    # Nodes for BM25
    # --------------------------------------------------

    bm25_nodes = get_filtered_nodes(
        file_name
    )


    if not bm25_nodes:

        raise ValueError(
            f"No nodes found for document: {file_name}"
        )


    # --------------------------------------------------
    # BM25 Retriever
    # --------------------------------------------------

    bm25_retriever = BM25Retriever.from_defaults(
        nodes=bm25_nodes,

        similarity_top_k=HYBRID_TOP_K,
    )


    # --------------------------------------------------
    # Hybrid Retrieval
    # --------------------------------------------------

    hybrid_retriever = QueryFusionRetriever(

        [
            vector_retriever,
            bm25_retriever,
        ],

        similarity_top_k=HYBRID_TOP_K,

        num_queries=1,

        mode="reciprocal_rerank",

        use_async=False,

        verbose=False,

        llm=Settings.llm,
    )


    return hybrid_retriever


# ==================================================
# Query Transformation
# ==================================================

def build_transformed_retriever(
    file_name: Optional[str] = None,
):

    hybrid_retriever = (
        build_hybrid_retriever(
            file_name
        )
    )


    # --------------------------------------------------
    # HyDE
    # --------------------------------------------------

    hyde = HyDEQueryTransform(
        include_original=True
    )


    transformed_retriever = TransformRetriever(

        retriever=hybrid_retriever,

        query_transform=hyde,
    )


    return transformed_retriever


# ==================================================
# Reranker
# ==================================================

def build_reranker():

    return SentenceTransformerRerank(

        model=RERANKER_MODEL,

        top_n=RERANK_TOP_N,

    )


# ==================================================
# Document Query Engine
# ==================================================

def build_document_query_engine(
    file_name: Optional[str] = None,
):

    retriever = (
        build_transformed_retriever(
            file_name
        )
    )


    reranker = build_reranker()


    query_engine = (
        RetrieverQueryEngine.from_args(

            retriever=retriever,

            llm=Settings.llm,

            node_postprocessors=[
                reranker
            ],
        )
    )


    return query_engine


# ==================================================
# Summary Query Engine
# ==================================================

def build_summary_query_engine(
    file_name: Optional[str] = None,
):

    nodes = get_filtered_nodes(
        file_name
    )


    if not nodes:

        raise ValueError(
            "No documents available for summary."
        )


    summary_index = SummaryIndex(
        nodes
    )


    summary_query_engine = (
        summary_index.as_query_engine(

            response_mode="tree_summarize",

            llm=Settings.llm,
        )
    )


    return summary_query_engine


# ==================================================
# Router Query Engine
# ==================================================

def build_router_query_engine(
    file_name: Optional[str] = None,
):

    document_query_engine = (
        build_document_query_engine(
            file_name
        )
    )


    summary_query_engine = (
        build_summary_query_engine(
            file_name
        )
    )


    # --------------------------------------------------
    # Document QA Tool
    # --------------------------------------------------

    document_tool = (
        QueryEngineTool.from_defaults(

            query_engine=document_query_engine,

            name="document_qa",

            description=(
                "Use this tool when the user asks "
                "a specific question about information "
                "contained in the documents."
            ),
        )
    )


    # --------------------------------------------------
    # Summary Tool
    # --------------------------------------------------

    summary_tool = (
        QueryEngineTool.from_defaults(

            query_engine=summary_query_engine,

            name="document_summary",

            description=(
                "Use this tool when the user asks "
                "for a summary, overview, key points, "
                "or a broad explanation of the documents."
            ),
        )
    )


    # --------------------------------------------------
    # Router
    # --------------------------------------------------

    router = RouterQueryEngine.from_defaults(

        query_engine_tools=[
            document_tool,
            summary_tool,
        ],

        selector=LLMSingleSelector.from_defaults(),

        llm=Settings.llm,

        verbose=False,
    )


    return router


# ==================================================
# Normal Question
# ==================================================

def ask_question(
    question: str,
    file_name: Optional[str] = None,
) -> dict:

    router = build_router_query_engine(
        file_name
    )


    response = router.query(
        question
    )


    sources = []


    for node_with_score in (
        response.source_nodes
    ):

        node = node_with_score.node


        sources.append(
            {
                "file_name": node.metadata.get(
                    "file_name",
                    "Unknown",
                ),

                "text": node.text,
            }
        )


    return {
        "answer": str(response),

        "sources": sources,
    }


# ==================================================
# Chat Engine
# ==================================================

def get_chat_engine(
    session_id: str,
    file_name: Optional[str] = None,
):

    cache_key = (
        f"{session_id}:{file_name or '__all__'}"
    )


    if cache_key in _chat_engines:

        return _chat_engines[
            cache_key
        ]


    retriever = (
        build_transformed_retriever(
            file_name
        )
    )


    reranker = build_reranker()


    chat_engine = ContextChatEngine.from_defaults(

        retriever=retriever,

        llm=Settings.llm,

        node_postprocessors=[
            reranker
        ],

        system_prompt=(
            "You are an enterprise document assistant. "
            "Answer using the retrieved document context. "
            "If the information is not present in the "
            "retrieved documents, clearly say that the "
            "information was not found in the documents."
        ),
    )


    _chat_engines[
        cache_key
    ] = chat_engine


    return chat_engine


# ==================================================
# Chat Question
# ==================================================

def chat_question(
    question: str,

    session_id: str,

    file_name: Optional[str] = None,
) -> dict:

    chat_engine = get_chat_engine(

        session_id=session_id,

        file_name=file_name,
    )


    response = chat_engine.chat(
        question
    )


    sources = []


    for node_with_score in (
        response.source_nodes
    ):

        node = node_with_score.node


        sources.append(
            {
                "file_name": node.metadata.get(
                    "file_name",
                    "Unknown",
                ),

                "text": node.text,
            }
        )


    return {
        "answer": str(response),

        "sources": sources,
    }


# ==================================================
# Reset Chat Session
# ==================================================

def reset_chat_session(
    session_id: str,
):

    keys_to_remove = []


    for key in _chat_engines:

        if key.startswith(
            f"{session_id}:"
        ):

            keys_to_remove.append(key)


    for key in keys_to_remove:

        del _chat_engines[key]