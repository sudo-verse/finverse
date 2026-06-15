"""L9 — RAG over financial documents (annual reports, filings, presentations).

ChromaDB persistent vector store + Gemini embeddings for retrieval, Gemini for
the grounded answer. Documents can be scoped to a stock symbol so questions can
be filtered to one company's filings.
"""

import hashlib
import os

from app.config import CHROMA_DIR
from app.genai import gemini_client
from app.utils.logger import logger

COLLECTION = "documents"

_collection = None


def _get_collection():
    global _collection
    if _collection is None:
        import chromadb

        client = chromadb.PersistentClient(path=CHROMA_DIR)
        # we supply our own (Gemini) embeddings, so no embedding function here
        _collection = client.get_or_create_collection(
            COLLECTION, metadata={"hnsw:space": "cosine"}
        )
    return _collection


def chunk_text(text: str, size: int = 1000, overlap: int = 150):
    text = " ".join(text.split())
    if not text:
        return []
    chunks = []
    start = 0
    while start < len(text):
        end = start + size
        chunks.append(text[start:end])
        start = end - overlap
    return chunks


def _doc_id(source: str, idx: int, content: str) -> str:
    h = hashlib.sha1(f"{source}:{idx}:{content[:64]}".encode()).hexdigest()[:16]
    return f"{source}:{idx}:{h}"


def _build_meta(source: str, symbol: str = None, doc_type: str = None,
                year: int = None, page: int = None) -> dict:
    """Chroma metadata values must be scalars; skip Nones entirely."""
    meta = {"source": source}
    if symbol:
        meta["symbol"] = symbol.upper()
    if doc_type:
        meta["doc_type"] = doc_type
    if year:
        meta["year"] = int(year)
    if page:
        meta["page"] = int(page)
    return meta


def ingest_text(text: str, source: str, symbol: str = None, doc_type: str = None,
                year: int = None, page: int = None) -> int:
    """Chunk, embed, and store a document. Returns the number of chunks added.

    Upserts on deterministic ids, so re-ingesting the same source is idempotent.
    """
    chunks = chunk_text(text)
    if not chunks:
        return 0

    vectors = gemini_client.embed(chunks)
    meta = _build_meta(source, symbol, doc_type, year, page)
    key = f"{source}:p{page or 0}"

    collection = _get_collection()
    collection.upsert(
        ids=[_doc_id(key, i, c) for i, c in enumerate(chunks)],
        embeddings=vectors,
        documents=chunks,
        metadatas=[dict(meta) for _ in chunks],
    )
    logger.info(f"rag: ingested {len(chunks)} chunks from {source}"
                + (f" p{page}" if page else ""))
    return len(chunks)


def ingest_pdf(path: str, symbol: str = None, doc_type: str = None, year: int = None) -> int:
    """Ingest a PDF page by page so each chunk carries a real page number
    (needed for 'Annual Report 2024 — Page 128' style citations)."""
    from pypdf import PdfReader

    reader = PdfReader(path)
    source = os.path.basename(path)
    total = 0
    for page_no, pdf_page in enumerate(reader.pages, start=1):
        text = pdf_page.extract_text() or ""
        if not text.strip():
            continue
        total += ingest_text(text, source=source, symbol=symbol,
                             doc_type=doc_type, year=year, page=page_no)
    return total


def ingest_file(path: str, symbol: str = None, doc_type: str = None, year: int = None) -> int:
    if path.lower().endswith(".pdf"):
        return ingest_pdf(path, symbol=symbol, doc_type=doc_type, year=year)
    with open(path, "r", errors="ignore") as f:
        return ingest_text(f.read(), source=os.path.basename(path),
                           symbol=symbol, doc_type=doc_type, year=year)


def get_collection():
    """Public accessor for the document collection (used by the research layer)."""
    return _get_collection()


def stats() -> dict:
    try:
        return {"chunks": _get_collection().count()}
    except Exception:
        return {"chunks": 0}


RAG_SYSTEM = (
    "You answer questions about companies using ONLY the provided document "
    "excerpts. If the answer is not in the excerpts, say you don't have that "
    "information in the documents. Quote figures and facts directly from the "
    "context. Be concise and cite which excerpt you used."
)


def answer_question(question: str, symbol: str = None, k: int = 4) -> dict:
    """Retrieve the top-k relevant chunks and answer the question with Gemini.

    Returns {answer, sources}. `sources` is a list of {source, snippet}.
    """
    collection = _get_collection()
    if collection.count() == 0:
        return {"answer": "No documents have been ingested yet.", "sources": []}

    q_vec = gemini_client.embed([question], task_type="RETRIEVAL_QUERY")[0]
    where = {"symbol": symbol} if symbol else None
    result = collection.query(query_embeddings=[q_vec], n_results=k, where=where)

    docs = result.get("documents", [[]])[0]
    metas = result.get("metadatas", [[]])[0]
    if not docs:
        return {"answer": "No relevant content found in the documents.", "sources": []}

    context = "\n\n".join(
        f"[Excerpt {i + 1} — {m.get('source', '?')}]\n{d}"
        for i, (d, m) in enumerate(zip(docs, metas))
    )
    prompt = (
        f"Question: {question}\n\n"
        f"Use only these document excerpts to answer:\n\n{context}\n\n"
        f"Answer:"
    )
    answer = gemini_client.generate_text(prompt, system_instruction=RAG_SYSTEM)

    sources = [
        {"source": m.get("source", "?"), "snippet": d[:240]}
        for d, m in zip(docs, metas)
    ]
    return {"answer": answer, "sources": sources}
