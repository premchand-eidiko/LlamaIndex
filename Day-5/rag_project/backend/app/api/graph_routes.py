"""
GraphRAG API Routes (Phase 17)
"""

from fastapi import APIRouter
from app.graph.knowledge_graph import kg_manager
from app.schemas.models import GraphExploreRequest, GraphExploreResponse
from app.core.logging import logger

router = APIRouter(prefix="/graph", tags=["GraphRAG / Knowledge Graph"])


@router.post("/explore", response_model=GraphExploreResponse)
async def explore_graph(request: GraphExploreRequest):
    """
    Explore multi-hop relations starting from an entity in the Knowledge Graph.
    """
    logger.info(f"Exploring knowledge graph for entity: '{request.entity}' (max_depth={request.max_depth})")
    result = kg_manager.query_graph(request.entity, max_depth=request.max_depth or 2)
    return GraphExploreResponse(
        entity=result["entity"],
        paths_found=result["paths_found"],
        network_subgraph=result["network_subgraph"],
    )


@router.get("/triplets")
async def get_triplets():
    """List all extracted entity-relation triplets in the graph."""
    return {
        "triplet_count": len(kg_manager.graph_store.triplets),
        "entities": list(kg_manager.graph_store.entities),
        "triplets": [t.to_dict() for t in kg_manager.graph_store.triplets],
    }
