from langchain.chat_models import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationChain
import os
import psycopg2

# OpenAI model setup
llm = ChatOpenAI(
    temperature=0,
    openai_api_key=os.environ["OPENAI_API_KEY"],
    model_name="gpt-4"
)

# Conversational memory
memory = ConversationBufferMemory()

# Conversation chain
conversation = ConversationChain(
    llm=llm,
    memory=memory
)

async def chat_with_memory(message: str) -> str:
    # Aquí podrías conectar con la base de datos y usar SQL dinámico
    # basado en la interpretación del mensaje
    response = conversation.run(message)
    return response
