from llama_index.core import Document
from llama_index.core.node_parser import SentenceSplitter

document = Document(
    text="""
    LlamaIndex is a framework for building LLM applications.
    It helps connect LLMs with external data.
    It provides tools for indexing and retrieval.
    Documents can be divided into smaller nodes.
    """,
    metadata={
        "department": "AI",
        "source": "llamaindex_notes.txt",
        "topic": "RAG"
    }
)

splitter = SentenceSplitter(
    chunk_size=50,
    chunk_overlap=0
)

nodes = splitter.get_nodes_from_documents([document])

for i, node in enumerate(nodes):
    print(f"----- NODE {i + 1} -----")
    print("TEXT:", node.text)
    print("METADATA:", node.metadata)
    print()