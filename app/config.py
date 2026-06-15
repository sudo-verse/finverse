import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Database — defaults to a local SQLite file for zero-setup dev.
# Switch to MySQL by setting DATABASE_URL in .env, e.g.:
#   mysql+pymysql://user:password@localhost:3306/finverse
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///finverse.db")

# Generative AI (investment reports + RAG) — Google Gemini
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
GEMINI_EMBED_MODEL = os.getenv("GEMINI_EMBED_MODEL", "gemini-embedding-001")

# Optional extra keys (separate projects) rotated through on quota (429) errors
# to multiply the free-tier per-minute / daily embedding budget. Reads the base
# GEMINI_API_KEY plus GEMINI_API_KEY1..GEMINI_API_KEY12; order-preserving dedupe.
GEMINI_API_KEYS = list(dict.fromkeys(
    k for k in (
        GEMINI_API_KEY,
        *(os.getenv(f"GEMINI_API_KEY{i}") for i in range(1, 13)),
    ) if k
))

# RAG vector store (ChromaDB persistent directory)
CHROMA_DIR = os.getenv("CHROMA_DIR", "chroma_db")

MAX_ARTICLES = 5
SENTIMENT_THRESHOLD = 0.7