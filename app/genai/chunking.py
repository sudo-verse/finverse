"""Structural, table-aware, parent–child chunking with contextual headers.

Replaces the old fixed 1000-char splitter (which collapsed whitespace and cut
through the financial tables that *are* the answer for an equity-research
corpus). For each document we produce:

  Document
    └── Parent (a page or a heading-delimited section — the unit shown to the LLM)
          ├── Child text chunk   (sentence-aware window — the unit we embed/match)
          ├── Child text chunk
          └── Table chunk        (a full table, serialised to Markdown, kept intact)

Each chunk also carries a **contextual header** ("TCS · Annual Report 2025 ·
Segment Results") that is prepended *before embedding* so an otherwise-ambiguous
fragment ("Revenue grew 18%") knows which company/period/section it belongs to.
The clean body (no header) is what gets stored and cited; small-to-big parent
expansion at retrieval time swaps the matched child for its full parent.
"""

import os
import re
from dataclasses import dataclass, field

from app.utils.logger import logger

# Doc-type → human label for the contextual header (mirrors research.DOC_TYPE_LABELS).
DOC_TYPE_LABELS = {
    "annual_report": "Annual Report",
    "quarterly_report": "Quarterly Report",
    "earnings_call": "Earnings Call",
    "presentation": "Investor Presentation",
    "announcement": "NSE Announcement",
    "financials": "Financial Statements",
    "news": "News Signal",
}

CHILD_SIZE = 800        # target child chunk size (chars), sentence-aware
CHILD_OVERLAP = 120     # carry-over between adjacent children
PARENT_MAX = 4000       # cap parent text so generation context stays bounded

_SENT_RE = re.compile(r"(?<=[.!?])\s+")
# A heading-ish line: short, no terminal period, has letters, not a bare number.
_HEADING_RE = re.compile(r"^[A-Z0-9][^.\n]{2,58}$")


@dataclass
class Chunk:
    text: str                       # clean body — stored + cited
    embed_text: str                 # contextual header + body — what we embed
    parent_id: str
    chunk_type: str = "text"        # "text" | "table"
    section: str | None = None
    page: int | None = None


@dataclass
class _Block:
    text: str
    kind: str = "prose"             # "prose" | "table"
    page: int | None = None
    section: str | None = None


@dataclass
class _Parent:
    parent_id: str
    text: str
    section: str | None = None
    page: int | None = None
    children: list[Chunk] = field(default_factory=list)


# --------------------------------------------------------------------------- headers
def build_header(symbol: str | None, doc_type: str | None,
                 year: int | None, section: str | None) -> str:
    parts = []
    if symbol:
        parts.append(symbol.upper())
    label = DOC_TYPE_LABELS.get(doc_type or "", "")
    if label:
        parts.append(f"{label} {year}" if year else label)
    elif year:
        parts.append(str(year))
    if section:
        parts.append(section)
    return " · ".join(parts)


# --------------------------------------------------------------------------- parsing
def _detect_section(text: str) -> str | None:
    """Best-effort heading for a block: first short heading-like line."""
    for line in (l.strip() for l in text.splitlines()):
        if line and _HEADING_RE.match(line) and not line.isdigit():
            return line[:60]
    return None


def _table_to_markdown(table: list[list]) -> str:
    """Serialise a real table to Markdown, or "" if it looks like page-layout
    noise (too few rows/cols, or mostly empty cells)."""
    rows = [[(c or "").strip().replace("\n", " ") for c in row]
            for row in table if any((c or "").strip() for c in row)]
    if len(rows) < 2:
        return ""
    width = max(len(r) for r in rows)
    if width < 2:
        return ""
    rows = [(r + [""] * width)[:width] for r in rows]
    filled = sum(1 for r in rows for c in r if c)
    if filled / (len(rows) * width) < 0.4:  # sparse grid → layout artifact
        return ""
    out = ["| " + " | ".join(rows[0]) + " |",
           "| " + " | ".join(["---"] * width) + " |"]
    out += ["| " + " | ".join(r) + " |" for r in rows[1:]]
    return "\n".join(out)


def _parse_pdf(path: str) -> list[_Block]:
    """Page-aware extraction with real tables. Falls back to pypdf text if
    pdfplumber is unavailable."""
    blocks: list[_Block] = []
    try:
        import pdfplumber

        with pdfplumber.open(path) as pdf:
            for pageno, page in enumerate(pdf.pages, start=1):
                text = page.extract_text() or ""
                section = _detect_section(text)
                if text.strip():
                    blocks.append(_Block(text=text, kind="prose",
                                         page=pageno, section=section))
                for table in page.extract_tables() or []:
                    md = _table_to_markdown(table)  # "" if layout noise
                    if md:
                        blocks.append(_Block(text=md, kind="table",
                                             page=pageno, section=section))
        return blocks
    except Exception as e:
        logger.warning("chunking: pdfplumber failed for %s (%s); using pypdf", path, e)

    from pypdf import PdfReader

    for pageno, page in enumerate(PdfReader(path).pages, start=1):
        text = page.extract_text() or ""
        if text.strip():
            blocks.append(_Block(text=text, kind="prose", page=pageno,
                                 section=_detect_section(text)))
    return blocks


