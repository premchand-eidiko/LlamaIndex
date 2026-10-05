"""
Hybrid Retrieval Module (Phase 8)

This module implements hybrid retrieval combining dense vector similarity search
with sparse keyword/lexical matching using Reciprocal Rank Fusion (RRF).

Why we need Hybrid Retrieval:
- Dense vector search understands semantics and intent, but can miss exact keyword hits (IDs, product codes, technical terms).
- Sparse search (keyword / BM25) excels at exact matches but lacks semantic awareness.
- Combining both with Reciprocal Rank Fusion (RRF) provides the highest retrieval recall and precision in enterprise environments.
"""

from typing import List, Dict, Optional, Any
from collections import defaultdict
from llama_index.core.retrievers import BaseRetriever
from llama_index.core.schema import NodeWithScore, QueryBundle
from llama_index.core import VectorStoreIndex
from llama_index.core.vector_stores import MetadataFilters
from loguru import logger

from app.core.config import settings


def reciprocal_rank_fusion(
    results_list: List[List[NodeWithScore]],
    k: int = 60,
    top_k: int = 5,
) -> List[NodeWithScore]:
    """
    Combine multiple ranked lists of nodes using Reciprocal Rank Fusion (RRF).

    Formula:
        RRF_Score(d) = sum_{m in rank_lists} (1 / (k + rank_m(d)))

    Args:
        results_list: List of ranked node lists from different retrievers
        k: Smoothing constant (default: 60, standard in IR literature)
        top_k: Final number of nodes to return

    Returns:
        List[NodeWithScore]: Fused and re-ranked list of nodes
    """
    rrf_scores: Dict[str, float] = defaultdict(float)
    node_map: Dict[str, NodeWithScore] = {}

    for ranked_nodes in results_list:
        for rank, node_with_score in enumerate(ranked_nodes, start=1):
            node_id = node_with_score.node.node_id
            node_map[node_id] = node_with_score
            rrf_scores[node_id] += 1.0 / (k + rank)

    # Sort nodes by combined RRF score descending
    sorted_node_ids = sorted(rrf_scores.keys(), key=lambda nid: rrf_scores[nid], reverse=True)

    fused_results: List[NodeWithScore] = []
    for nid in sorted_node_ids[:top_k]:
        original_node = node_map[nid]
        fused_results.append(
            NodeWithScore(
                node=original_node.node,
                score=rrf_scores[nid],
            )
        )

    return fused_results


class HybridRetriever(BaseRetriever):
    """
    Hybrid retriever that combines vector similarity with keyword-based retrieval.
    """

    def __init__(
        self,
        vector_retriever: BaseRetriever,
        nodes: Optional[List] = None,
        top_k: int = 5,
        alpha: float = 0.5,
    ):
        """
        Initialize HybridRetriever.

        Args:
            vector_retriever: Underlying vector retriever
            nodes: Corpus nodes for lexical matching
            top_k: Number of combined nodes to return
            alpha: Weight balancing vector (alpha) and lexical (1 - alpha)
        """
        super().__init__()
        self.vector_retriever = vector_retriever
        self.nodes = nodes or []
        self.top_k = top_k
        self.alpha = alpha
        logger.info(f"Initialized HybridRetriever (top_k={top_k}, alpha={alpha}, corpus_nodes={len(self.nodes)})")

    def _lexical_search(self, query_str: str, top_k: int) -> List[NodeWithScore]:
        """Perform simple term-frequency lexical search over available nodes."""
        query_terms = set(query_str.lower().split())
        scored_nodes = []

        for node in self.nodes:
            text = node.get_content().lower()
            # Simple TF match score based on term occurrences
            score = sum(text.count(term) for term in query_terms if term)
            if score > 0:
                scored_nodes.append(NodeWithScore(node=node, score=float(score)))

        scored_nodes.sort(key=lambda x: x.score or 0.0, reverse=True)
        return scored_nodes[:top_k]

    def _retrieve(self, query_bundle: QueryBundle) -> List[NodeWithScore]:
        """Execute hybrid retrieval combining vector and lexical results."""
        query_str = query_bundle.query_str
        logger.info(f"Executing hybrid retrieval for query: '{query_str}'")

        # 1. Dense vector retrieval
        vector_nodes = self.vector_retriever.retrieve(query_bundle)
        logger.debug(f"Vector retriever returned {len(vector_nodes)} nodes")

        # 2. Sparse / lexical retrieval
        lexical_nodes = self._lexical_search(query_str, top_k=self.top_k * 2)
        logger.debug(f"Lexical search returned {len(lexical_nodes)} nodes")

        # 3. Fuse results using RRF
        combined = reciprocal_rank_fusion(
            results_list=[vector_nodes, lexical_nodes],
            k=60,
            top_k=self.top_k,
        )
        logger.info(f"Hybrid retrieval fused into {len(combined)} final nodes")
        return combined


class HybridRetrieverManager:
    """Manager for setting up and configuring hybrid retrievers."""

    def __init__(self, top_k: Optional[int] = None):
        self.top_k = top_k or settings.similarity_top_k

    def create_hybrid_retriever(
        self,
        index: VectorStoreIndex,
        nodes: Optional[List] = None,
        top_k: Optional[int] = None,
        filters: Optional[MetadataFilters] = None,
        alpha: float = 0.5,
    ) -> HybridRetriever:
        """Create a HybridRetriever from a VectorStoreIndex and document nodes."""
        final_top_k = top_k or self.top_k
        vector_retriever = index.as_retriever(
            similarity_top_k=final_top_k,
            filters=filters,
        )
        return HybridRetriever(
            vector_retriever=vector_retriever,
            nodes=nodes,
            top_k=final_top_k,
            alpha=alpha,
        )


# Global singleton instance
hybrid_retriever_manager = HybridRetrieverManager()
