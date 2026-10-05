import os
from dotenv import load_dotenv
from llama_index.core import (
    SimpleDirectoryReader,
    VectorStoreIndex,
    Settings
)
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.llms.groq import Groq

# Load environment variables from .env file
load_dotenv()

# 1. Load documents
documents = SimpleDirectoryReader("../Day-1/data").load_data()

# 2. Configure local embeddings and Groq LLM
Settings.embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-small-en-v1.5")
Settings.llm = Groq(model="openai/gpt-oss-20b", api_key=os.getenv("GROQ_API_KEY"))

# 3. Create index
index = VectorStoreIndex.from_documents(documents)

# 4. Create query engine
query_engine = index.as_query_engine(
    response_mode="compact"
)

# 5. Ask question
response = query_engine.query(
    "What is the remote work policy?"
)

# 6. Print answer
print(response)