# Finverse backend (FastAPI) + background worker.
# The same image serves both: the API (uvicorn) and the worker
# (python -m backend.worker) — the compose file picks the command per service.
FROM python:3.13-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# System deps: build tools for any wheels that need compiling.
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps first for better layer caching.
COPY requirements.txt requirements-api.txt requirements-engine.txt ./
RUN pip install -r requirements-api.txt -r requirements-engine.txt && \
    python -m spacy download en_core_web_sm

COPY . .
RUN chmod +x entrypoint.sh

EXPOSE 8000

# Default command runs the API via the entrypoint script
CMD ["/app/entrypoint.sh"]
