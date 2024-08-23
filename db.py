from typing     import Any

from sqlalchemy import (
	CursorResult,
	Insert,
	Select,
	Update,
	func
)
from sqlalchemy.ext.asyncio        import create_async_engine
from sqlalchemy.ext.asyncio.engine import AsyncEngine


class Db:
	engine : AsyncEngine

	@staticmethod
	async def fetch_one(query: Select | Insert | Update) -> dict[str, Any] | None:
		async with Db.engine.begin() as conn:
			cursor: CursorResult = await conn.execute(query)
			return cursor.first()._asdict() if cursor.rowcount > 0 else None

	@staticmethod
	async def fetch_all(query: Select | Insert | Update) -> list[dict[str, Any]]:
		async with Db.engine.begin() as conn:
			cursor: CursorResult = await conn.execute(query)
			return [r._asdict() for r in cursor.all()]

	@staticmethod
	async def fetch_exists(query: Select) -> bool:
		async with Db.engine.begin() as conn:
			cursor: CursorResult = await conn.execute(query)
			return bool(cursor.scalar())

	@staticmethod
	async def fetch_count(query: Select) -> int:
		async with Db.engine.begin() as conn:
			count_query = query.with_only_columns(func.count()).order_by(None)
			cursor: CursorResult = await conn.execute(count_query)
			count = cursor.scalar()
			return count if count is not None else 0

	@staticmethod
	async def execute(query: Insert | Update) -> None:
		async with Db.engine.begin() as conn:
			await conn.execute(query)

	@staticmethod
	def setup(url: str, **kwargs):
		Db.engine = create_async_engine(url, **kwargs)
