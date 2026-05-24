"""Shared configuration for LocalMind."""
import os
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_PATH = PROJECT_ROOT / ".env"
load_dotenv(ENV_PATH)

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "llama3")
DEFAULT_TEMPERATURE = float(os.getenv("DEFAULT_TEMPERATURE", "0.7"))
MAX_TOKENS = int(os.getenv("MAX_TOKENS", "2048"))

MODEL_LIST = [
    "llama3.2",
    "mistral",
    "phi3",
]

BENCHMARK_PROMPTS = [
    "Explain the difference between TCP and UDP in two paragraphs.",
    "Write a Python function to merge two sorted lists.",
    "Summarize the key ideas of functional programming.",
    "Describe three uses of local LLMs for developers.",
    "What are the tradeoffs of RAG vs fine-tuning?",
    "List five best practices for API error handling.",
    "How does gradient descent work in simple terms?",
    "Write a short poem about debugging at midnight.",
    "Compare REST and GraphQL for a mobile app backend.",
    "Give a checklist for securing a FastAPI service.",
]

COMPARISON_MODELS = ["llama3.2", "phi3", "mistral"]
