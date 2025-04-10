from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.httpsredirect import HTTPSRedirectMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.gzip import GZipMiddleware

def add_cors(app: FastAPI):
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["https://nascenture.com",
                       "https://faq-manager.onrender.com",
                       "https://nascenture-chatbot.onrender.com",
                       "http://localhost",
                       "http://127.0.0.1:8000",
                       
                       ], 
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    


def add_security_middleware(app: FastAPI):
    # Force HTTPS
    app.add_middleware(HTTPSRedirectMiddleware)

    # Allow only your domain or trusted hosts (adjust this in prod)
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["*"
                    ]
    )

    # Enable response compression
    app.add_middleware(GZipMiddleware, minimum_size=1000)