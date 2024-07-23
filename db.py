from typing     import Any

from sqlalchemy import (
    CursorResult,
    Insert,
    Select,
    Update,
)
from sqlalchemy.ext.asyncio        import create_async_engine
from sqlalchemy.ext.asyncio.engine import AsyncEngine


class Db:
    engine : AsyncEngine
    
    @staticmethod
    async def fetch_one(query: Select | Insert | Update, query_exists: bool = False) -> dict[str, Any] | bool:
        async with Db.engine.begin() as conn:
            cursor: CursorResult = await conn.execute(query)
            if query_exists:
                return cursor.scalar()
            return cursor.first()._asdict() if cursor.rowcount > 0 else None

    @staticmethod
    async def fetch_all(query: Select | Insert | Update) -> list[dict[str, Any]]:
        async with Db.engine.begin() as conn:
            cursor: CursorResult = await conn.execute(query)
            return [r._asdict() for r in cursor.all()]

    @staticmethod
    async def execute(query: Insert | Update) -> None:
        async with Db.engine.begin() as conn:
            await conn.execute(query)

    @staticmethod
    def setup(url: str, **kwargs):
        Db.engine = create_async_engine(url, **kwargs)
