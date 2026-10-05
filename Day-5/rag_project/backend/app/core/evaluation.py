"""
Evaluation Framework Module (Phase 18)

This module implements automated evaluation for the Enterprise RAG system:
1. Retrieval Metrics: Hit Rate, MRR (Mean Reciprocal Rank)
2. Response Metrics: Faithfulness (hallucination detection), Answer Relevancy
3. Batch evaluation across enterprise benchmark datasets.
"""

from typing import List, Dict, Any, Optional
from llama_index.core.schema import NodeWithScore
from llama_index.core.evaluation import FaithfulnessEvaluator, RelevancyEvaluator
from loguru import logger


class RAGEvaluator:
    """
    Evaluates both retrieval quality and response generation quality.
    """

    def __init__(self, llm: Optional[Any] = None):
        self.llm = llm
        logger.info("Initialized RAGEvaluator")

    def evaluate_retrieval_hit_rate(
        self,
        retrieved_nodes: List[NodeWithScore],
        expected_keywords: List[str],
    ) -> Dict[str, float]:
        """
        Evaluate if expected ground truth keywords/concepts were retrieved in top-K.

        Returns:
            Dict containing hit (1.0 or 0.0) and reciprocal_rank (1 / rank)
        """
        hit = 0.0
        reciprocal_rank = 0.0

        for rank, n in enumerate(retrieved_nodes, start=1):
            text = n.node.get_content().lower()
            if any(kw.lower() in text for kw in expected_keywords):
                hit = 1.0
                reciprocal_rank = 1.0 / rank
                break

        return {
            "hit": hit,
            "reciprocal_rank": reciprocal_rank,
            "nodes_checked": len(retrieved_nodes),
        }

    def evaluate_faithfulness_heuristic(
        self,
        answer: str,
        context_nodes: List[NodeWithScore],
    ) -> Dict[str, Any]:
        """
        Heuristic or LLM-based hallucination detection.
        Checks what fraction of key terms in the answer are supported in retrieved context.
        """
        combined_context = " ".join([n.node.get_content().lower() for n in context_nodes])
        words = [w.strip(".,;:?!()[]\"'") for w in answer.lower().split() if len(w) > 3]

        if not words:
            return {"faithfulness_score": 1.0, "is_faithful": True}

        # Check exact word match or stem/root match (>4 chars)
        supported = 0
        for w in words:
            if w in combined_context or (len(w) >= 5 and w[:4] in combined_context):
                supported += 1

        score = supported / len(words)
        is_faithful = score >= 0.60
        return {
            "faithfulness_score": round(score, 3),
            "is_faithful": is_faithful,
            "supported_terms": supported,
            "total_terms": len(words),
        }

    def evaluate_relevancy_heuristic(
        self,
        query: str,
        answer: str,
    ) -> Dict[str, Any]:
        """
        Evaluates semantic overlap between query and generated response.
        """
        stop_words = {"what", "which", "where", "when", "how", "does", "with", "from", "that", "this", "have"}
        q_terms = [
            t.lower().strip(".,;:?!")
            for t in query.split()
            if len(t) > 3 and t.lower() not in stop_words
        ]
        if not q_terms:
            return {"relevancy_score": 1.0, "is_relevant": True}

        a_lower = answer.lower()
        matched = 0
        for t in q_terms:
            if t in a_lower or t[:4] in a_lower or (len(t) >= 4 and t[:3] in a_lower):
                matched += 1

        score = matched / len(q_terms)
        return {
            "relevancy_score": round(score, 3),
            "is_relevant": score >= 0.5,
        }

    def run_benchmark(self, test_cases: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Run evaluation across multiple benchmark test cases.
        """
        total_hits = 0.0
        total_mrr = 0.0
        total_faithfulness = 0.0

        for tc in test_cases:
            nodes = tc.get("retrieved_nodes", [])
            expected = tc.get("expected_keywords", [])
            ret_metrics = self.evaluate_retrieval_hit_rate(nodes, expected)
            total_hits += ret_metrics["hit"]
            total_mrr += ret_metrics["reciprocal_rank"]

            if "answer" in tc and nodes:
                f_metrics = self.evaluate_faithfulness_heuristic(tc["answer"], nodes)
                total_faithfulness += f_metrics["faithfulness_score"]

        count = len(test_cases)
        return {
            "sample_size": count,
            "hit_rate": round(total_hits / count, 3) if count else 0.0,
            "mean_reciprocal_rank": round(total_mrr / count, 3) if count else 0.0,
            "average_faithfulness": round(total_faithfulness / count, 3) if count else 0.0,
        }


# Global instance
rag_evaluator = RAGEvaluator()
