import os
from pathlib import Path

from dotenv import load_dotenv


load_dotenv()

DATA_DIR = Path(os.getenv("DATA_DIR", str(Path(__file__).resolve().parents[2] / "data")))
MAX_UPLOAD_BYTES = int(os.getenv("MAX_UPLOAD_MB", "10")) * 1024 * 1024
CORS_ORIGINS = [origin.strip() for origin in os.getenv(
    "CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000"
).split(",") if origin.strip()]


# =========================================
# ACTIVE PROVIDER
# =========================================

LLM_PROVIDER = os.getenv(
    "LLM_PROVIDER",
    "mock",
).strip().lower()


# =========================================
# OPENAI
# =========================================

OPENAI_API_KEY = os.getenv(
    "OPENAI_API_KEY",
    "",
).strip()

OPENAI_MODEL = os.getenv(
    "OPENAI_MODEL",
    "",
).strip()


# =========================================
# GROQ
# =========================================

GROQ_API_KEY = os.getenv(
    "GROQ_API_KEY",
    "",
).strip()

GROQ_MODEL = os.getenv(
    "GROQ_MODEL",
    "",
).strip()
