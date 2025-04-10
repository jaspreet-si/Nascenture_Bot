# routes/sync.py
from fastapi import APIRouter
from pydantic import BaseModel

from services.sync_service import scrape_website  # make sure these are initialized

from langchain.text_splitter import RecursiveCharacterTextSplitter

from utils.common import  embeddings, scraped_index
from langchain_pinecone import PineconeVectorStore

router = APIRouter()

class URLInput(BaseModel):
    id: int
    url: str

@router.post("/sync-url")
async def sync_url_data_pinecone(url: URLInput):
    try:
        content = scrape_website(url.url)
        if not content:
            return {"status": "error", "message": "No content found"}

        text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=100)
        texts = text_splitter.split_text(content)
        
        metadatas = [{"source": url.url} for _ in texts]  # no need for 'id' inside metadata
        ids = [f"{url.id}_{i}" for i in range(len(texts))]
        scraped_index.add_texts(texts, metadatas=metadatas, ids=ids)
        # vectorstore = PineconeVectorStore(index=scraped_index, embedding=embeddings, text_key="text")
        # vectorstore.add_texts(texts, metadatas=metadatas, ids=ids)

        return {"status": "success", "message": f"Synced URL {url.url} to Pinecone."}

    except Exception as e:
        return {"status": "error", "message": str(e)}