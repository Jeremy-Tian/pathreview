"""Reproduction test for issue #155.

Health check references ``settings.redis_host`` (and ``settings.redis_port``),
which do not exist on ``Settings`` -- only ``settings.redis_url`` is defined in
``core/config.py``. When ``api/routes/health.py`` builds its Redis probe it
evaluates ``settings.redis_host`` first, which raises ``AttributeError``. That
error is swallowed by the surrounding ``try/except Exception``, so ``GET /health``
does not crash outright -- instead it *always* reports Redis as ``"unhealthy"``
and returns HTTP 503, even when Redis is perfectly reachable.

This test stubs a fully healthy Redis (``ping()`` -> ``True``) and a working DB,
so the only reason Redis can be reported unhealthy is bug #155. It therefore
FAILS on the current code (503 / "unhealthy") and should PASS once #155 is fixed,
regardless of whether the fix adds the missing settings fields or switches the
probe to ``settings.redis_url``.

Issue: https://github.com/ascherj/pathreview/issues/155
"""

import sys
import types

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.routes.health import router
from core.database import get_db


@pytest.fixture
def healthy_redis(monkeypatch):
    """Inject a stub ``redis`` module whose client always pings successfully."""
    fake_redis = types.ModuleType("redis")

    class _FakeRedis:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

        def ping(self):
            return True

    fake_redis.Redis = _FakeRedis
    monkeypatch.setitem(sys.modules, "redis", fake_redis)
    return fake_redis


@pytest.fixture
def client(healthy_redis):
    """FastAPI test client with the DB dependency overridden to a healthy stub."""

    class _FakeDB:
        async def execute(self, *args, **kwargs):
            return None

    async def _fake_get_db():
        yield _FakeDB()

    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_db] = _fake_get_db
    return TestClient(app)


@pytest.mark.unit
def test_health_reports_redis_healthy_when_reachable(client):
    """With Redis reachable, /health should return 200 and redis 'healthy'.

    Currently fails (503 / 'unhealthy') because of issue #155 -- the probe
    raises AttributeError on settings.redis_host before it can ping Redis.
    """
    resp = client.get("/health")
    body = resp.json()
    # On a 503 FastAPI nests the payload under "detail"; unwrap either shape.
    payload = body.get("detail", body)

    assert payload["dependencies"]["redis"] == "healthy", (
        "Redis is reachable (ping succeeds) but the health check reports it "
        "unhealthy -- reproduces issue #155 (settings.redis_host does not exist)."
    )
    assert resp.status_code == 200
