"""CLI de bootstrap : `python -m app.seeds.cli`."""

from __future__ import annotations

import asyncio
import logging
import sys

from app.core.database import SessionLocal
from app.seeds.bootstrap import bootstrap


async def _main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s %(name)s %(message)s",
    )
    async with SessionLocal() as session:
        try:
            await bootstrap(session)
            await session.commit()
        except Exception as exc:  # noqa: BLE001
            await session.rollback()
            logging.exception("Bootstrap échoué : %s", exc)
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(_main()))