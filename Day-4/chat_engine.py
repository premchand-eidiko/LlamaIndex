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

# 4. Create chat engine
chat_engine = index.as_chat_engine(
    chat_mode="condense_plus_context",
    similarity_top_k=3
)

# 5. Conversation
response = chat_engine.chat(
    "What is the remote work policy?"
)

print("AI:", response)

response = chat_engine.chat(
    "How many days can I work remotely?"
)

print("AI:", response)

response = chat_engine.chat(
    "Do I need to come to the office on specific days?"
)

print("AI:", response)