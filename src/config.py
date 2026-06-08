import os
from pathlib import Path
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

def _get_api_key(name: str) -> str | None:
    value = os.getenv(name, "").strip().strip('"').strip("'")
    return value or None

GROQ_API_KEY = _get_api_key("GROQ_API_KEY")
TAVILY_API_KEY = _get_api_key("TAVILY_API_KEY")
MODEL_NAME = "llama-3.3-70b-versatile"
OUTPUT_DIR = "outputs"
