# NetMon — Project Status

**Last verified:** 2026-10-29 (all results below come from commands actually run on this machine)
**Repo root:** `C:\Users\User\Desktop\netmon`
**Shell:** Windows PowerShell 5.1 (not PowerShell 7 — some cmdlets such as `-SkipHttpErrorCheck` are unavailable)

---

## 1. Objective and technology stack

NetMon is a **local** network monitoring application. It monitors only authorized local
network devices; no arbitrary public IP scanning, no paid APIs, no cloud services, no
frontend until explicitly requested.

| Layer | Choice | Version verified in venv |
|---|---|---|
| Language | Python | 3.13.5 |
| Web framework | FastAPI | 0.162.0 |
| ASGI server | Uvicorn | 0.54.0 |
| ORM | SQLAlchemy (sync) | 2.1.6 |
| Database | SQLite via stdlib `sqlite3` | bundled with Python |
| Tests | pytest | 9.2.0 |
| Test HTTP client | httpx (used by Starlette `TestClient`) | 0.28.1 |
| Transitive | Starlette / Pydantic | 1.10.0 / 2.14.2 |

Only these five direct dependencies are declared: `fastapi`, `uvicorn[standard]`,
`SQLAlchemy`, `pytest`, `httpx`. No dotenv, no Alembic, no Docker, no Redis.

---

## 2. Current milestone

**Milestone 1 — application foundation: COMPLETED.**

Delivered: configuration, SQLAlchemy engine + declarative `Base`, FastAPI entry point, a
database-backed health endpoint, and tests.

**Not** delivered (intentionally out of scope): monitoring models, sessions/CRUD,
network checkers, scheduling, background workers, frontend, Docker.

---

## 3. What was implemented

| File | Purpose |
|---|---|
| `app/__init__.py` | Empty package marker. Deliberately empty to avoid import side effects / cycles. |
| `app/config.py` | Configuration. Frozen `Settings` dataclass plus `load_settings()`, which reads `NETMON_APP_NAME`, `NETMON_APP_VERSION`, `NETMON_DATABASE_URL`, `NETMON_DEBUG` from `os.environ`. Default DB URL: `sqlite:///./netmon.db`. Env is read inside the function (not at import), so tests can build their own `Settings`. |
| `app/database.py` | `Base(DeclarativeBase)` shared by future models. `create_db_engine(url)` adds `check_same_thread=False` for SQLite only. `Database` class owns the engine, exposes `ping()` (runs `text("SELECT 1")`) and `dispose()`. Contains **no** `sessionmaker` and **no** `create_all()` yet. |
| `app/api/__init__.py` | Empty package marker for the API router package. |
| `app/api/health.py` | `GET /health`. Sync `def` handler. Calls `database.ping()`; returns 200 `{"status":"ok","database":"ok"}` or, on `SQLAlchemyError`, logs the exception and returns 503 `{"status":"degraded","database":"unavailable"}`. Never creates or modifies tables. |
| `app/main.py` | `create_app(settings=None)` factory: builds `Database`, stores `settings` and `database` on `app.state`, mounts the health router, disposes the engine in a `lifespan` shutdown hook. Module-level `app = create_app()` is the uvicorn target. |
| `tests/test_health.py` | Three tests: healthy response, simulated DB outage (monkeypatched `ping`), and proof that a health call creates no tables (`inspect(engine).get_table_names() == []`). Fixture uses `tmp_path` for a throwaway SQLite file, so `netmon.db` is never touched by tests. |
| `pytest.ini` | `pythonpath = .` and `testpaths = tests`. Without it, plain `pytest` cannot import `app`. |
| `requirements.txt` | Five bounded dependencies: `fastapi>=0.115,<1`, `uvicorn[standard]>=0.30,<1`, `SQLAlchemy>=2.0,<3`, `pytest>=8,<10`, `httpx>=0.27,<1`. |
| `.gitignore` | `.venv/`, `__pycache__/`, `*.py[cod]`, `.pytest_cache/`, `.env`, `*.db`, `*.sqlite3`, `*.db-journal`, `*.db-wal`, `*.db-shm`. |
| `AGENTS.md` | Project instructions: engineering principles, workflow, learning requirements, restrictions. |
| `PROJECT_STATUS.md` | This handoff document. |

### How to run

