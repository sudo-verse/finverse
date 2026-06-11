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

# RAG vector store (ChromaDB persistent directory)
CHROMA_DIR = os.getenv("CHROMA_DIR", "chroma_db")

MAX_ARTICLES = 5
SENTIMENT_THRESHOLD = 0.7