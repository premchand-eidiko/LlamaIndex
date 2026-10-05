"""
Metadata Extraction Module

This module handles metadata extraction and enrichment for documents.

Why we need metadata extraction:
- Metadata enables filtering during retrieval
- Provides context for each document
- Supports access control and authorization
- Enables document-level tracking and auditing

What it does:
- Extracts metadata from file properties
- Enriches metadata with custom fields
- Validates metadata structure
- Ensures metadata consistency

Metadata concept in LlamaIndex:
- Each Document and Node has a metadata dictionary
- Metadata is preserved through the ingestion pipeline
- Metadata can be used for filtering during retrieval
- Metadata is included in source citations
"""

import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
from loguru import logger


class MetadataExtractor:
    """
    Metadata extractor for enriching document metadata.

    Why we need this class:
    - Standardize metadata structure across documents
    - Add enterprise-specific metadata fields
    - Generate unique identifiers
    - Validate metadata completeness

    What it does:
    - Takes basic file metadata
    - Adds enterprise-specific fields
    - Generates document_id
    - Returns enriched metadata dictionary
    """

    def __init__(self):
        """Initialize the metadata extractor."""
        logger.info("Initialized MetadataExtractor")

    def extract_file_metadata(
        self,
        file_path: str,
        extra_metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Extract metadata from a file.

        Why we need this method:
        - Get file properties (size, modification time)
        - Generate unique document_id
        - Add enterprise metadata fields
        - Merge with user-provided metadata

        Args:
            file_path: Path to the file
            extra_metadata: Additional metadata provided by user

        Returns:
            Dictionary with complete metadata

        What happens internally:
        1. Get file properties from filesystem
        2. Generate unique document_id using UUID
        3. Add standard fields (created_at, version)
        4. Merge with extra_metadata
        5. Return complete metadata dictionary

        What is document_id?
        - A unique identifier for each document
        - Generated using UUID4 (random, virtually collision-free)
        - Used to track documents through the pipeline
        - Enables document deletion and updates
        - Required for multi-document querying

        What would happen if we removed this:
        - No unique tracking of documents
        - Difficult to manage document lifecycle
        - No consistent metadata structure
        - Metadata filtering would be unreliable
        """

        file_path_obj = Path(file_path)

        if not file_path_obj.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        # Basic file metadata
        file_stat = file_path_obj.stat()

        metadata = {
            # Unique identifier for the document
            # Why UUID4?
            # - Random and unique
            # - No central coordination needed
            # - Virtually collision-free
            # - Standard for unique IDs
            "document_id": str(uuid.uuid4()),

            # File information
            "file_name": file_path_obj.name,
            "file_path": str(file_path_obj.absolute()),
            "file_type": file_path_obj.suffix[1:] if file_path_obj.suffix else "unknown",
            "file_size": file_stat.st_size,

            # Timestamps
            "created_at": datetime.utcnow().isoformat(),
            "modified_at": datetime.fromtimestamp(file_stat.st_mtime).isoformat(),

            # Document version (can be updated later)
            "version": "1.0",
        }

        # Merge with extra metadata if provided
        # This allows users to add:
        # - department: HR, Finance, Engineering
        # - document_category: policy, handbook, report
        # - access_level: public, internal, confidential
        # - custom fields specific to the organization
        if extra_metadata:
            metadata.update(extra_metadata)

        logger.info(
            f"Extracted metadata for {file_path_obj.name} "
            f"(document_id: {metadata['document_id']})"
        )

        return metadata

    def validate_metadata(self, metadata: Dict[str, Any]) -> bool:
        """
        Validate that required metadata fields are present.

        Why we need this method:
        - Ensure metadata completeness
        - Catch missing required fields early
        - Prevent errors in downstream processing

        Args:
            metadata: Metadata dictionary to validate

        Returns:
            True if valid, raises ValueError if invalid

        What happens internally:
        1. Check for required fields
        2. Validate field types
        3. Return True if all checks pass
        4. Raise ValueError if any check fails
        """

        required_fields = [
            "document_id",
            "file_name",
            "file_type",
            "file_size",
            "created_at",
        ]

        missing_fields = [field for field in required_fields if field not in metadata]

        if missing_fields:
            raise ValueError(
                f"Missing required metadata fields: {missing_fields}"
            )

        # Validate types
        if not isinstance(metadata["document_id"], str):
            raise ValueError("document_id must be a string")

        if not isinstance(metadata["file_name"], str):
            raise ValueError("file_name must be a string")

        if not isinstance(metadata["file_size"], int):
            raise ValueError("file_size must be an integer")

        logger.debug("Metadata validation passed")

        return True

    def get_metadata_filters(
        self,
        metadata: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Extract filterable metadata fields.

        Why we need this method:
        - Identify which metadata fields can be used for filtering
        - Separate filterable from non-filterable fields
        - Prepare metadata for LlamaIndex filter objects

        Args:
            metadata: Complete metadata dictionary

        Returns:
            Dictionary with filterable fields only

        What are filterable fields?
        - Fields used during retrieval to narrow results
        - Examples: department, document_category, access_level
        - Non-filterable: timestamps, file_size, etc.
        """

        filterable_fields = [
            "document_id",
            "file_name",
            "file_type",
            "department",
            "document_category",
            "access_level",
            "version",
        ]

        filters = {
            key: value
            for key, value in metadata.items()
            if key in filterable_fields
        }

        logger.debug(f"Extracted {len(filters)} filterable metadata fields")

        return filters


# Singleton instance
metadata_extractor = MetadataExtractor()
