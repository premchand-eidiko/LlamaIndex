from llama_index.core import Document

document = Document(
    text="LlamaIndex connects LLMs with external data."
)

print(document)
print(document.text)