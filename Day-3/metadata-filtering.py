from llama_index.core import Document, VectorStoreIndex
from llama_index.core.vector_stores import (
    MetadataFilters,
    MetadataFilter,
    FilterCondition,
)


documents = [
    Document(
        text="Employees receive 20 days of annual leave.",
        metadata={
            "department": "HR",
            "year": 2026,
            "type": "policy",
        },
    ),

    Document(
        text="Employees received 18 days of annual leave.",
        metadata={
            "department": "HR",
            "year": 2025,
            "type": "policy",
        },
    ),

    Document(
        text="Finance department follows quarterly reporting rules.",
        metadata={
            "department": "Finance",
            "year": 2026,
            "type": "policy",
        },
    ),

    Document(
        text="The company provides health insurance.",
        metadata={
            "department": "HR",
            "year": 2026,
            "type": "benefit",
        },
    ),
]


index = VectorStoreIndex.from_documents(documents)


filters = MetadataFilters(
    filters=[
        MetadataFilter(
            key="department",
            value="HR",
        ),
        MetadataFilter(
            key="year",
            value=2026,
        ),
    ],
    condition=FilterCondition.AND,
)


retriever = index.as_retriever(
    similarity_top_k=3,
    filters=filters,
)


results = retriever.retrieve(
    "What is the employee leave policy?"
)


for result in results:
    print("Score:", result.score)
    print("Text:", result.node.text)
    print("Metadata:", result.node.metadata)
    print("-" * 50)