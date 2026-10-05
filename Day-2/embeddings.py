from llama_index.core import Document
from llama_index.core.ingestion import IngestionPipeline
from llama_index.core.node_parser import SentenceSplitter
from llama_index.embeddings.huggingface import HuggingFaceEmbedding


documents = [
    Document(
        text="Python is a programming language. "
             "Python is easy to learn. "
             "Python is widely used in AI."
    )
]


embed_model = HuggingFaceEmbedding(
    model_name="BAAI/bge-small-en-v1.5"
)


pipeline = IngestionPipeline(
    transformations=[
        SentenceSplitter(
            chunk_size=5,
            chunk_overlap=0
        ),
        embed_model
    ]
)


nodes = pipeline.run(
    documents=documents
)


print("Number of nodes:", len(nodes))

for i, node in enumerate(nodes):
    print(f"\n--- NODE {i+1} ---")
    print(node.text)
    print("Embedding length:", len(node.embedding))