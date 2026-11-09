# Secure File Drop backend

This foundation provides FastAPI, a public liveness endpoint, and a PostgreSQL
connection/session layer with migrations for `users`, `files`, and `audit_logs`. Authentication,
dashboard pages, uploads/downloads, and audit logging remain planned in the
[Phase 1 roadmap](../docs/mvp-roadmap.md).

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
SQLAlchemy (models/sessions), Psycopg (PostgreSQL driver), Alembic (migrations),
and `pytest` plus `httpx2` (testing). Direct dependencies are pinned to
the versions used for validation; transitive dependencies are resolved by pip.
The current Starlette test client, re-exported by FastAPI, uses `httpx2`;
its older `httpx` fallback is deprecated.

The web app and health check need no database configuration or uploaded files.
Only explicit database work and migration commands require `DATABASE_URL`.

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

## PostgreSQL setup and migrations

Use PostgreSQL **18** for development and integration tests. An existing local
installation is supported; the application does not install or start PostgreSQL.
Keep development and disposable test databases separate. No shared-server or
cloud configuration is included in this slice.

Have a local development database and appropriate database role provisioned by
its administrator. With the virtual environment active, from `backend/`, export
the connection URL locally (replace the placeholders and URL-encode special
characters in credentials):

```sh
export DATABASE_URL='postgresql+psycopg://USERNAME:PASSWORD@127.0.0.1:5432/filedrop'
python -m alembic upgrade head
python -m alembic current
python -m alembic check
```

`backend/.env.example` documents the variables; it is a template and is not loaded
automatically. Plain `postgresql://` URLs are also accepted and explicitly use
the Psycopg 3 driver. Never put real connection URLs in `alembic.ini`, commit
them, or print them in logs.

Migrations live under `app/database/migrations/`. They run only when requested;
application import/startup never creates tables or runs migrations. Review each
migration before applying it. `alembic check` detects changes supported by
autogeneration; it does not replace review of constraints and expression indexes.
Downgrades remove schema/data and should be used only on disposable databases or
as part of a separately reviewed recovery plan.

The implemented tables are `users`, `files`, and `audit_logs`. The column and
foreign-key contracts are recorded in [database-schema.md](../docs/database-schema.md).
The second migration preserves existing users, adds only file metadata and audit
records, and can be downgraded independently to the user-only revision.

Audit user/file IDs may be null for events such as unknown-user login failures.
Non-null IDs must reference existing rows. Soft deletion/deactivation preserves
audit references; hard deletion of referenced users/files is restricted. Details
are JSON objects and optional addresses use PostgreSQL INET. Services must exclude
secrets from audit details; the schema is not a redaction or append-only mechanism.

No accounts, uploaded files, or actual audit events are seeded. Login, upload and
download handlers, permission checks, and password hashing are still separate tasks.

`create_database_engine()` is explicit and lazy. The caller owns the engine and
disposes it when finished. `session_scope(engine)` supplies a short-lived session:
services call `session.commit()` explicitly; closing rolls back uncommitted work,
including on exceptions. Database failures from this context raise a generic
`DatabaseOperationError`; its optional five-character `sqlstate` supports safe
diagnostics or later domain-error mapping without exposing the original driver
exception or URL. Expected constraints should be mapped by the future service,
not returned as raw database errors.
Future routes using synchronous sessions should use synchronous FastAPI handlers
or dependencies, rather than blocking the event loop in an async handler.

## Test without PostgreSQL

With the virtual environment active, from `backend/`:

```sh
env -u DATABASE_URL -u TEST_DATABASE_URL -u FILEDROP_ALLOW_TEST_DATABASE_RESET python -m pytest -q -W error
```

This runs health/configuration/target-guard checks; PostgreSQL integration tests
skip explicitly when `TEST_DATABASE_URL` is absent. No running server or database
is required. The existing authentication and file test files remain placeholders.

## Full suite with an isolated PostgreSQL instance

Install PostgreSQL 18 binaries through your normal package manager or the
[official PostgreSQL downloads](https://www.postgresql.org/download/). The test
runner needs `postgres`, `initdb`, `pg_ctl`, and `createdb`. On macOS with Homebrew,
run the following from `backend/` with the virtual environment active:

```sh
python tests/run_postgres_tests.py --pg-bin "$(brew --prefix postgresql@18)/bin"
```

On macOS/Linux with PostgreSQL 18 binaries already on `PATH`:

```sh
python tests/run_postgres_tests.py
```

The runner creates a new private temporary cluster and a random `filedrop_test_*`
database, accepts only Unix-socket connections inside the private directory, and
does not listen on TCP. It ignores an inherited development URL. It runs the
suite, verifies the migration CLI, then stops and removes only its own cluster.
Do not run it as root. No background service or persistent development DB is created.

To target an already-provisioned disposable PostgreSQL 18 test database instead:

```sh
export TEST_DATABASE_URL='postgresql+psycopg://TEST_USERNAME:TEST_PASSWORD@127.0.0.1:5432/filedrop_test_local'
FILEDROP_ALLOW_TEST_DATABASE_RESET=1 python -m pytest -q -W error
```

This target must be empty and named exactly `filedrop_test` or start with
`filedrop_test_`. The reset flag is explicit permission for tests to create/remove
their tables there. Tests reject a configured development target and preexisting
user relations, types, or functions before applying migrations. Never point this
command at valuable data; the isolated runner is the preferred option.

Use `python -m pytest` from `backend/` so the existing `app/` namespace is on
the import path. Check `git status --short` before committing; the virtual
environment and generated Python/test caches should remain ignored.

References: [FastAPI testing](https://fastapi.tiangolo.com/tutorial/testing/),
[Starlette test client](https://starlette.dev/testclient/), and
[Uvicorn settings](https://uvicorn.dev/settings/). Database references:
[SQLAlchemy sessions](https://docs.sqlalchemy.org/en/20/orm/session_basics.html),
[Psycopg dialect](https://docs.sqlalchemy.org/en/20/dialects/postgresql.html#module-sqlalchemy.dialects.postgresql.psycopg),
and [Alembic migrations](https://alembic.sqlalchemy.org/en/latest/).
