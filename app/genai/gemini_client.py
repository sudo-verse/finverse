"""Thin wrapper over the google-genai SDK with multi-key quota rotation.

The free tier caps embeddings per project per day (1000), counted per chunk —
enough to stall a corpus re-embed. When several keys from different projects are
configured (GEMINI_API_KEY, GEMINI_API_KEY2, …) we rotate to the next key on a
429 RESOURCE_EXHAUSTED, multiplying the effective daily budget; a key that hits
its daily cap is parked for the rest of the day so we don't keep retrying it.
"""

import re
import time

from app.config import GEMINI_API_KEY, GEMINI_API_KEYS, GEMINI_MODEL
from app.utils.logger import logger

_clients: dict[int, object] = {}     # key index -> genai.Client
_idx = 0                             # current key pointer (round-robin)
_parked: dict[int, float] = {}       # key index -> unix time it can be retried
_DEFAULT_PARK = 60                   # fallback park if the 429 gives no retry delay

_RETRY_RE = re.compile(r"retry in ([0-9.]+)s|retryDelay['\":\s]+([0-9.]+)s", re.IGNORECASE)


def _retry_delay(exc) -> float:
    """Seconds the API asked us to wait (per-minute ~30-60s; daily ~thousands)."""
    m = _RETRY_RE.search(str(exc))
    if m:
        return float(m.group(1) or m.group(2))
    return _DEFAULT_PARK


class GeminiNotConfigured(RuntimeError):
    """Raised when no GEMINI_API_KEY is set."""


def is_configured() -> bool:
    return bool(GEMINI_API_KEYS or GEMINI_API_KEY)


def _keys() -> list[str]:
    return GEMINI_API_KEYS or ([GEMINI_API_KEY] if GEMINI_API_KEY else [])


def _client_at(idx: int):
    if idx not in _clients:
        from google import genai

        _clients[idx] = genai.Client(api_key=_keys()[idx])
    return _clients[idx]


def _get_client():
    """Backwards-compatible accessor: the currently-active client."""
    keys = _keys()
    if not keys:
        raise GeminiNotConfigured(
            "GEMINI_API_KEY is not set — add it to .env to enable AI features."
        )
    return _client_at(_idx % len(keys))


def _is_quota_error(exc) -> bool:
    from google.genai import errors as genai_errors

    return isinstance(exc, genai_errors.ClientError) and getattr(exc, "code", None) == 429


def _is_server_error(exc) -> bool:
    from google.genai import errors as genai_errors

    return isinstance(exc, genai_errors.ServerError) or \
        getattr(exc, "code", None) in (500, 502, 503, 504)


def _advance_to_unparked() -> bool:
    """Point _idx at the next key whose park has expired. False if all parked."""
    global _idx
    keys = _keys()
    now = time.time()
    for step in range(1, len(keys) + 1):
        cand = (_idx + step) % len(keys)
        if _parked.get(cand, 0) <= now:
            _idx = cand
            logger.info("gemini: rotated to key #%d of %d", _idx + 1, len(keys))
            return True
    return False


def _call_with_rotation(make_call, max_cycles: int = 12, max_transient: int = 6):
    """Run make_call(client) with resilience:

      - 429 (quota): park the spent key for exactly the delay the API asked for
        and rotate to another. When every key is parked, sleep until the soonest
        frees up (per-minute limits clear in ~60s; daily-capped keys park for
        hours and get skipped). Up to `max_cycles` such sleeps.
      - 5xx (transient server error): exponential-backoff retry on the same key.
      - anything else: raise.

    `max_cycles=0` makes the quota path fail fast (query path → BM25 fallback).
    """
    keys = _keys()
    if not keys:
        raise GeminiNotConfigured("GEMINI_API_KEY is not set.")
    quota_cycles = transient = 0
    while True:
        try:
            return make_call(_get_client())
        except Exception as e:
            if _is_quota_error(e):
                _parked[_idx % len(keys)] = time.time() + _retry_delay(e)
                if _advance_to_unparked():
                    continue  # another key is free — try it immediately
                if quota_cycles >= max_cycles:
                    raise RuntimeError("gemini: all API keys exhausted (429)") from e
                quota_cycles += 1
                wait = max(5.0, min(min(_parked.values()) - time.time(), 90.0))
                logger.warning("gemini: all keys rate-limited; sleeping %.0fs", wait)
                time.sleep(wait)
                _advance_to_unparked()
            elif _is_server_error(e):
                transient += 1
                if transient > max_transient:
                    raise
                wait = min(2 ** transient, 20)
                logger.warning("gemini: server error (%s); retry %d in %ss",
                               getattr(e, "code", "5xx"), transient, wait)
                time.sleep(wait)
            else:
                raise


