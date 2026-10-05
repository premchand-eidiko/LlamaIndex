"""
GraphRAG / Knowledge Graph Module (Phase 14)

This module implements entity-relation extraction and Knowledge Graph querying.

Why we need GraphRAG:
- Vector search retrieves isolated chunks; it struggles with multi-hop relationships
  (e.g., "Person A manages Project B which depends on Database C governed by Policy D").
- GraphRAG builds an explicit knowledge network of entities and relationships.
- Enables associative reasoning and multi-hop relationship exploration across enterprise data.
"""

from typing import List, Dict, Tuple, Set, Optional, Any
from collections import defaultdict
from llama_index.core.schema import Document
from loguru import logger

from app.core.config import settings


class GraphTriplet:
    """Represents a knowledge graph relationship triplet: (subject, relation, object)."""

    def __init__(self, subject: str, relation: str, object_: str):
        self.subject = subject.strip().lower()
        self.relation = relation.strip().lower()
        self.object_ = object_.strip().lower()

    def __repr__(self) -> str:
        return f"({self.subject}) -[{self.relation}]-> ({self.object_})"

    def to_dict(self) -> Dict[str, str]:
        return {
            "subject": self.subject,
            "relation": self.relation,
            "object": self.object_,
        }


class KnowledgeGraphStore:
    """In-memory Knowledge Graph store supporting entity indexing and multi-hop traversal."""

    def __init__(self):
        self.adjacency: Dict[str, List[Tuple[str, str]]] = defaultdict(list)
        self.triplets: List[GraphTriplet] = []
        self.entities: Set[str] = set()

    def add_triplet(self, subject: str, relation: str, object_: str):
        """Add a single triplet to the graph."""
        triplet = GraphTriplet(subject, relation, object_)
        self.triplets.append(triplet)
        self.entities.add(triplet.subject)
        self.entities.add(triplet.object_)
        self.adjacency[triplet.subject].append((triplet.relation, triplet.object_))
        logger.debug(f"Added triplet: {triplet}")

    def get_neighbors(self, entity: str) -> List[Tuple[str, str]]:
        """Retrieve 1-hop outgoing relationships for an entity."""
        return self.adjacency.get(entity.strip().lower(), [])

    def multi_hop_search(self, start_entity: str, max_depth: int = 2) -> List[List[str]]:
        """
        Perform Breadth-First-Search traversal starting from an entity up to max_depth.
        Returns paths of entities and relations.
        """
        start = start_entity.strip().lower()
        if start not in self.entities:
            return []

        paths = []
        queue = [([start], 0)]

        while queue:
            current_path, depth = queue.pop(0)
            current_node = current_path[-1]

            if depth >= max_depth:
                paths.append(current_path)
                continue

            neighbors = self.get_neighbors(current_node)
            if not neighbors:
                paths.append(current_path)
            else:
                for rel, neighbor in neighbors:
                    if neighbor not in current_path:  # Prevent cycles
                        queue.append((current_path + [f"-{rel}->" , neighbor], depth + 1))

        return paths


class KnowledgeGraphManager:
    """Manager for GraphRAG operations, extraction, and graph querying."""

    def __init__(self):
        self.graph_store = KnowledgeGraphStore()
        logger.info(f"Initialized KnowledgeGraphManager (store_type={settings.graph_store_type})")

    def extract_triplets_from_text(self, text: str) -> List[GraphTriplet]:
        """
        Extract entity-relation triplets from text.
        Supports rule-based parsing and connects with LLM when configured.
        """
        logger.info(f"Extracting knowledge graph triplets from text length={len(text)}")
        extracted = []
        # Common structural indicators in enterprise texts
        lines = text.split("\n")
        for line in lines:
            line_str = line.strip()
            if not line_str:
                continue
            if ":" in line_str:
                parts = line_str.split(":", 1)
                subj = parts[0].strip()
                obj = parts[1].strip()
                if subj and obj:
                    triplet = GraphTriplet(subj, "has_property", obj[:50])
                    extracted.append(triplet)
                    self.graph_store.add_triplet(triplet.subject, triplet.relation, triplet.object_)

            # Heuristic for policy / requirement relationships
            keywords_map = {
                "requires": "requires",
                "reports to": "reports_to",
                "manages": "manages",
                "part of": "part_of",
                "allocated to": "allocated_to",
            }
            for kw, rel in keywords_map.items():
                if f" {kw} " in line_str.lower():
                    segments = line_str.lower().split(f" {kw} ", 1)
                    s, o = segments[0].strip(), segments[1].strip()
                    if s and o:
                        triplet = GraphTriplet(s, rel, o[:40])
                        extracted.append(triplet)
                        self.graph_store.add_triplet(triplet.subject, triplet.relation, triplet.object_)

        logger.info(f"Extracted and indexed {len(extracted)} graph triplets")
        return extracted

    def query_graph(self, entity: str, max_depth: int = 2) -> Dict[str, Any]:
        """Query knowledge graph for an entity and its surrounding network."""
        paths = self.graph_store.multi_hop_search(entity, max_depth=max_depth)
        formatted_paths = [" ".join(p) for p in paths]
        return {
            "entity": entity,
            "paths_found": len(formatted_paths),
            "network_subgraph": formatted_paths,
        }


# Global singleton
kg_manager = KnowledgeGraphManager()
