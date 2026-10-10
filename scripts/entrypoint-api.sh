#!/usr/bin/env bash
set -euo pipefail

echo "[entrypoint] Attente de PostgreSQL…"
python - <<'PY'
import asyncio, os, sys
import asyncpg

url = os.environ["DATABASE_URL"].replace("postgresql+asyncpg://", "postgresql://")

async def wait_for_db() -> None:
    last_err = None
    for _ in range(60):
        try:
            conn = await asyncpg.connect(url)
            await conn.close()
            print("[entrypoint] PostgreSQL OK")
            return
        except Exception as e:
            last_err = e
            await asyncio.sleep(1)
    print(f"[entrypoint] PostgreSQL injoignable : {last_err}", file=sys.stderr)
    sys.exit(1)

asyncio.run(wait_for_db())
PY

echo "[entrypoint] Migrations Alembic…"
alembic upgrade head

echo "[entrypoint] Bootstrap des données de référence…"
python -m app.seeds.cli

echo "[entrypoint] Démarrage d'Uvicorn…"
exec uvicorn app.main:app --host "${API_HOST:-0.0.0.0}" --port "${API_PORT:-8000}"