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
                year: int = None, page: int = None, section: str = None,
                parent_id: str = None, chunk_type: str = None) -> dict:
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
    if section:
        meta["section"] = section
    if parent_id:
        meta["parent_id"] = parent_id
    if chunk_type:
        meta["chunk_type"] = chunk_type
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


def ingest_file(path: str, symbol: str = None, doc_type: str = None, year: int = None) -> int:
    """Structural, table-aware, parent–child ingestion (app.genai.chunking).

    Embeds the *contextual* form of each child chunk (header + body) but stores
    the clean body for display/citation; parent sections go to parent_store for
    small-to-big retrieval. Resumable: chunk ids already present in Chroma are
    skipped and batches are upserted as they embed, so a run interrupted by the
    daily embedding quota continues where it left off on the next run.
    """
    from app.genai import chunking, parent_store

    chunks, parents = chunking.chunk_file(path, symbol=symbol, doc_type=doc_type, year=year)
    if not chunks:
        return 0
    source = os.path.basename(path)

    # Parents are free (not embedded) — persist them up front so they survive a
    # quota interruption mid-embed.
    parent_store.put_many(parents)

    collection = _get_collection()
    ids = [_doc_id(source, i, c.text) for i, c in enumerate(chunks)]
    existing = set(collection.get(ids=ids).get("ids") or [])

    added = 0
    pending: list[tuple[str, "chunking.Chunk"]] = [
        (cid, c) for cid, c in zip(ids, chunks) if cid not in existing
    ]
    for i in range(0, len(pending), 100):
        batch = pending[i:i + 100]
        vectors = gemini_client.embed([c.embed_text for _, c in batch])  # RETRIEVAL_DOCUMENT
        collection.upsert(
            ids=[cid for cid, _ in batch],
            embeddings=vectors,
            documents=[c.text for _, c in batch],
            metadatas=[_build_meta(source, symbol, doc_type, year, page=c.page,
                                   section=c.section, parent_id=c.parent_id,
                                   chunk_type=c.chunk_type)
                       for _, c in batch],
        )
        added += len(batch)

    if added:
        from app.genai import lexical
        lexical.invalidate()  # rebuild BM25 index over the new chunks
    logger.info("rag: ingested %s — %d new chunks (%d already present)",
                source, added, len(existing))
    return added


def get_collection():
    """Public accessor for the document collection (used by the research layer)."""
    return _get_collection()


def reset_collection():
    """Drop and recreate the document collection. Used by a full reindex when
    the chunking scheme changes (old chunk ids would otherwise linger)."""
    global _collection
    import chromadb

    client = chromadb.PersistentClient(path=CHROMA_DIR)
    try:
        client.delete_collection(COLLECTION)
    except Exception:  # collection may not exist yet
        pass
    _collection = None
    logger.info("rag: document collection reset")
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
