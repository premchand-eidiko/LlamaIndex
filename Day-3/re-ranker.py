from llama_index.core import VectorStoreIndex, Document
from llama_index.core.retrievers import VectorIndexRetriever
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.postprocessor.sbert_rerank import SentenceTransformerRerank


documents = [
    Document(
        text="Employees receive 20 days of annual leave every year."
    ),
    Document(
        text="The company provides health insurance to employees."
    ),
    Document(
        text="Employees can apply for leave using the HR portal."
    ),
    Document(
        text="The company headquarters is located in Hyderabad."
    ),
]


index = VectorStoreIndex.from_documents(documents)


retriever = VectorIndexRetriever(
    index=index,
    similarity_top_k=4
)


reranker = SentenceTransformerRerank(
    model="cross-encoder/ms-marco-MiniLM-L-2-v2",
    top_n=2
)


query_engine = RetrieverQueryEngine(
    retriever=retriever,
    node_postprocessors=[reranker]
)