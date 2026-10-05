from llama_index.core import SimpleDirectoryReader
from llama_index.core.ingestion import IngestionPipeline
from llama_index.core.node_parser import SentenceSplitter


# 1. Load all documents
documents = SimpleDirectoryReader(
    input_dir="data"
).load_data()

print("Documents loaded:", len(documents))


# 2. Create Ingestion Pipeline
pipeline = IngestionPipeline(
    transformations=[
        SentenceSplitter(
            chunk_size=50,
            chunk_overlap=30
        )
    ]
)


# 3. Run the ingestion pipeline
nodes = pipeline.run(
    documents=documents
)

print("Nodes created:", len(nodes))


# 4. Display the Nodes
for i, node in enumerate(nodes):

    print(f"\n----- NODE {i + 1} -----")

    print("TEXT:")
    print(node.text)

    print("\nSOURCE:")
    print(node.metadata.get("file_name"))

    print("\nMETADATA:")
    print(node.metadata)