def generate_text(prompt: str, system_instruction: str = None, model: str = None) -> str:
    from google.genai import types

    model = model or GEMINI_MODEL
    config = types.GenerateContentConfig(system_instruction=system_instruction) \
        if system_instruction else None

    def call(client):
        return client.models.generate_content(model=model, contents=prompt, config=config)

    response = _call_with_rotation(call)
    text = getattr(response, "text", None)
    if not text:
        logger.error("Gemini returned an empty response")
        return ""
    return text


def generate_stream(prompt: str, system_instruction: str = None, model: str = None,
                    max_attempts: int = 5):
    """Yield response text incrementally.

    Streaming requests are lazy, so quota/5xx errors surface *during* iteration,
    not at connect. We can't un-emit tokens, so we only retry (from scratch,
    rotating keys / backing off) while nothing has been yielded yet — which
    covers the common "model busy" 503 that hits before the first token."""
    from google.genai import types

    model = model or GEMINI_MODEL
    config = types.GenerateContentConfig(system_instruction=system_instruction) \
        if system_instruction else None

    def call(client):
        return client.models.generate_content_stream(model=model, contents=prompt, config=config)

    attempt = 0
    while True:
        emitted = False
        try:
            for chunk in _call_with_rotation(call):
                text = getattr(chunk, "text", None)
                if text:
                    emitted = True
                    yield text
            return
        except Exception as e:
            attempt += 1
            if emitted or attempt >= max_attempts or not (
                _is_server_error(e) or _is_quota_error(e)):
                raise
            if _is_quota_error(e):
                _parked[_idx % len(_keys())] = time.time() + _retry_delay(e)
                _advance_to_unparked()
            wait = min(2 ** attempt, 20)
            logger.warning("gemini: stream failed pre-token (%s); retry %d in %ss",
                           getattr(e, "code", "err"), attempt, wait)
            time.sleep(wait)


def embed(texts, model: str = None, max_retries: int = 20,
          task_type: str = "RETRIEVAL_DOCUMENT"):
    """Embed a list of texts. Returns a list of vectors (list[list[float]]).

    `task_type` tunes the embedding for its role — `RETRIEVAL_DOCUMENT` when
    indexing corpus chunks (the default), `RETRIEVAL_QUERY` for a search query.

    Rotates across configured keys on 429 to multiply the daily quota.
    `max_retries=0` makes a query path fail fast instead of stalling.
    """
    from google.genai import types

    from app.config import GEMINI_EMBED_MODEL

    model = model or GEMINI_EMBED_MODEL
    config = types.EmbedContentConfig(task_type=task_type) if task_type else None

    vectors = []
    # Keep batches under the free-tier per-minute embed cap (100 requests/min):
    # a batch of 100 trips it in one call, so 50 leaves headroom for rotation.
    for i in range(0, len(texts), 50):
        batch = texts[i:i + 50]

        def call(client):
            resp = client.models.embed_content(model=model, contents=batch, config=config)
            return [e.values for e in resp.embeddings]

        vectors.extend(_call_with_rotation(call, max_cycles=max_retries))
    return vectors
