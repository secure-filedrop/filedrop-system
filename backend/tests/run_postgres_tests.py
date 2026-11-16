"""Run the suite against a private PostgreSQL 18 cluster, then remove that cluster."""

import argparse
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import sys
import tempfile
from uuid import uuid4

from sqlalchemy.engine import URL


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pg-bin", type=Path, help="Directory containing PostgreSQL 18 binaries")
    args = parser.parse_args()
    found = shutil.which("initdb")
    binaries = args.pg_bin or (Path(found).parent if found else None)
    if binaries is None:
        parser.error("Install PostgreSQL 18 or supply --pg-bin; this script does not install/start services.")
    binaries = binaries.resolve()
    version = subprocess.check_output([str(binaries / "postgres"), "--version"], text=True)
    if not version.startswith("postgres (PostgreSQL) 18."):
        parser.error("PostgreSQL 18 binaries are required.")
    print(version.strip(), flush=True)

    # A short private path also avoids macOS's Unix-socket path-length limit.
    root = Path(tempfile.mkdtemp(prefix="filedrop-pg-", dir="/tmp")).resolve()
    data = root / "data"
    sockets = root / "sockets"
    sockets.mkdir(mode=0o700)
    backend = Path(__file__).resolve().parents[1]
    result = 1
    try:
        subprocess.run([
            str(binaries / "initdb"), "-D", str(data), "-U", "filedrop_test_runner",
            "--encoding=UTF8", "--locale=C", "--auth-local=trust", "--auth-host=reject",
        ], check=True, stdout=subprocess.DEVNULL)
        options = shlex.join(["-F", "-c", "listen_addresses=", "-k", str(sockets), "-p", "55432"])
        subprocess.run([
            str(binaries / "pg_ctl"), "-D", str(data), "-l", str(root / "postgres.log"),
            "-o", options, "-w", "-t", "15", "start",
        ], check=True)
        database = "filedrop_test_" + uuid4().hex
        subprocess.run([
            str(binaries / "createdb"), "-h", str(sockets), "-p", "55432",
            "-U", "filedrop_test_runner", database,
        ], check=True)
        environment = os.environ.copy()
        environment.pop("DATABASE_URL", None)
        environment["TEST_DATABASE_URL"] = URL.create(
            "postgresql+psycopg", username="filedrop_test_runner", database=database,
            query={"host": str(sockets), "port": "55432"},
        ).render_as_string(hide_password=False)
        environment["FILEDROP_ALLOW_TEST_DATABASE_RESET"] = "1"
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "-q", "-W", "error"],
            cwd=backend, env=environment,
        ).returncode
        if result == 0:
            migration_environment = environment.copy()
            migration_environment["DATABASE_URL"] = environment["TEST_DATABASE_URL"]
            for operation in ["upgrade head", "current", "check", "downgrade base"]:
                subprocess.run(
                    [sys.executable, "-m", "alembic", *operation.split()],
                    cwd=backend, env=migration_environment, check=True,
                )
            print("PASS migration CLI: upgrade, current, drift check, downgrade.", flush=True)
    finally:
        # pg_ctl is scoped to the fresh, private data directory; no shared PID/port lookup.
        if (data / "postmaster.pid").exists():
            subprocess.run([
                str(binaries / "pg_ctl"), "-D", str(data), "-m", "fast", "-w", "-t", "15", "stop",
            ], check=True)
        shutil.rmtree(root)
        print("Stopped and removed only the temporary test cluster.", flush=True)
    return result


if __name__ == "__main__":
    raise SystemExit(main())
