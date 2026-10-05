"""
Re-ranking Module (Phase 9)

This module implements re-ranking using NodePostprocessor in LlamaIndex.

Why we need Re-ranking:
- First-stage retrieval retrieves top-K candidates (e.g., K=10 or 20) with high recall.
- Vector distance doesn't always reflect nuanced semantic relevance or answer quality.
- Re-ranking computes deep cross-attention or score-based filtering to select the top 3-5 nodes.
- Significantly reduces hallucinations and prompt token waste.
"""

from typing import List, Optional
from pydantic import Field
from llama_index.core.postprocessor.types import BaseNodePostprocessor
from llama_index.core.schema import NodeWithScore, QueryBundle
from loguru import logger

from app.core.config import settings


class EnterpriseReranker(BaseNodePostprocessor):
    """
    Enterprise re-ranking component that filters and sorts retrieved nodes.
    Supports minimum score thresholding, top-N truncation, and score-based sorting.
    """

    top_n: int = Field(default_factory=lambda: settings.rerank_top_k)
    similarity_cutoff: Optional[float] = Field(default=None)

    def _postprocess_nodes(
        self,
        nodes: List[NodeWithScore],
        query_bundle: Optional[QueryBundle] = None,
    ) -> List[NodeWithScore]:
        """
        Filter and re-rank nodes based on score and top-N cutoff.
        """
        logger.info(f"Re-ranking {len(nodes)} input nodes (target top_n={self.top_n})")

        filtered_nodes = nodes
        if self.similarity_cutoff is not None:
            filtered_nodes = [
                n for n in nodes if n.score is not None and n.score >= self.similarity_cutoff
            ]
            logger.debug(f"Filtered {len(nodes) - len(filtered_nodes)} nodes below cutoff {self.similarity_cutoff}")

        # Sort descending by score
        sorted_nodes = sorted(
            filtered_nodes,
            key=lambda x: x.score if x.score is not None else 0.0,
            reverse=True,
        )

        final_nodes = sorted_nodes[: self.top_n]
        logger.info(f"Final re-ranked output: {len(final_nodes)} nodes")
        return final_nodes


class RerankerManager:
    """Manager for configuring and running re-rankers."""

    def __init__(self, default_top_n: Optional[int] = None):
        self.default_top_n = default_top_n or settings.rerank_top_k

    def create_reranker(
        self,
        top_n: Optional[int] = None,
        similarity_cutoff: Optional[float] = None,
    ) -> EnterpriseReranker:
        """Create an EnterpriseReranker instance."""
        return EnterpriseReranker(
            top_n=top_n if top_n is not None else self.default_top_n,
            similarity_cutoff=similarity_cutoff,
        )

    def rerank(
        self,
        nodes: List[NodeWithScore],
        query: str,
        top_n: Optional[int] = None,
        similarity_cutoff: Optional[float] = None,
    ) -> List[NodeWithScore]:
        """Convenience method to execute re-ranking on a list of nodes."""
        reranker = self.create_reranker(top_n=top_n, similarity_cutoff=similarity_cutoff)
        query_bundle = QueryBundle(query_str=query)
        return reranker.postprocess_nodes(nodes, query_bundle=query_bundle)


# Global singleton instance
reranker_manager = RerankerManager()
