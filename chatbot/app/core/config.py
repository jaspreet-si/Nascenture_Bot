from pydantic_settings import BaseSettings
from pathlib import Path

class Settings(BaseSettings):
    OPENAI_API_KEY: str
    PINECONE_API_KEY: str
    PINECONE_ENVIRONMENT:str
    
    class Config:
        env_file = Path(__file__).resolve().parent.parent / ".env"
        

settings = Settings()
