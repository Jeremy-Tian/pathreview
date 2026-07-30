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

---

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Implemented the #155 fix using the preferred approach from PLAN.md — `api/routes/health.py`
now builds the Redis client via `redis.Redis.from_url(settings.redis_url, decode_responses=True)`
instead of the nonexistent `settings.redis_host` / `settings.redis_port`. Confirmed
(via grep) that no other module reads those fields, so the change is safe and localized.
My Week 8 reproduction test now passes, and I added a companion test asserting a
genuinely-unreachable Redis still reports `unhealthy` / 503.

**Next steps:**
Open a draft PR and request peer review in Slack; finalize wording and self-review
against `make check` / `make test-unit`.

**Blockers:**
Local `.venv` is broken (x86_64 wheels on this arm64 Mac), so I couldn't run the
project's `make` targets directly. I reproduced an equivalent clean Python 3.11 venv
to run the unit suite, `ruff`, and `black` on my changes. Need the project venv
rebuilt to run `make check` / `make test-unit` natively (tracked for follow-up).

---

### Check-in 2 (end of week)

**PR link:** _<!-- paste the PR URL here once the draft PR is opened -->_

**Branch:** `fix/155-health-check-redis-host`

**What you built:**
`GET /health` now probes Redis using the configured `redis_url` via
`redis.Redis.from_url(...)`, the single source of truth already on `Settings`.
This removes the `AttributeError` on the phantom `settings.redis_host` field, so the
endpoint reports Redis health based on real reachability instead of always returning 503.

**Tests added or updated:**
- [tests/unit/test_health_redis_config.py](tests/unit/test_health_redis_config.py) —
  regression test for #155: asserts redis `healthy`/200 when reachable (the repro) and
  `unhealthy`/503 when unreachable (guards against a fix that skips the check).
- [tests/conftest.py](tests/conftest.py) — autouse fixture routing structlog into
  stdlib logging so `caplog`-based assertions work in the suite.

**Self-review confirmation:** [ ] make check passes  [ ] make test-unit passes
<!-- Not run natively (broken local .venv). Verified in an equivalent clean venv:
     unit subset shows no new failures vs. baseline; ruff/black clean on changed files;
     the 4 ruff findings and other unit failures are pre-existing and unrelated (see PR). -->

**Draft PR feedback received from:** none yet (draft PR pending)
