"""
Query Transformation Module (Phase 10)

This module implements query transformation strategies:
1. HyDE (Hypothetical Document Embeddings)
2. Query Rewriting and Expansion
3. Sub-Question Decomposition
4. Step-Back Querying

Why we need Query Transformation:
- User queries are frequently ambiguous, too brief, or packed with multiple distinct questions.
- Raw query vectors often don't align well with document chunks (queries are questions, chunks are answers).
- HyDE translates a question into a hypothetical answer before retrieval.
- Decomposing multi-part questions allows focused retrieval for each sub-topic.
"""

from typing import List, Optional, Dict, Any
from llama_index.core.indices.query.query_transform.base import BaseQueryTransform
from llama_index.core.schema import QueryBundle
from llama_index.core.llms import LLM
from loguru import logger

from app.core.config import settings


class QueryTransformer:
    """
    Manager for query transformations: HyDE, rewriting, and decomposition.
    """

    def __init__(self, llm: Optional[LLM] = None):
        self.llm = llm
        logger.info("Initialized QueryTransformer")

    def generate_hypothetical_document(self, query: str) -> str:
        """
        HyDE: Generate a hypothetical document/answer to the user query.
        """
        logger.info(f"Generating HyDE document for query: '{query}'")
        if self.llm is not None:
            prompt = (
                f"Please write a passage to answer the question: '{query}'. "
                f"Provide a clear, detailed, factual paragraph."
            )
            response = self.llm.complete(prompt)
            return response.text
        else:
            # Deterministic fallback when LLM is offline
            return f"Hypothetical answer regarding '{query}': Document details policies, rules, and procedures related to this topic."

    def rewrite_query(self, query: str, context: Optional[str] = None) -> str:
        """
        Rewrite and expand ambiguous query with domain context.
        """
        logger.info(f"Rewriting query: '{query}'")
        if self.llm is not None:
            prompt = (
                f"Given the user query: '{query}'"
                + (f" and context: '{context}'" if context else "")
                + "\nRewrite this query to be clear, specific, and optimized for vector search. Return only the rewritten query."
            )
            response = self.llm.complete(prompt)
            return response.text.strip()
        else:
            return f"{query} details policy guidelines overview"

    def decompose_query(self, query: str) -> List[str]:
        """
        Decompose a complex multi-part query into atomic sub-questions.
        """
        logger.info(f"Decomposing query: '{query}'")
        if self.llm is not None:
            prompt = (
                f"Break down the following complex question into 2 to 4 simpler sub-questions:\n"
                f"Question: {query}\n"
                f"Format: Return each sub-question on a new line."
            )
            response = self.llm.complete(prompt)
            lines = [line.strip("- *0123456789. ") for line in response.text.strip().split("\n") if line.strip()]
            return lines if lines else [query]
        else:
            # Rule-based fallback splitting by 'and', 'vs', 'compared to'
            delimiters = [" and ", " vs ", " compared to "]
            sub_q = [query]
            for d in delimiters:
                if d in query.lower():
                    sub_q = [q.strip() for q in query.split(d)]
                    break
            return sub_q if len(sub_q) > 1 else [f"{query} overview", f"{query} specific rules"]


# Global instance
query_transformer = QueryTransformer()
