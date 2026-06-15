"""Background jobs: task wrappers call the right services; the queue + API
degrade to 503 when Redis isn't configured (the test default)."""

import asyncio

import pytest

from backend.core.exceptions import ServiceUnavailableError


class TestTasks:
    def test_sentiment_task_runs_service(self, monkeypatch):
        from backend import tasks
        from backend.services.sentiment_service import sentiment_service

        monkeypatch.setattr(sentiment_service, "refresh_universe",
                            lambda: {"scored": 5, "skipped": 0, "failed": 0})
        result = asyncio.run(tasks.refresh_sentiment_universe(ctx=None))
        assert result["scored"] == 5

    def test_ingest_task_passes_symbol(self, monkeypatch):
        import app.etl.ingest_documents as ing
        from backend import tasks

        monkeypatch.setattr(ing, "ingest_documents",
                            lambda symbol=None: {"files": 1, "symbol": symbol})
        result = asyncio.run(tasks.ingest_documents(ctx=None, symbol="TCS"))
        assert result["symbol"] == "TCS"


class TestQueueGuard:
    def test_enqueue_requires_redis(self, monkeypatch):
        from backend.core import config, queue

        monkeypatch.setattr(config.settings, "redis_url", "", raising=False)
        queue._pool = None
        with pytest.raises(ServiceUnavailableError):
            asyncio.run(queue.enqueue("refresh_sentiment_universe"))


class TestJobsApi:
    def test_enqueue_503_without_redis(self, register, client, monkeypatch):
        from backend.core import config

        monkeypatch.setattr(config.settings, "redis_url", "", raising=False)
        headers = register("ops@example.com")
        r = client.post("/api/jobs/sentiment-refresh", headers=headers)
        assert r.status_code == 503

    def test_jobs_require_auth(self, client):
        assert client.post("/api/jobs/sentiment-refresh").status_code == 401
