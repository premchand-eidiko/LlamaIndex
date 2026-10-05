"""
Ingestion Pipeline Module

This module orchestrates the complete document ingestion process.

Why we need an ingestion pipeline:
- Coordinate multiple steps (loading, parsing, metadata)
- Ensure consistent processing across all documents
- Provide a single interface for ingestion
- Enable batch processing of multiple files

What it does:
- Loads documents using DocumentLoader
- Extracts metadata using MetadataExtractor
- Parses documents into nodes using NodeParser
- Returns nodes ready for indexing
- Logs all operations for monitoring

Pipeline concept:
- A pipeline is a sequence of operations
- Each operation transforms the data
- Data flows from one operation to the next
- Operations are modular and reusable
"""

from typing import List, Dict, Any, Optional
from pathlib import Path
from llama_index.core import Document
from loguru import logger

from app.ingestion.loaders import DocumentLoader, document_loader
from app.ingestion.parsers import NodeParser, default_parser
from app.ingestion.metadata import MetadataExtractor, metadata_extractor


class IngestionPipeline:
    """
    Complete ingestion pipeline for processing documents.

    Why we need this class:
    - Orchestrate the entire ingestion process
    - Provide a clean interface for the application
    - Ensure all steps are executed in order
    - Handle errors gracefully

    What it does:
    1. Load documents from files or directories
    2. Extract and enrich metadata
    3. Parse documents into nodes
    4. Return nodes ready for indexing

    Pipeline flow:
    File/Directory → DocumentLoader → Document → MetadataExtractor → Document with metadata → NodeParser → Nodes
    """

    def __init__(
        self,
        loader: Optional[DocumentLoader] = None,
        parser: Optional[NodeParser] = None,
        metadata_extractor_inst: Optional[MetadataExtractor] = None,
    ):
        """
        Initialize the ingestion pipeline.

        Args:
            loader: DocumentLoader instance (uses default if None)
            parser: NodeParser instance (uses default if None)
            metadata_extractor_inst: MetadataExtractor instance (uses default if None)

        Why we allow custom instances:
        - Enables testing with mock objects
        - Allows different configurations
        - Supports dependency injection
        """

        self.loader = loader or document_loader
        self.parser = parser or default_parser
        self.metadata_extractor = metadata_extractor_inst or metadata_extractor

        logger.info("Initialized IngestionPipeline")

    def ingest_file(
        self,
        file_path: str,
        extra_metadata: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> List:
        """
        Ingest a single file through the complete pipeline.

        Why we need this method:
        - Process individual files
        - Useful for incremental ingestion
        - Simple interface for single-file operations

        Args:
            file_path: Path to the file to ingest
            extra_metadata: Additional metadata to add

        Returns:
            List of Node objects ready for indexing

        What happens internally:
        1. Load the file into a Document
        2. Extract file metadata
        3. Merge with extra_metadata
        4. Add metadata to Document
        5. Parse Document into Nodes
        6. Return Nodes

        Pipeline steps in detail:
        Step 1: DocumentLoader.load_file()
        - Reads the file from disk
        - Extracts text content
        - Returns Document object

        Step 2: MetadataExtractor.extract_file_metadata()
        - Gets file properties
        - Generates document_id
        - Returns metadata dictionary

        Step 3: Merge metadata
        - Combines file metadata with extra_metadata
        - User-provided metadata takes precedence

        Step 4: Add metadata to Document
        - Document.metadata = merged_metadata

        Step 5: NodeParser.parse_document()
        - Splits Document into Nodes
        - Each Node inherits Document metadata
        - Returns list of Nodes

        Step 6: Return Nodes
        - Nodes are ready for embedding and indexing
        """

        meta = extra_metadata.copy() if extra_metadata else {}
        meta.update(kwargs)
        extra_metadata = meta

        logger.info(f"Starting ingestion pipeline for file: {file_path}")

        # Step 1: Load the file
        logger.info("Step 1: Loading document")
        doc = self.loader.load_file(file_path)

        # Step 2: Extract metadata
        logger.info("Step 2: Extracting metadata")
        file_metadata = self.metadata_extractor.extract_file_metadata(
            file_path,
            extra_metadata=extra_metadata,
        )

        # Step 3: Merge metadata
        # User-provided metadata overrides file metadata
        if extra_metadata:
            file_metadata.update(extra_metadata)

        # Step 4: Add metadata to document
        doc.metadata = file_metadata

        # Step 5: Parse document into nodes
        logger.info("Step 3: Parsing document into nodes")
        nodes = self.parser.parse_document(doc)

        logger.info(
            f"Ingestion pipeline completed: "
            f"{file_path} → {len(nodes)} nodes"
        )

        return nodes

    def ingest_directory(
        self,
        directory_path: str,
        recursive: bool = False,
        extra_metadata: Optional[Dict[str, Any]] = None,
    ) -> List:
        """
        Ingest all files from a directory.

        Why we need this method:
        - Batch process multiple files
        - Useful for initial bulk ingestion
        - Efficient processing of document collections

        Args:
            directory_path: Path to the directory
            recursive: Whether to search subdirectories
            extra_metadata: Additional metadata to add to all documents

        Returns:
            List of Node objects from all files

        What happens internally:
        1. Load all files from directory
        2. For each file, extract metadata
        3. Parse each file into nodes
        4. Combine all nodes from all files
        5. Return combined list
        """

        logger.info(f"Starting ingestion pipeline for directory: {directory_path}")

        # Step 1: Load all documents from directory
        logger.info("Step 1: Loading documents from directory")
        docs = self.loader.load_directory(
            directory_path,
            recursive=recursive,
            extra_metadata=extra_metadata,
        )

        # Step 2: Parse all documents into nodes
        logger.info("Step 2: Parsing documents into nodes")
        nodes = self.parser.parse_documents(docs)

        logger.info(
            f"Ingestion pipeline completed: "
            f"{directory_path} → {len(docs)} documents → {len(nodes)} nodes"
        )

        return nodes

    def ingest_documents(
        self,
        documents: List[Document],
        extra_metadata: Optional[Dict[str, Any]] = None,
    ) -> List:
        """
        Ingest pre-loaded Document objects.

        Why we need this method:
        - Process documents already loaded elsewhere
        - Useful for web scraping or API ingestion
        - Enables custom loading workflows

        Args:
            documents: List of Document objects
            extra_metadata: Additional metadata to add

        Returns:
            List of Node objects
        """

        logger.info(f"Starting ingestion pipeline for {len(documents)} documents")

        # Add extra metadata to all documents
        if extra_metadata:
            for doc in documents:
                doc.metadata.update(extra_metadata)

        # Parse documents into nodes
        logger.info("Parsing documents into nodes")
        nodes = self.parser.parse_documents(documents)

        logger.info(
            f"Ingestion pipeline completed: "
            f"{len(documents)} documents → {len(nodes)} nodes"
        )

        return nodes


# Singleton instance
ingestion_pipeline = IngestionPipeline()
