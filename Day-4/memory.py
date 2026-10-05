from llama_index.core.memory import ChatMemoryBuffer
from llama_index.core.llms import ChatMessage


# Create memory
memory = ChatMemoryBuffer.from_defaults(
    token_limit=3000
)


# Store user message
memory.put(
    ChatMessage(
        role="user",
        content="What is the leave policy?"
    )
)


# Store AI response
memory.put(
    ChatMessage(
        role="assistant",
        content="Employees get 20 days of annual leave."
    )
)


# Get conversation
messages = memory.get()


# Display conversation
for message in messages:
    print(f"{message.role}: {message.content}")