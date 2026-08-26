import os

from sqlalchemy import create_engine
from config.utils import DB_URL


def _resolve_db_url() -> str:
    """Return a DB URL that works on the current platform.

    Vercel's filesystem is read-only except for /tmp, so a SQLite file in the
    project directory will crash with FUNCTION_INVOCATION_FAILED. When running
    on Vercel with a SQLite URL, redirect the DB file to /tmp so the function
    can start (note: /tmp is ephemeral — data is lost between invocations).
    """
    url = DB_URL
    if os.getenv("VERCEL") == "1" and url.startswith("sqlite:///"):
        # sqlite:///database.db -> sqlite:////tmp/database.db
        path = url[len("sqlite:///"):]
        if not path.startswith("/"):
            path = "/tmp/" + path
        return f"sqlite:///{path}"
    return url


engine = create_engine(url=_resolve_db_url())

