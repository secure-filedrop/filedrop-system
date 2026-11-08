# Secure File Drop backend

This foundation provides a FastAPI application and a public liveness endpoint.
Authentication, dashboard pages, uploads/downloads, PostgreSQL, and audit logging
are planned in the [Phase 1 roadmap](../docs/mvp-roadmap.md).

## Local setup

Use Python 3.14 (validated with Python 3.14.4). From the repository root, run
these commands on macOS/Linux:

```sh
cd backend
python3.14 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

The requirements include `fastapi` (web framework), `uvicorn` (local ASGI server),
and `pytest` plus `httpx2` (endpoint testing). Direct dependencies are pinned to
the versions used for validation; transitive dependencies are resolved by pip.
The current Starlette test client, re-exported by FastAPI, uses `httpx2`;
its older `httpx` fallback is deprecated.

This foundation needs no `.env` file, credentials, database, or uploaded files.

## Run locally

With the virtual environment active, from `backend/`:

```sh
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

The server listens on this computer only. In a second terminal:

```sh
curl -i http://127.0.0.1:8000/health
```

Expected response: HTTP 200 with JSON `{"status":"ok"}`. This means the app is
running; it does not check database or storage readiness. The route exposes no
configuration details. See the [API endpoint documentation](../docs/api-endpoints.md).

Interactive API docs are available at <http://127.0.0.1:8000/docs> while the
server is running. Stop the server with `Ctrl+C`.

If port 8000 is already in use, choose another port with `--port` and update
the health-check URL to match; keep the host set to `127.0.0.1`.

## Test

With the virtual environment active, from `backend/`:

```sh
python -m pytest
```

The health test checks the HTTP status, JSON content type, and exact response
body using FastAPI's test client. No running server or database is required.
The existing authentication and file test files remain placeholders for later tasks.

Use `python -m pytest` from `backend/` so the existing `app/` namespace is on
the import path. Check `git status --short` before committing; the virtual
environment and generated Python/test caches should remain ignored.

References: [FastAPI testing](https://fastapi.tiangolo.com/tutorial/testing/),
[Starlette test client](https://starlette.dev/testclient/), and
[Uvicorn settings](https://uvicorn.dev/settings/).