```powershell
.\.venv\Scripts\pytest -q                        # tests
.\.venv\Scripts\python -m uvicorn app.main:app --host 127.0.0.1 --port 8010   # dev server
curl.exe -s -w "`nHTTP %{http_code}`n" http://127.0.0.1:8010/health
```

---

## 4. Test results (actual)

Command: `.\.venv\Scripts\pytest -q`
Latest run: **3 passed, 1 warning in 0.74s**

```
...                                                                      [100%]
============================== warnings summary ===============================
.venv\Lib\site-packages\fastapi\testclient.py:1
  ...\fastapi\testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
3 passed, 1 warning in 0.74s
```

Verbose run (earlier same day) listed the three tests by name:

```
tests/test_health.py::test_health_returns_ok PASSED
tests/test_health.py::test_health_reports_503_when_database_is_down PASSED
tests/test_health.py::test_health_creates_no_tables PASSED
```

The single warning originates in the installed libraries, not in project code.

---

## 5. Live API verification (actual)

Both cases were checked against real Uvicorn processes, not only the test client.

**Healthy path** — `uvicorn app.main:app --host 127.0.0.1 --port 8010`:

```
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8010 (Press CTRL+C to quit)
INFO:     127.0.0.1:57595 - "GET /health HTTP/1.1" 200 OK
```
```
HTTP 200
{"status":"ok","database":"ok"}
```

**Failure path** — second instance on port 8011 with
`NETMON_DATABASE_URL='sqlite:///C:/netmon_missing_dir_9f3a/data.db'` (directory does not exist):

```
HTTP 503
{"status":"degraded","database":"unavailable"}
```

The server log showed `sqlite3.OperationalError: unable to open database file` as a logged
traceback, while the HTTP body contained no driver detail — error hiding is confirmed.

Side effect of the healthy call: `netmon.db` was created (0 bytes) and
`inspect(engine).get_table_names()` returned `[]`, confirming `SELECT 1` writes no schema.
Both servers were terminated afterwards (subsequent requests returned `HTTP 000`).

---

## 6. Current project structure

```
netmon/
├── .git/
├── .gitignore
├── .venv/                  (ignored)
├── AGENTS.md
├── PROJECT_STATUS.md       (this file; untracked at time of writing)
├── pytest.ini
├── requirements.txt
├── netmon.db               (generated, 0 bytes, ignored)
├── app/
│   ├── __init__.py         (empty)
│   ├── main.py
│   ├── config.py
│   ├── database.py
│   └── api/
│       ├── __init__.py     (empty)
│       └── health.py
└── tests/
    └── test_health.py
```

No `conftest.py`, no `pyproject.toml`, no README, no migrations directory.

---

## 7. Architectural decisions and why

1. **App factory + `app.state`.** `create_app(settings)` lets tests inject a temporary
   SQLite URL without mutating environment variables or relying on import order. Uvicorn
   still finds the module-level `app`. This is dependency injection, not an abstraction layer.
2. **`lifespan` instead of `@app.on_event`.** FastAPI 0.162 deprecates `on_event`; the
   lifespan context manager runs startup logging and disposes the engine on shutdown.
3. **Health check uses `SELECT 1`, not `create_all()`.** It validates connectivity without
   touching application tables, so it works on an empty database and can never mutate schema.
   Schema creation is deferred to the milestone that introduces models.
4. **Sync `def` endpoint, not `async def`.** The SQLAlchemy call is synchronous. FastAPI runs
   sync endpoints in a worker thread pool, so the event loop is never blocked. An `async def`
   calling blocking SQLite directly would be a bug. `check_same_thread=False` is required
   because pooled connections are reused across those worker threads.
5. **503 + generic body on database failure.** Probes need a distinguishable signal; the DSN
   and driver exception stay in logs. Only `SQLAlchemyError` is caught, so genuine code bugs
   still surface as 500.
6. **`response.status_code = 503` with a dict return.** Keeps one response shape; using
   `HTTPException` would return `{"detail": ...}` and change the contract.
7. **No `sessionmaker` / `get_session()` in Milestone 1.** Nothing needs a session yet;
   unused plumbing is the "unnecessary abstraction" AGENTS.md warns about. It arrives with
   the first model.
8. **`Settings` is a frozen dataclass, not `pydantic-settings`.** No extra dependency for
   four fields. `frozen=True` prevents accidental mutation.
