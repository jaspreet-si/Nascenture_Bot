from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services.chat_service import chat_bot

router = APIRouter()


class ChatRequest(BaseModel):
    query: str
    session_id : str
    # print("ChatRequest",query)

@router.post("/chat/")
async def chat(request: ChatRequest):
    print("Called-------")
    try:
        response = chat_bot(request.query, request.session_id)
        if not response:
            raise HTTPException(status_code=500, detail="No response from chatbot.")
        return {"response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
