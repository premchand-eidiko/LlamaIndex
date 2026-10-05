from llama_index.core import SimpleDirectoryReader
from llama_index.core.node_parser import SentenceSplitter

documents = SimpleDirectoryReader(
    input_dir="data"
).load_data()

parser = SentenceSplitter(
    chunk_size=30,
    chunk_overlap=5
)

nodes = parser.get_nodes_from_documents(documents)

print("Number of documents:", len(documents))
print("Number of nodes:", len(nodes))

for i, node in enumerate(nodes):
    print(f"\n----- NODE {i + 1} -----")
    print(node.text)
    print("SOURCE:", node.metadata.get("file_name"))