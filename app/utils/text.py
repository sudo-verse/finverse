"""Text cleanup helpers shared by ingestion and display layers."""

import html
import re

_TAG_RE = re.compile(r"<[^>]*>")
_UNTERMINATED_TAG_RE = re.compile(r"<[^>]*$")  # tag cut off by truncation
_WS_RE = re.compile(r"\s+")


def strip_html(text: str | None) -> str:
    """Strip HTML tags/entities and collapse whitespace.

    Handles tags left unterminated by column truncation (e.g. the 1024-char
    cap on news_signals.news cutting through an <a href="..."> attribute).
    """
    if not text:
        return ""
    text = html.unescape(text)
    text = _TAG_RE.sub(" ", text)
    text = _UNTERMINATED_TAG_RE.sub(" ", text)
    return _WS_RE.sub(" ", text).strip()
