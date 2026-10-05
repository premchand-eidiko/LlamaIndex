"""
Document Loaders Module

This module provides document loaders for various file formats.

Why we need document loaders:
- Convert different file formats into a unified Document object
- Extract text content from PDFs, DOCX, HTML, etc.
- Preserve metadata from the original files
- Handle encoding and parsing complexities

What they do:
- Read files from disk or URLs
- Extract text content
- Extract metadata (filename, file type, page numbers, etc.)
- Return LlamaIndex Document objects

LlamaIndex Document concept:
- A Document is a container for text and metadata
- It has a `text` field containing the content
- It has a `metadata` dictionary for additional information
- Documents are the input to node parsing and indexing
"""

from pathlib import Path
from typing import List, Optional, Dict, Any
from llama_index.core import Document
from llama_index.core.readers import SimpleDirectoryReader
from llama_index.readers.file import (
    PDFReader,
    DocxReader,
    PyMuPDFReader,
)
try:
    from llama_index.readers.file import UnstructuredReader
except ImportError:
    UnstructuredReader = None
try:
    from llama_index.readers.web import SimpleWebPageReader
except ImportError:
    SimpleWebPageReader = None
from loguru import logger

# Supported file types
SUPPORTED_EXTENSIONS = {
    ".pdf",
    ".docx",
    ".txt",
    ".csv",
    ".md",
    ".json",
}