def _parse_html(path: str) -> list[_Block]:
    from bs4 import BeautifulSoup

    with open(path, errors="ignore") as f:
        soup = BeautifulSoup(f.read(), "html.parser")
    blocks, current = [], None
    for el in soup.find_all(["h1", "h2", "h3", "p", "li", "table"]):
        if el.name in ("h1", "h2", "h3"):
            current = el.get_text(" ", strip=True)[:60]
        elif el.name == "table":
            rows = [[td.get_text(" ", strip=True) for td in tr.find_all(["td", "th"])]
                    for tr in el.find_all("tr")]
            md = _table_to_markdown(rows)
            if md:
                blocks.append(_Block(text=md, kind="table", section=current))
        else:
            txt = el.get_text(" ", strip=True)
            if txt:
                blocks.append(_Block(text=txt, kind="prose", section=current))
    return blocks


def _parse_text(path: str) -> list[_Block]:
    """Plain text / Markdown: split on Markdown headings into sections."""
    with open(path, errors="ignore") as f:
        raw = f.read()
    blocks, section, buf = [], None, []

    def flush():
        body = "\n".join(buf).strip()
        if body:
            blocks.append(_Block(text=body, kind="prose", section=section))

    for line in raw.splitlines():
        if line.startswith("#"):
            flush(); buf = []
            section = line.lstrip("#").strip()[:60]
        else:
            buf.append(line)
    flush()
    if not blocks:  # no headings — keep whole doc as one block
        blocks = [_Block(text=raw.strip(), kind="prose")]
    return blocks


# --------------------------------------------------------------------------- chunking
def _split_sentences(text: str) -> list[str]:
    text = re.sub(r"[ \t]+", " ", text).strip()
    return [s for s in _SENT_RE.split(text) if s.strip()]


def _windows(text: str) -> list[str]:
    """Sentence-aware windows ~CHILD_SIZE chars with CHILD_OVERLAP carry-over."""
    sents = _split_sentences(text)
    if not sents:
        return []
    chunks, cur = [], ""
    for s in sents:
        if cur and len(cur) + len(s) + 1 > CHILD_SIZE:
            chunks.append(cur.strip())
            cur = (cur[-CHILD_OVERLAP:] + " " + s) if CHILD_OVERLAP else s
        else:
            cur = f"{cur} {s}".strip()
    if cur.strip():
        chunks.append(cur.strip())
    return chunks


def _parent_id(source: str, idx: int) -> str:
    import hashlib

    return f"{source}:P{idx}:{hashlib.sha1(f'{source}:{idx}'.encode()).hexdigest()[:8]}"


def chunk_file(path: str, symbol: str | None = None, doc_type: str | None = None,
               year: int | None = None) -> tuple[list[Chunk], dict[str, dict]]:
    """Parse + chunk a file into (child_chunks, parents).

    `parents` maps parent_id -> {text, section, page, symbol, doc_type, year}
    for the small-to-big retrieval store. Child chunks reference their parent.
    """
    ext = os.path.splitext(path)[1].lower()
    source = os.path.basename(path)
    if ext == ".pdf":
        blocks = _parse_pdf(path)
    elif ext in (".html", ".htm"):
        blocks = _parse_html(path)
    else:
        blocks = _parse_text(path)

    # Group consecutive blocks into a parent per page (PDF) or per block (text).
    parents: list[_Parent] = []
    for i, b in enumerate(blocks):
        key = b.page if b.page is not None else i
        if parents and parents[-1].page == b.page and b.page is not None and b.kind == "prose":
            # same page prose already opened a parent — append text to it
            parents[-1].text = (parents[-1].text + "\n" + b.text)[:PARENT_MAX]
            parents[-1]._blocks.append(b)  # type: ignore[attr-defined]
        else:
            p = _Parent(parent_id=_parent_id(source, len(parents)),
                        text=b.text[:PARENT_MAX] if b.kind == "prose" else "",
                        section=b.section, page=b.page)
            p._blocks = [b]  # type: ignore[attr-defined]
            parents.append(p)

    chunks: list[Chunk] = []
    parent_map: dict[str, dict] = {}
    for p in parents:
        header_for = lambda sec: build_header(symbol, doc_type, year, sec)  # noqa: E731
        for b in p._blocks:  # type: ignore[attr-defined]
            if b.kind == "table":
                body = b.text
                chunks.append(Chunk(
                    text=body,
                    embed_text=f"{header_for(b.section)}\n\n{body}",
                    parent_id=p.parent_id, chunk_type="table",
                    section=b.section, page=b.page))
            else:
                for w in _windows(b.text):
                    chunks.append(Chunk(
                        text=w,
                        embed_text=f"{header_for(b.section)}\n\n{w}",
                        parent_id=p.parent_id, chunk_type="text",
                        section=b.section, page=b.page))
        parent_text = p.text or "\n\n".join(
            b.text for b in p._blocks)[:PARENT_MAX]  # type: ignore[attr-defined]
        parent_map[p.parent_id] = {
            "text": parent_text, "section": p.section, "page": p.page,
            "symbol": (symbol or "").upper() or None, "doc_type": doc_type, "year": year,
        }
    logger.info("chunking: %s -> %d parents, %d chunks", source, len(parents), len(chunks))
    return chunks, parent_map
