"""FastAPI application entry point."""
import sys
from pathlib import Path

# Ensure project root is on sys.path
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import benchmark, chat, comparison, settings

app = FastAPI(title="LocalMind API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router)
app.include_router(benchmark.router)
app.include_router(comparison.router)
app.include_router(settings.router)


@app.on_event("startup")
async def startup_message():
    print(
        "LocalMind running → UI: http://localhost:5173 \n"
        "                    → API: http://localhost:8000"
    )


@app.get("/")
async def root():
    return {"service": "LocalMind API", "docs": "/docs"}
