from llama_index.core.node_parser import SentenceSplitter
from llama_index.core import Document

document = Document(
    text="""
    LlamaIndex is a framework for building LLM applications.
    It helps connect LLMs with external data.
    It provides tools for indexing and retrieval.
    It can be used to build RAG applications.
    Retrieval augmented generation allows an LLM to use external knowledge.
    Documents can be loaded from PDFs, websites, databases, and text files.
    Documents can be divided into smaller nodes for efficient retrieval.
    Nodes can contain text, metadata, and relationships.
    Embeddings can represent the meaning of text numerically.
    Vector stores can be used to store and retrieve embeddings.
    A retriever finds relevant nodes for a user query.
    The retrieved nodes can then be provided to an LLM.
    The LLM uses this context to generate an answer.
    """
)

splitter=SentenceSplitter(chunk_size=50,chunk_overlap=0)

nodes=splitter.get_nodes_from_documents([document])

for i, node in enumerate(nodes):
    print(f"----- NODE {i+1} -----")
    print(node.text)
    print("Characters:", len(node.text))
    print()