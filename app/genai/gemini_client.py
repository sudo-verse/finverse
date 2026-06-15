"""Thin wrapper over the google-genai SDK for text generation."""

from app.config import GEMINI_API_KEY, GEMINI_MODEL
from app.utils.logger import logger

_client = None


class GeminiNotConfigured(RuntimeError):
    """Raised when GEMINI_API_KEY is not set."""


def is_configured() -> bool:
    return bool(GEMINI_API_KEY)


def _get_client():
    global _client
    if not GEMINI_API_KEY:
        raise GeminiNotConfigured(
            "GEMINI_API_KEY is not set — add it to .env to enable AI reports."
        )
    if _client is None:
        from google import genai
        _client = genai.Client(api_key=GEMINI_API_KEY)
    return _client


def generate_text(prompt: str, system_instruction: str = None, model: str = None) -> str:
    """Generate text from a prompt. Returns the response text.

    Raises GeminiNotConfigured if no API key is set.
    """
    from google.genai import types

    client = _get_client()
    model = model or GEMINI_MODEL

    config = None
    if system_instruction:
        config = types.GenerateContentConfig(system_instruction=system_instruction)

    response = client.models.generate_content(
        model=model,
        contents=prompt,
        config=config,
    )

    text = getattr(response, "text", None)
    if not text:
        logger.error("Gemini returned an empty response")
        return ""
    return text


def generate_stream(prompt: str, system_instruction: str = None, model: str = None):
    """Yield response text incrementally (generator of str chunks).

    Raises GeminiNotConfigured if no API key is set.
    """
    from google.genai import types

    client = _get_client()
    model = model or GEMINI_MODEL

    config = None
    if system_instruction:
        config = types.GenerateContentConfig(system_instruction=system_instruction)

    for chunk in client.models.generate_content_stream(
        model=model,
        contents=prompt,
        config=config,
    ):
        text = getattr(chunk, "text", None)
        if text:
            yield text


def embed(texts, model: str = None, max_retries: int = 4,
          task_type: str = "RETRIEVAL_DOCUMENT"):
    """Embed a list of texts. Returns a list of vectors (list[list[float]]).

    `task_type` tunes the embedding for its role — `RETRIEVAL_DOCUMENT` when
    indexing corpus chunks (the default), `RETRIEVAL_QUERY` when embedding a
    search query. Matching query↔document task types is an easy, free retrieval
    quality win; mixing them (or leaving both default) costs mAP/NDCG.

    Retries with a backoff on 429 RESOURCE_EXHAUSTED — the free tier allows
    100 embed requests/minute, which page-by-page PDF ingestion can exceed.
    """
    import time

    from google.genai import errors as genai_errors
    from google.genai import types

    from app.config import GEMINI_EMBED_MODEL

    client = _get_client()
    model = model or GEMINI_EMBED_MODEL
    config = types.EmbedContentConfig(task_type=task_type) if task_type else None

    vectors = []
    # batch to stay within request limits
    for i in range(0, len(texts), 100):
        batch = texts[i:i + 100]
        for attempt in range(max_retries + 1):
            try:
                resp = client.models.embed_content(model=model, contents=batch,
                                                    config=config)
                vectors.extend([e.values for e in resp.embeddings])
                break
            except genai_errors.ClientError as e:
                if getattr(e, "code", None) != 429 or attempt == max_retries:
                    raise
                wait = 35 * (attempt + 1)
                logger.warning(f"embed: rate-limited (429), retrying in {wait}s")
                time.sleep(wait)
    return vectors
