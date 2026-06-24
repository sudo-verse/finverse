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

# RAG vector store. Default: embedded ChromaDB persisting to CHROMA_DIR (the
# parent_store sidecar + ingest manifest always live here). In a multi-container
# deployment set CHROMA_HOST (+ CHROMA_PORT) to talk to a standalone Chroma
# server instead, so the API (reads) and ingestion worker (writes) share one
# vector store over HTTP rather than a shared filesystem.
CHROMA_DIR = os.getenv("CHROMA_DIR", "chroma_db")
CHROMA_HOST = os.getenv("CHROMA_HOST") or None
CHROMA_PORT = int(os.getenv("CHROMA_PORT", "8000"))

# Cross-encoder reranker (self-hosted via transformers — no extra API). When
# enabled it RRF-blends with the lexical/semantic fusion order. Default OFF:
# on our figure-heavy golden set the plain fused order measured best (MRR 0.77
# vs 0.70 blended), and reranking demoted exact-figure matches. Enable for query
# mixes with more ambiguous/semantic questions, where a cross-encoder earns its
# keep. bge-reranker-base is fast on CPU; BAAI/bge-reranker-v2-m3 is stronger.
RERANKER_ENABLED = os.getenv("RERANKER_ENABLED", "false").lower() == "true"
RERANKER_MODEL = os.getenv("RERANKER_MODEL", "BAAI/bge-reranker-base")

# Query rewriting: expand a question into semantic + keyword + alternate forms
# before hybrid search (one extra Gemini call per uncached retrieval). Falls
# back to the raw question on any failure. Disable with QUERY_REWRITE_ENABLED=false.
QUERY_REWRITE_ENABLED = os.getenv("QUERY_REWRITE_ENABLED", "true").lower() == "true"

MAX_ARTICLES = 5
SENTIMENT_THRESHOLD = 0.7