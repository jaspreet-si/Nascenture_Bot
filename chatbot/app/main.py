import sys
import os
print("PYTHON PATH:", sys.path)

# Add project root to PYTHONPATH so imports like 'api.v1' work
current_dir = os.path.dirname(os.path.abspath(__file__))  # chatbot/app/
project_root = os.path.abspath(os.path.join(current_dir,))  # chatbot/
sys.path.insert(0, project_root)
print("✅ Added to sys.path:", project_root)
from fastapi import FastAPI
from api.v1.sync import router as sync_router
from api.v1.chat import router as chat_router
# from fastapi.middleware.cors import CORSMiddleware
from utils.middleware import add_cors, add_security_middleware

app = FastAPI()

add_cors(app)
# add_security_middleware(app)

app.include_router(chat_router, prefix="/api")
app.include_router(sync_router, prefix="/api")
@app.get("/")
async def root():
    return {"message": "Welcome to Nascenture Chatbot API!"}
