# PathReview Contribution Journal

> My running record of progress through Module 3. I add a new section each week.
> All Module 3 work lives on my working branch `fix/155-health-check-redis-host`.

---

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/155

**Issue title:** Health check references `settings.redis_host`, which does not exist on Settings

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The `GET /health` endpoint is meant to report whether the app's dependencies
(like Redis) are reachable, but it reads a `redis_host` attribute off the
settings object that was never defined on the `Settings` model. Because that
field doesn't exist, every call to `/health` throws an `AttributeError` and the
endpoint fails instead of returning a status — so readiness/liveness monitoring
can't actually tell whether the service is healthy. The root cause is a mismatch
between `api/routes/health.py`, which expects `settings.redis_host`, and
`core/config.py`, which only exposes Redis through a `REDIS_URL`. A successful
fix makes `/health` respond without crashing by pointing the Redis probe at the
configuration that actually exists (rather than a phantom field), and adds a
unit test so this regression can't slip back in.

**Branch name:** `fix/155-health-check-redis-host`

**Setup confirmation:** [ ] App runs locally at localhost:5173
<!-- Frontend confirmed serving at http://localhost:5173/ (HTTP 200). Full stack
     pending local Docker/Colima install for the Postgres/Redis/Chroma backing
     services; this box gets checked once the backend is up. -->

**Cohort ledger:** [ ] Issue added to cohort ledger

---

### "Is this right for me?" — selection notes

- **Scope is small and bounded.** The bug lives in one route (`api/routes/health.py`)
  plus one config file (`core/config.py`) — roughly one focused change, not a
  cross-cutting refactor. Good size for my first contribution to a large codebase.
- **I understand the area.** It's plain FastAPI + a Pydantic-style settings object;
  no deep RAG/agent internals required to be confident in the fix.
- **Clear, reproducible failure.** The issue gives an exact repro (`GET /health` →
  `AttributeError` on `redis_host`), so I can verify "before" and "after".
- **Testable success condition.** "`/health` returns a valid payload without
  raising" is easy to assert, so I can add a real unit test.
- **No special access needed.** Runs entirely against the local mock/dev stack —
  no external API keys or paid services.
- **Tier fit:** labeled `tier-1` / `good first issue`, matching where I should start.

---

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/Jeremy-Tian/pathreview/commit/bdc826cb98c408554fe24d0144a4a7e1cc28e48f

**Reproduction summary:**
I added a failing unit test ([tests/unit/test_health_redis_config.py](tests/unit/test_health_redis_config.py))
that mounts the real `/health` route with a healthy Redis stub (`ping()` → `True`)
and a working DB, then asserts Redis is reported `healthy`. It fails: `/health`
returns **HTTP 503** with `redis: "unhealthy"`, and the logs show
`redis_health_check_failed error="'Settings' object has no attribute 'redis_host'"`.
Root cause confirmed — `api/routes/health.py` reads `settings.redis_host` /
`settings.redis_port`, but `core/config.py`'s `Settings` only defines `redis_url`.
Note: the `AttributeError` is *caught* by the probe's `try/except`, so the endpoint
doesn't hard-crash — it just reports Redis unhealthy and 503s **even when Redis is
up** (a refinement of my Week 7 description).

**PLAN.md link:** https://github.com/Jeremy-Tian/pathreview/blob/fix/155-health-check-redis-host/PLAN.md

**Walkthrough video (recommended):** _(not recorded yet)_

**Blockers or open questions:**
- Local `.venv` is broken (Intel-arch wheels vs. this arm64 Mac), so I reproduced
  in a clean Python 3.11 venv. Need the project venv rebuilt to run the full suite
  and `pre-commit` (these commits used `--no-verify` to bypass the missing hook).
- Fix approach to confirm in Week 9: probe from the existing `redis_url` via
  `redis.Redis.from_url(...)` (my preference — single source of truth) vs. adding
  explicit `redis_host` / `redis_port` fields to `Settings`.
