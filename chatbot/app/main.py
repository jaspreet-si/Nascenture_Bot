import sys
import os
import threading



# Add project root to PYTHONPATH so imports like 'api.v1' work
current_dir = os.path.dirname(os.path.abspath(__file__))  # chatbot/app/
project_root = os.path.abspath(os.path.join(current_dir,))  # chatbot/
sys.path.insert(0, project_root)


from fastapi import FastAPI
from routers.v1.sync import router as sync_router
from routers.v1.chat import router as chat_router
# from fastapi.middleware.cors import CORSMiddleware
from utils.middleware import add_cors, add_security_middleware
import requests


app = FastAPI()

add_cors(app)
# add_security_middleware(app)

app.include_router(chat_router, prefix="/api")

app.include_router(sync_router, prefix="/api")

@app.get("/")
async def root():
    return {"message": "Welcome to Nascenture Chatbot API!"}


@app.get("/awake")
async def awake():
    print("Awake endpoint hit.")
    return {"status": "awake"}

def call_awake_periodically():
    """Function to call /awake every 10 minutes."""
    threading.Timer(600, call_awake_periodically).start()  # 600 seconds = 10 minutes
    print("Triggering /awake...")
    try:
        
        response = requests.get("https://nascenture-chatbot.onrender.com/awake")
        print(f"Awake Response: {response.status_code}")
    except Exception as e:
        print(f"Error calling awake: {e}")

@app.on_event("startup")
def start_awake_pinger():
    print("Starting periodic awake pinger...")
    threading.Thread(target=call_awake_periodically, daemon=True).start()
