from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from routes import webhook, debug
from voice.router import router as voice_router


app = FastAPI(
    title=settings.api_title,
    version=settings.api_version,
    description="Multi-channel AI support agent with Redis batching and LLM tool use",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(webhook.router, prefix="/webhook", tags=["webhook"])
app.include_router(debug.router, prefix="", tags=["debug"])
app.include_router(voice_router, tags=["voice"])


@app.get("/health", tags=["health"])
def health_check():
    """Health check endpoint for Docker and load balancers."""
    return {"status": "healthy"}


@app.get("/", tags=["root"])
def root():
    """API info. Frontend is served separately at localhost:3000."""
    return {
        "name": settings.api_title,
        "version": settings.api_version,
        "docs": "/docs",
        "frontend": "http://localhost:3000",
    }
