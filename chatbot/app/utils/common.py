from core.config import  settings
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
# from langchain_community.embeddings.openai import OpenAIEmbeddings
from pinecone import Pinecone as PC
import os
from langchain_pinecone import Pinecone
try:
    pc = PC(
        api_key=settings.PINECONE_API_KEY,
        environment=settings.PINECONE_ENVIRONMENT,
    )

    llm = ChatOpenAI(
        api_key=settings.OPENAI_API_KEY,
        temperature=0.7,
        model_name="gpt-3.5-turbo",
    )

    # 2) Setup Embeddings
    embeddings = OpenAIEmbeddings(api_key=settings.OPENAI_API_KEY)

    # 3) Pinecone Vector Database Setup

    os.environ["PINECONE_API_KEY"] = settings.PINECONE_API_KEY
    os.environ["PINECONE_ENVIRONMENT"] = settings.PINECONE_ENVIRONMENT
    scraped_index = Pinecone.from_existing_index("nascenture-chatbot", embeddings)
    faq_index = Pinecone.from_existing_index('faq-index',embeddings)
    print("Setup successfully initilized")
except Exception as e:
    print(f"Something went wrong as {str(e)}")

