"""
Node Parsers Module

This module provides node parsers for chunking documents into smaller pieces.

Why we need node parsers:
- Documents are often too large for effective retrieval
- LLMs have context window limits
- Smaller chunks enable more precise retrieval
- Chunking improves semantic search quality

What they do:
- Split documents into smaller text chunks (nodes)
- Preserve metadata in each node
- Control chunk size and overlap
- Maintain context between chunks

LlamaIndex Node concept:
- A Node is a chunk of text with metadata
- It's smaller than a Document
- Multiple Nodes come from one Document
- Nodes are the units indexed and retrieved
- TextNode is the basic node type
- IndexNode can reference other indexes (for recursive retrieval)
"""

from typing import List, Optional
from llama_index.core import Document
from llama_index.core.node_parser import (
    SentenceSplitter,
    TextSplitter,
    TokenTextSplitter,
)
from loguru import logger


class NodeParser:
    """
    Main node parser class for chunking documents.

    Why we need this class:
    - Provide a unified interface for different parsing strategies
    - Configure chunking parameters (size, overlap)
    - Ensure consistent chunking across the application
    - Log parsing operations

    What it does:
    - Takes Document objects as input
    - Splits them into smaller Node objects
    - Preserves metadata from Documents to Nodes
    - Returns list of Node objects
    """

    def __init__(
        self,
        chunk_size: int = 1024,
        chunk_overlap: int = 200,
        parser_type: str = "sentence",
    ):
        """
        Initialize the node parser with configuration.

        Args:
            chunk_size: Maximum characters per chunk
            chunk_overlap: Number of characters to overlap between chunks
            parser_type: Type of parser (sentence, token, or simple)

        Why these parameters:
        - chunk_size: Controls granularity of retrieval
          - Too small: insufficient context
          - Too large: imprecise retrieval
          - 1024 is a good default for most use cases
        - chunk_overlap: Ensures context continuity
          - Prevents cutting sentences in half
          - Helps retrieval find relevant boundaries
          - 200 is typically 15-20% of chunk_size
        - parser_type: Different splitting strategies
          - sentence: Splits at sentence boundaries (most natural)
          - token: Splits at token boundaries (LLM-aware)
          - simple: Character-based splitting (simplest)
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.parser_type = parser_type

        # Initialize the appropriate parser
        if parser_type == "sentence":
            # SentenceSplitter: Splits at sentence boundaries
            # Why SentenceSplitter?
            # - Most natural way to split text
            # - Preserves semantic meaning
            # - Respects sentence structure
            # - Good for general documents
            self.parser = SentenceSplitter(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                separator=" ",
            )
        elif parser_type == "token":
            # TokenTextSplitter: Splits at token boundaries
            # Why TokenTextSplitter?
            # - Token-aware splitting
            # - Respects LLM token limits
            # - Better for precise token counting
            # - Useful when token limits are critical
            self.parser = TokenTextSplitter(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
            )
        else:
            # TextSplitter: Simple character-based splitting
            # Why TextSplitter?
            # - Simplest approach
            # - Predictable behavior
            # - Good for code or structured text
            self.parser = TextSplitter(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
            )

        logger.info(
            f"Initialized {parser_type} parser "
            f"(chunk_size={chunk_size}, overlap={chunk_overlap})"
        )

    def parse_documents(
        self,
        documents: List[Document],
    ) -> List:
        """
        Parse a list of documents into nodes.

        Why we need this method:
        - Batch process multiple documents
        - Apply consistent chunking strategy
        - Return nodes ready for indexing

        Args:
            documents: List of Document objects to parse

        Returns:
            List of Node objects

        What happens internally:
        1. For each Document, call the parser
        2. Parser splits Document into multiple Nodes
        3. Each Node inherits Document's metadata
        4. Nodes get additional metadata (chunk index, etc.)
        5. Return all Nodes from all Documents

        What is the relationship between Document and Node?
        - Document: The original file (e.g., entire PDF)
        - Node: A chunk of the Document (e.g., one section)
        - One Document → Multiple Nodes
        - Nodes have the same metadata as their parent Document
        - Nodes have additional metadata (chunk_id, chunk_index)

        What would happen if we removed this:
        - Documents would be too large for effective retrieval
        - LLM context window would be exceeded
        - Retrieval would be imprecise
        - Would need to implement chunking manually
        """

        logger.info(f"Parsing {len(documents)} documents")

        all_nodes = []

        for doc in documents:
            # Use the parser to split the document
            # The parser's get_nodes_from_documents method:
            # - Takes a Document as input
            # - Splits it into Nodes based on configuration
            # - Returns a list of Node objects
            # - Preserves metadata from Document to Nodes
            nodes = self.parser.get_nodes_from_documents([doc])

            # Add chunk-specific metadata
            for i, node in enumerate(nodes):
                node.metadata["chunk_id"] = f"{doc.metadata.get('file_name', 'doc')}_{i}"
                node.metadata["chunk_index"] = i
                node.metadata["total_chunks"] = len(nodes)

            all_nodes.extend(nodes)

            logger.info(
                f"Parsed document '{doc.metadata.get('file_name', 'unknown')}' "
                f"into {len(nodes)} nodes"
            )

        logger.info(f"Total nodes created: {len(all_nodes)}")

        return all_nodes

    def parse_document(
        self,
        document: Document,
    ) -> List:
        """
        Parse a single document into nodes.

        Why we need this method:
        - Process individual documents
        - Useful for incremental ingestion
        - Simpler interface for single-file operations

        Args:
            document: Document object to parse

        Returns:
            List of Node objects
        """

        logger.info(f"Parsing document: {document.metadata.get('file_name', 'unknown')}")

        nodes = self.parser.get_nodes_from_documents([document])

        # Add chunk-specific metadata
        for i, node in enumerate(nodes):
            node.metadata["chunk_id"] = f"{document.metadata.get('file_name', 'doc')}_{i}"
            node.metadata["chunk_index"] = i
            node.metadata["total_chunks"] = len(nodes)

        logger.info(f"Created {len(nodes)} nodes from document")

        return nodes


# Singleton instance with default configuration
default_parser = NodeParser(
    chunk_size=1024,
    chunk_overlap=200,
    parser_type="sentence",
)
