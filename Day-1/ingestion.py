from llama_index.core import Document
from llama_index.core.ingestion import IngestionPipeline
from llama_index.core.node_parser import SentenceSplitter

document = Document(
    text="""
    LlamaIndex connects LLMs with external data.
    Documents can be divided into smaller nodes.
    Nodes can then be used for retrieval.
    """
)

pipeline = IngestionPipeline(
    transformations=[
        SentenceSplitter(
            chunk_size=50,
            chunk_overlap=0
        )
    ]
)

nodes = pipeline.run(
    documents=[document]
)

for i, node in enumerate(nodes):
    print(f"----- NODE {i + 1} -----")
    print(node.text)
    print()