"""
Phase 18 Test: Evaluation Framework

This script demonstrates and verifies:
1. Retrieval Hit Rate and MRR (Mean Reciprocal Rank) evaluation
2. Response Faithfulness (hallucination detection)
3. Answer Relevancy
4. Batch benchmark reporting
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from llama_index.core.schema import TextNode, NodeWithScore
from app.core.evaluation import RAGEvaluator, rag_evaluator
from app.core.logging import logger


def test_evaluation():
    """Test RAG retrieval and response evaluation."""
    logger.info("=" * 60)
    logger.info("TESTING PHASE 18: EVALUATION FRAMEWORK")
    logger.info("=" * 60)

    evaluator = RAGEvaluator()

    # 1. Retrieval Hit Rate & MRR test
    n1 = NodeWithScore(node=TextNode(text="Corporate travel policy reimburses meals up to $75/day."), score=0.88)
    n2 = NodeWithScore(node=TextNode(text="Employee health insurance covers medical, dental, and vision."), score=0.72)

    ret_metrics = evaluator.evaluate_retrieval_hit_rate(
        retrieved_nodes=[n1, n2],
        expected_keywords=["reimburses meals", "travel policy"],
    )
    logger.info(f"1. Retrieval Metrics: Hit={ret_metrics['hit']}, MRR={ret_metrics['reciprocal_rank']}")
    assert ret_metrics["hit"] == 1.0
    assert ret_metrics["reciprocal_rank"] == 1.0

    # 2. Faithfulness / Hallucination detection
    faithful_answer = "The travel policy provides a reimbursement for meals up to $75 per day."
    f_result = evaluator.evaluate_faithfulness_heuristic(faithful_answer, [n1])
    logger.info(f"2. Faithfulness Result: Score={f_result['faithfulness_score']}, Faithful={f_result['is_faithful']}")
    assert f_result["is_faithful"] is True

    # 3. Answer Relevancy
    query = "What is the daily meal allowance for travel?"
    r_result = evaluator.evaluate_relevancy_heuristic(query, faithful_answer)
    logger.info(f"3. Relevancy Result: Score={r_result['relevancy_score']}, Relevant={r_result['is_relevant']}")
    assert r_result["is_relevant"] is True

    # 4. Benchmark evaluation across dataset
    benchmark_dataset = [
        {
            "query": query,
            "answer": faithful_answer,
            "retrieved_nodes": [n1, n2],
            "expected_keywords": ["meals"],
        },
        {
            "query": "What benefits are offered?",
            "answer": "Employee health insurance covers medical dental vision.",
            "retrieved_nodes": [n2, n1],
            "expected_keywords": ["health insurance"],
        },
    ]
    summary = evaluator.run_benchmark(benchmark_dataset)
    logger.info(f"4. Batch Benchmark Summary (sample size={summary['sample_size']}):")
    logger.info(f"   - Hit Rate: {summary['hit_rate'] * 100}%")
    logger.info(f"   - Mean Reciprocal Rank (MRR): {summary['mean_reciprocal_rank']}")
    logger.info(f"   - Average Faithfulness: {summary['average_faithfulness']}")

    assert summary["hit_rate"] == 1.0
    logger.info("✅ Phase 18 Evaluation Framework test passed successfully!")


if __name__ == "__main__":
    test_evaluation()
