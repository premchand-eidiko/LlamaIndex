from llama_index.core.schema import TextNode
from llama_index.core import Document

document = Document(
    text="LlamaIndex connects LLMs with external data."
)

node=TextNode(
        text=document.text,
        metadata={
        "topic": "Python",
        "source": "notes.txt"
         }   
   )

print(node)
print(node.text)
print(node.metadata)