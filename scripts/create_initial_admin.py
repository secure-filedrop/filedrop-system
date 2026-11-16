"""Create the first administrator account for a migrated Secure File Drop database.

Run explicitly by an administrator from an interactive terminal, with the backend
virtual environment active and DATABASE_URL exported:

    python scripts/create_initial_admin.py

The password is read privately and never accepted as a command-line argument.
The command refuses to run if any administrator already exists. There are no
default credentials and no public registration.
"""

import argparse
import getpass
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from app.auth.security import CredentialPolicyError  # noqa: E402
from app.core.config import ConfigurationError  # noqa: E402
from app.database.db import DatabaseOperationError, create_database_engine, session_scope  # noqa: E402
from app.services.auth_service import AccountExistsError, InitialAdminExistsError, create_initial_admin  # noqa: E402


def main(argv=None, *, read_line=input, read_secret=getpass.getpass, interactive=None) -> int:
    # No options are accepted, so a password can never arrive through argv/shell history.
    argparse.ArgumentParser(description="Interactively create the first administrator account.").parse_args(argv)
    if not (sys.stdin.isatty() if interactive is None else interactive):
        print("Run this command from an interactive terminal so the password is read privately.", file=sys.stderr)
        return 2

    email = read_line("Administrator email: ")
    password = read_secret("Password: ")
    if read_secret("Confirm password: ") != password:
        print("Passwords did not match; no account was created.", file=sys.stderr)
        return 1

    try:
        engine = create_database_engine()
        try:
            with session_scope(engine) as session:
                create_initial_admin(session, email, password)
        finally:
            engine.dispose()
    except (InitialAdminExistsError, AccountExistsError) as error:
        print(error, file=sys.stderr)
        return 1
    except (CredentialPolicyError, ConfigurationError) as error:
        # These messages are written without the supplied values.
        print(f"{error} No account was created.", file=sys.stderr)
        return 1
    except DatabaseOperationError:
        print("Database operation failed; check that migrations are applied. No account was created.",
              file=sys.stderr)
        return 1
    print("Created the initial administrator account.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