9. **No DB ping at startup.** The app boots even if the database is unreachable and reports
   the problem via `/health` (503) instead of crash-looping. Easy to change to fail-fast.
10. **Version-bounded requirements.** Prevents a future `pip install -r` from pulling
    SQLAlchemy 3.x and breaking code written against the 2.x API.
11. **Test fixture uses a temp file, not `sqlite://`.** In-memory SQLite is per-connection, so
    a pooled engine can silently see a different, empty database. A real file in `tmp_path`
    avoids that trap and leaves no artifacts.

---

## 8. Known warnings and unresolved issues

1. **`StarletteDeprecationWarning`: "Using `httpx` with `starlette.testclient` is deprecated;
   install `httpx2` instead."** Tests pass with httpx 0.28.1. Not fixed because adding a
   package was not approved.
2. **Verbose logging on health failure.** `logger.exception` prints a full traceback on every
   failing poll. Acceptable while learning; consider `logger.warning` or rate limiting if
   health is polled frequently.
3. **Relative SQLite path.** `sqlite:///./netmon.db` resolves against the process CWD, so
   starting uvicorn from another directory creates a second database file.
4. **No check that the database's parent directory exists.** SQLite raises
   `unable to open database file`, which surfaces correctly as 503 but is not pre-validated.
5. **`/health` is unauthenticated.** Bind to `127.0.0.1` only. It reveals just `ok`/`degraded`.
6. **No schema and no migrations.** `Base.metadata` is intentionally empty; there is no
   `create_all()` call and no Alembic.
7. **No `.env` loading.** `.env` is gitignored, but nothing reads it — configuration comes from
   real environment variables only (stdlib `os.environ`).
8. **`PROJECT_STATUS.md` is new and uncommitted** as of this writing.

---

## 9. Git state (verified immediately before this file was written)

| Item | Value |
|---|---|
| Branch | `main` |
| Latest commit | `c211fde` — "Complete Milestone 1: application foundation" |
| Author / date | armanschar &lt;ascharbay@hotmail.com&gt; — 2026-10-29 21:26:23 -0400 |
| Working tree | clean (`git diff HEAD` empty, `git status --short` empty) |
| Remote | `origin` → https://github.com/armanschar/netmon.git |
| Sync | `main...origin/main`, 0 ahead / 0 behind |
| Commit contents | 11 files, 260 insertions (all Milestone 1 files listed in section 3 except this status file) |
| Ignored | `.venv/`, `__pycache__/` (app, app/api, tests), `netmon.db` |

> Note: earlier in development the repository had **no commits** and the branch was
> `master`. The state above is the current, verified state. Adding `PROJECT_STATUS.md`
> creates one new untracked file.

---

## 10. Next milestone and prerequisites

**Next: Milestone 2 — first monitoring data models (`Check` and `CheckResult`).**
These were explicitly deferred from Milestone 1. Their exact fields, relationships and
behaviour have **not** been specified or approved yet, so no design should be assumed.

Before implementation can start:

1. **Approval from the user** for the Milestone 2 scope (no future milestone may be started
   without explicit approval).
2. **Agree the model design:** columns, types, nullability, indexes, and the
   `Check` → `CheckResult` relationship, including whether historical results are required.
3. **Decide session management:** add `sessionmaker` in `app/database.py` plus a FastAPI
   dependency (e.g. `get_db`) — the deliberately missing piece from Milestone 1.
4. **Decide schema creation strategy:** `Base.metadata.create_all()` for learning simplicity
   vs. introducing Alembic migrations. This decision was intentionally postponed.
5. **Decide whether `/health` stays table-free** (`SELECT 1`) — recommended, so health does
   not depend on schema.
6. **Commit `PROJECT_STATUS.md`** (or the Milestone 2 branch) before starting new code.
7. Re-run `.\.venv\Scripts\pytest -q` after every meaningful change and report real output.

Still out of scope until separately approved: network checkers (ping/TCP), scheduling,
background workers, frontend, Docker.

---

## Development rules for the next session

- **OpenCode / DeepSeek is the implementation agent.**
- **Do not implement future milestones without approval.**
- **Explain architectural decisions and code changes** before and alongside implementing them.
- **Inspect existing files before modifying them** — never assume a file is empty or overwrite
  existing work.
- **Run tests after meaningful changes** and report actual output; never claim tests pass
  without running them.
- **Prioritize teaching and maintainable code** over generating large amounts of code.
