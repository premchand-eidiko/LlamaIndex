from llama_index.core import Document, VectorStoreIndex
from llama_index.embeddings.huggingface import HuggingFaceEmbedding


documents = [
    Document(
        text="Python is a programming language."
    ),
    Document(
        text="FastAPI is a Python web framework."
    ),
    Document(
        text="Hyderabad is a city in India."
    )
]


embed_model = HuggingFaceEmbedding(
    model_name="BAAI/bge-small-en-v1.5"
)


index = VectorStoreIndex.from_documents(
    documents,
    embed_model=embed_model
)


print("Index created successfully!")
print(index)