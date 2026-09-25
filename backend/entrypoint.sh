#!/bin/sh
set -e

python - <<'PY'
import asyncio
import os
import sys

import asyncpg


def libpq_dsn(url: str) -> str:
    return url.replace("postgresql+asyncpg://", "postgresql://", 1)


async def wait_for_database() -> None:
    dsn = libpq_dsn(os.environ.get("DATABASE_URL", ""))
    for attempt in range(30):
        try:
            connection = await asyncpg.connect(dsn)
            await connection.close()
            return
        except Exception:
            print(f"waiting for database ({attempt})", file=sys.stderr)
            await asyncio.sleep(1)
    print("database did not become ready", file=sys.stderr)
    sys.exit(1)


asyncio.run(wait_for_database())
PY

alembic upgrade head
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
