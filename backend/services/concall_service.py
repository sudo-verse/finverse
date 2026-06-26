"""Concall (earnings-call) transcripts + AI summaries.

Transcripts are filed as PDFs in a company's NSE announcements. We detect those
filings by keyword, then (on demand) download the PDF, extract its text and ask
Gemini for a structured summary — highlights, guidance, outlook and risks —
cached in `company_insights`. Reuses the existing NSE session + Gemini client;
no new data store. Generate-on-click so browsing never spends an AI call.
"""

import hashlib
import json
import logging
import os
import re
import tempfile
from datetime import datetime

from sqlalchemy.orm import Session

from app.db.database import engine, get_session
from app.db.models import CompanyInsight
from app.genai import gemini_client
from backend.core.exceptions import NoDataError, ServiceUnavailableError
from backend.schemas.concall import ConcallRow, ConcallSummary
from backend.services.nse_service import nse_service

logger = logging.getLogger("finverse.api")

_KEYWORDS = (
    "transcript", "earnings call", "conference call", "concall",
    "earnings conference", "analyst call", "investor call", "earnings call transcript",
)
_MAX_CHARS = 30000

_SYSTEM = (
    "You are an equity research analyst summarising an earnings-call (concall) "
    "transcript. Return STRICT JSON only: "
    '{"highlights": [str], "guidance": str, "outlook": str, "risks": [str]}. '
    "highlights: 3-6 concrete points management made (numbers, segment trends, "
    "capex, demand). guidance: forward revenue/margin/growth guidance in one "
    "sentence (or \"Not specified\"). outlook: management's tone in one sentence. "
    "risks: 2-4 concerns or headwinds raised. Ground everything in the "
    "transcript. No markdown, no commentary outside the JSON."
)


def _key(url: str) -> str:
    return "concall:" + hashlib.md5(url.encode()).hexdigest()[:16]


def list_concalls(symbol: str, limit: int = 15) -> list[ConcallRow]:
    out: list[ConcallRow] = []
    try:
        anns = nse_service.announcements(symbol.upper(), limit=50)
    except Exception:
        return []
    for a in anns:
        blob = f"{a.subject or ''} {a.details or ''}".lower()
        if a.attachment_url and any(k in blob for k in _KEYWORDS):
            out.append(ConcallRow(date=a.broadcast_at, title=a.subject, url=a.attachment_url))
    return out[:limit]


def _pdf_text(url: str) -> str | None:
    from app.market import nse_shp

    path = None
    try:
        r = nse_shp._sess().get(url, timeout=45)
        if r.status_code != 200 or not r.content:
            return None
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            f.write(r.content)
            path = f.name
        from pypdf import PdfReader

        pages = PdfReader(path).pages
        return "\n".join((p.extract_text() or "") for p in pages)
    except Exception:
        logger.warning("concall: PDF fetch/parse failed for %s", url, exc_info=True)
        return None
    finally:
        if path and os.path.exists(path):
            try:
                os.unlink(path)
            except OSError:
                pass


def summarize(session: Session, symbol: str, url: str, refresh: bool = False) -> ConcallSummary:
    sym = symbol.upper()
    CompanyInsight.__table__.create(engine, checkfirst=True)
    kind = _key(url)

    def _from(data: dict, **kw) -> ConcallSummary:
        return ConcallSummary(
            symbol=sym, url=url,
            highlights=data.get("highlights", [])[:6],
            guidance=data.get("guidance"),
            outlook=data.get("outlook"),
            risks=data.get("risks", [])[:4],
            **kw,
        )

    if not refresh:
        row = session.query(CompanyInsight).filter_by(symbol=sym, kind=kind).first()
        if row and row.content:
            return _from(json.loads(row.content), cached=True, model=row.model,
                         generated_at=str(row.generated_at))
        return ConcallSummary(symbol=sym, url=url, cached=False)

    if not gemini_client.is_configured():
        raise ServiceUnavailableError("GEMINI_API_KEY is not configured.")
    from app.config import GEMINI_MODEL

    text = _pdf_text(url)
    if not text or len(text.strip()) < 400:
        raise NoDataError("Could not read the transcript PDF (it may be a scanned image or unavailable).")

    prompt = f"Company: {sym} (NSE).\n\n=== CONCALL TRANSCRIPT ===\n{text[:_MAX_CHARS]}\n\nJSON:"
    raw = gemini_client.generate_text(prompt, system_instruction=_SYSTEM)
    match = re.search(r"\{.*\}", raw or "", re.DOTALL)
    if not match:
        raise NoDataError(f"Could not summarise the transcript for {sym}.")
    parsed = json.loads(match.group(0))
    data = {
        "highlights": [str(x) for x in parsed.get("highlights", []) if x][:6],
        "guidance": (str(parsed.get("guidance")) if parsed.get("guidance") else None),
        "outlook": (str(parsed.get("outlook")) if parsed.get("outlook") else None),
        "risks": [str(x) for x in parsed.get("risks", []) if x][:4],
    }

    with get_session() as ws:
        row = ws.query(CompanyInsight).filter_by(symbol=sym, kind=kind).first()
        if row:
            row.content, row.model, row.generated_at = json.dumps(data), GEMINI_MODEL, datetime.utcnow()
        else:
            ws.add(CompanyInsight(symbol=sym, kind=kind, content=json.dumps(data), model=GEMINI_MODEL))

    return _from(data, cached=False, model=GEMINI_MODEL, generated_at=str(datetime.utcnow()))