class DocumentLoader:
    """
    Main document loader class that handles multiple file formats.

    Why we need this class:
    - Provide a unified interface for loading different file types
    - Handle file format detection automatically
    - Apply appropriate loader based on file extension
    - Log ingestion operations for monitoring

    What it does:
    - Detects file type from extension
    - Selects appropriate LlamaIndex reader
    - Loads documents and returns Document objects
    - Extracts and preserves metadata
    """

    def __init__(self):
        """
        Initialize the document loader with appropriate readers.

        Why we need specific readers:
        - PDF: Requires PDF parsing libraries (pypdf, PyMuPDF)
        - DOCX: Requires python-docx for Word documents
        - HTML: Requires BeautifulSoup for web pages
        - Each format has different structure and metadata
        """
        self.readers = {
            ".pdf": PyMuPDFReader(),
            ".docx": DocxReader(),
        }

        # Only add HTML support if unstructured is installed
        try:
            if UnstructuredReader is not None:
                test_reader = UnstructuredReader()
                self.readers[".html"] = test_reader
                self.readers[".htm"] = test_reader
        except ImportError:
            logger.warning("Unstructured not installed. HTML support disabled.")
            logger.warning("Install with: pip install -U unstructured")

    def load_file(
        self,
        file_path: str,
        extra_metadata: Optional[Dict[str, Any]] = None
    ) -> Document:
        """
        Load a single file and return a Document object.

        Why we need this method:
        - Load individual files on-demand
        - Add custom metadata (department, category, etc.)
        - Handle errors gracefully

        Args:
            file_path: Path to the file to load
            extra_metadata: Additional metadata to add to the document

        Returns:
            Document: LlamaIndex Document object with text and metadata

        What happens internally:
        1. Check if file exists
        2. Determine file type from extension
        3. Select appropriate reader
        4. Load the file
        5. Extract file metadata (name, size, type)
        6. Merge with extra_metadata
        7. Return Document object

        What would happen if we removed it:
        - No way to load individual files
        - Would need to implement loading logic elsewhere
        - Inconsistent metadata handling
        """

        file_path_obj = Path(file_path)

        if not file_path_obj.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        # Get file extension
        extension = file_path_obj.suffix.lower()

        if extension not in SUPPORTED_EXTENSIONS:
            raise ValueError(
                f"Unsupported file type: {extension}. "
                f"Supported types: {SUPPORTED_EXTENSIONS}"
            )

        logger.info(f"Loading file: {file_path_obj.name} ({extension})")

        # For text-based files, read directly
        if extension in {".txt", ".md", ".json", ".csv"}:
            with open(file_path_obj, "r", encoding="utf-8") as f:
                text = f.read()

            doc = Document(text=text)

        # For PDF and DOCX, use LlamaIndex readers
        elif extension in {".pdf", ".docx"}:
            reader = self.readers.get(extension)
            if reader is None:
                raise ValueError(f"No reader available for {extension}")

            docs = reader.load_data(file_path)
            if not docs:
                raise ValueError(f"Failed to load {file_path}")

            # Combine multiple pages into one document
            doc = Document(text="\n\n".join([d.text for d in docs]))

        # For HTML, use UnstructuredReader if available
        elif extension in {".html", ".htm"}:
            if UnstructuredReader is None:
                raise ValueError(
                    "HTML support requires llama-index-readers-file with unstructured. "
                    "Install it with: pip install llama-index-readers-file[unstructured]"
                )

            reader = self.readers.get(extension)
            if reader is None:
                raise ValueError(f"No reader available for {extension}")

            docs = reader.load_data(file_path)
            if not docs:
                raise ValueError(f"Failed to load {file_path}")

            doc = Document(text="\n\n".join([d.text for d in docs]))

        else:
            raise ValueError(f"Unsupported file type: {extension}")

        # Add file metadata
        file_metadata = {
            "file_name": file_path_obj.name,
            "file_path": str(file_path_obj.absolute()),
            "file_type": extension[1:],  # Remove the dot
            "file_size": file_path_obj.stat().st_size,
        }

        # Merge with extra metadata
        if extra_metadata:
            file_metadata.update(extra_metadata)

        doc.metadata = file_metadata

        logger.info(
            f"Successfully loaded {file_path_obj.name} "
            f"({len(doc.text)} characters)"
        )

        return doc

    def load_directory(
        self,
        directory_path: str,
        recursive: bool = False,
        extra_metadata: Optional[Dict[str, Any]] = None
    ) -> List[Document]:
        """
        Load all supported files from a directory.

        Why we need this method:
        - Batch load multiple documents at once
        - Useful for initial bulk ingestion
        - SimpleDirectoryReader handles format detection

        Args:
            directory_path: Path to the directory
            recursive: Whether to search subdirectories
            extra_metadata: Additional metadata to add to all documents

        Returns:
            List[Document]: List of loaded Document objects

        What happens internally:
        1. Use SimpleDirectoryReader to load all files
        2. SimpleDirectoryReader automatically detects file types
        3. Returns list of Document objects
        4. We add extra metadata to each document

        What is SimpleDirectoryReader:
        - A LlamaIndex utility for batch loading
        - Automatically detects file types
        - Uses appropriate readers for each file
        - Returns list of Document objects
        - Handles errors gracefully

        What would happen if we removed it:
        - Would need to manually iterate through files
        - Would need to handle file type detection manually
        - More error-prone and less efficient
        """

        directory_path_obj = Path(directory_path)

        if not directory_path_obj.exists():
            raise FileNotFoundError(f"Directory not found: {directory_path}")

        logger.info(f"Loading documents from directory: {directory_path}")

        # Use SimpleDirectoryReader for batch loading
        # Why SimpleDirectoryReader?
        # - Handles multiple file types automatically
        # - Provides a simple interface
        # - LlamaIndex's recommended approach for batch loading
        reader = SimpleDirectoryReader(
            input_dir=str(directory_path_obj),
            recursive=recursive,
            required_exts=list(SUPPORTED_EXTENSIONS),
        )

        docs = reader.load_data()

        logger.info(f"Loaded {len(docs)} documents from directory")

        # Add extra metadata to each document
        if extra_metadata:
            for doc in docs:
                doc.metadata.update(extra_metadata)

        return docs

    def load_from_url(self, url: str) -> Document:
        """
        Load a document from a URL.

        Why we need this method:
        - Ingest web content directly
        - Support web scraping for enterprise knowledge bases
        - Load documentation from external sources

        Args:
            url: URL to load from

        Returns:
            Document: LlamaIndex Document object

        What happens internally:
        1. Use SimpleWebPageReader to fetch the URL
        2. Extract text content from HTML
        3. Create Document object with URL metadata
        """

        if SimpleWebPageReader is None:
            raise ImportError(
                "llama-index-readers-web is not installed. "
                "Install it with: pip install llama-index-readers-web"
            )

        logger.info(f"Loading document from URL: {url}")

        # SimpleWebPageReader fetches and parses web pages
        # Why SimpleWebPageReader?
        # - Handles HTTP requests
        # - Extracts text from HTML
        # - Returns Document objects
        # - Clean interface for web scraping
        reader = SimpleWebPageReader(html_to_text=True)
        docs = reader.load_data([url])

        if not docs:
            raise ValueError(f"Failed to load document from URL: {url}")

        doc = docs[0]
        doc.metadata["source_url"] = url

        logger.info(f"Successfully loaded document from URL ({len(doc.text)} characters)")

        return doc


# Singleton instance for use throughout the application
document_loader = DocumentLoader()
