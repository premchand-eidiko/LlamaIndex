"""
Router Query Engine Module (Phase 12)

This module implements intelligent query routing across multiple specialized query engines.

Why we need Router Query Engine:
- Factual queries ("What is the maximum travel allowance?") require VectorStoreIndex for precise retrieval.
- Comprehensive queries ("Summarize the entire company strategy", "What are all the topics covered?")
  require a SummaryIndex to synthesize across all content.
- The Router Query Engine inspects the incoming query and automatically selects the optimal query engine.
"""

from typing import List, Optional
from llama_index.core import VectorStoreIndex, SummaryIndex, Settings
from llama_index.core.query_engine import RouterQueryEngine
from llama_index.core.selectors import LLMSingleSelector
from llama_index.core.tools import QueryEngineTool, ToolMetadata
from llama_index.core.schema import Document
from loguru import logger


class RouterEngineManager:
    """
    Manager for creating and configuring RouterQueryEngines.
    """

    def __init__(self):
        logger.info("Initialized RouterEngineManager")

    def build_router_query_engine(
        self,
        documents: List[Document],
        vector_index: Optional[VectorStoreIndex] = None,
        summary_index: Optional[SummaryIndex] = None,
    ) -> RouterQueryEngine:
        """
        Build a RouterQueryEngine configured with both Vector and Summary engines.
        """
        logger.info(f"Building router query engine for {len(documents)} documents")

        from app.core.llm import get_llm
        llm = get_llm()
        if llm:
            Settings.llm = llm

        # 1. Vector Index for factual lookups
        if vector_index is None:
            vector_index = VectorStoreIndex.from_documents(documents)
        vector_query_engine = vector_index.as_query_engine(llm=llm, similarity_top_k=3)

        # 2. Summary Index for broad syntheses and summaries
        if summary_index is None:
            summary_index = SummaryIndex.from_documents(documents)
        summary_query_engine = summary_index.as_query_engine(llm=llm, response_mode="tree_summarize")

        # 3. Create Tools
        vector_tool = QueryEngineTool(
            query_engine=vector_query_engine,
            metadata=ToolMetadata(
                name="vector_tool",
                description="Useful for retrieving specific facts, numbers, dates, rules, or details about the documents.",
            ),
        )

        summary_tool = QueryEngineTool(
            query_engine=summary_query_engine,
            metadata=ToolMetadata(
                name="summary_tool",
                description="Useful for high-level summaries, overviews, comparisons, or synthesizing across the entire document set.",
            ),
        )

        # 4. Construct Router
        router_query_engine = RouterQueryEngine(
            selector=LLMSingleSelector.from_defaults(llm=llm),
            query_engine_tools=[vector_tool, summary_tool],
            verbose=True,
        )

        logger.info("Successfully constructed RouterQueryEngine")
        return router_query_engine

    def route_query_rule_based(self, query: str) -> str:
        """
        Rule-based router fallback when LLM is unavailable.
        """
        summary_keywords = ["summarize", "summary", "overview", "main ideas", "all topics", "outline", "brief"]
        q_lower = query.lower()
        for kw in summary_keywords:
            if kw in q_lower:
                return "summary_tool"
        return "vector_tool"


# Global singleton
router_engine_manager = RouterEngineManager()
