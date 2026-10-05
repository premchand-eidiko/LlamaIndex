from llama_index.core import VectorStoreIndex, Document
from llama_index.core.retrievers import VectorIndexRetriever
from llama_index.core.node_parser import SentenceSplitter
from llama_index.embeddings.huggingface import HuggingFaceEmbedding


documents = [
    Document(
        text="Employees receive 20 days of annual leave every year."
    ),
    Document(
        text="Employees can apply for leave using the HR portal."
    ),
    Document(
        text="The company was founded in 2010."
    ),
    Document(
        text="The company headquarters is located in Hyderabad."
    ),
    Document(
        text="Employees receive health insurance benefits."
    ),
]

# Create ingestion pipeline components
node_parser = SentenceSplitter(chunk_size=256, chunk_overlap=64)
embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-small-en-v1.5")

# Create index with ingestion pipeline
index = VectorStoreIndex.from_documents(
    documents,
    transformations=[node_parser],
    embed_model=embed_model
)

retriever = VectorIndexRetriever(
    index=index,
    similarity_top_k=2
)

query = "How much vacation can an employee take?"

nodes = retriever.retrieve(query)

for node in nodes:
    print(f"Text: {node.text}")
    print(f"Metadata: {node.metadata}")
    print("Score:", node.score)
    print(type(node))
    print("-" * 50)