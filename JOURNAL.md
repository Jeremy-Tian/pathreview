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
