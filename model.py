from typing     import Any, Iterable, Callable

from sqlalchemy import (
	Table,
	insert,
	update,
	select,
	exists,
	delete,
	and_,

	Select,
	Insert,
	Update
)
from sqlalchemy.orm import aliased

from .db import Db


class Model:
	__aliases_cache    : dict = None
	__decorators_cache : dict[str, Callable] = None

	__pk_field__         = 'id'
	__time_order_field__ = 'created'
	__related__          = {}
	"""
	:__related__
	uses for join requests automation
	example signature

	__related__ = {
		'country' : {
			'table' : 'countries',
			'on'    : ('country_id', 'id')
		}
	}
	"""

	#################### POST PROCESSING ####################

	@classmethod
	def _get_decorators(cls) -> dict[str, Callable]:
		if cls.__decorators_cache is None:
			cls.__decorators_cache = {}
			for name in cls.__dict__:
				if name.startswith('define_'):
					f = getattr(cls, name)
					if callable(f):
						cls.__decorators_cache[name[7:]] = f
		return cls.__decorators_cache

	@classmethod
	def _decorate_record(cls, record: dict | bool | None) -> dict | None:
		if not isinstance(record, dict) or record is None:
			return record
		for name, f in cls._get_decorators().items():
			record[name] = f(record)
		return record

	@classmethod
	def _decorate_records(cls, records: list) -> list:
		return [
			cls._decorate_record(r)
			for r in records
		]

	@staticmethod
	def normalize_joined(sub_models: Iterable[str], data: dict) -> dict:
		"""
		prepare data from puerpy.model.Model.get_by_join()
		for BaseModel.model_validate method
		"""
		normalized = {}

		for key, value in data.items():
			splitted_key = key.split('__')
			sub_model    = splitted_key[0]

			if sub_model in sub_models:
				if not normalized.get(sub_model):
					normalized[sub_model] = {}
				normalized[sub_model][splitted_key[1]] = value
			else:
				normalized[key] = value

		return normalized

	@staticmethod
	def normalize_joined_list(sub_models: Iterable[str], data: Iterable[dict]) -> list[dict]:
		"""
		prepare data from puerpy.model.Model.get_all_join()
		for RootModel[list[BaseModel]].model_validate method
		"""
		return [Model.normalize_joined(sub_models, d) for d in data]

	#################### QUERY BUILDING ####################

	@classmethod
	def aliases(cls) -> dict:
		if not cls.__aliases_cache:
			cls.__aliases_cache = {
				name: aliased(Table(cls.__related__[name]['table'], cls.metadata))
				for name in cls.__related__
			}
		return cls.__aliases_cache

	@classmethod
	def q_filter(cls, q: Select, filters: Iterable = None) -> Select:
		if filters:
			q = q.where(and_(*filters))
		return q

	@classmethod
	def q_join(cls, tables: Iterable[str], filters: Iterable = None) -> Select:
		aliases = cls.aliases()
		labels = [
			getattr(aliases[t].c, c.key).label(f'{t}__{c.key}')
			for t in tables
			for c in aliases[t].c
		]

		q = cls.q_filter(
			select(cls, *labels)
				.select_from(cls),
			filters
		)

		for t in tables:
			on = cls.__related__[t]['on']
			q = q.join(
				aliases[t],
				getattr(cls, on[0]) == getattr(aliases[t].c, on[1])
			)
		return q

	#################### DB OPERATIONS ####################

	@classmethod
	async def fetch_one(cls,
		query : Select | Insert | Update,
	) -> dict[str, Any] | None:
		"""Can be extended in child classes"""
		return cls._decorate_record(
			await Db.fetch_one(query)
		)

	@classmethod
	async def fetch_all(cls,
		query: Select | Insert | Update
	) -> list[dict[str, Any]]:
		"""Can be extended in child classes"""
		return cls._decorate_records(
			await Db.fetch_all(query)
		)

	@classmethod
	async def fetch_exists(cls, query: Select) -> bool:
		"""Can be extended in child classes"""
		return await Db.fetch_exists(query)

	@classmethod
	async def fetch_count(cls, query: Select) -> int:
		"""Can be extended in child classes"""
		return await Db.fetch_count(query)

	@classmethod
	async def execute(cls, query: Insert | Update) -> None:
		"""Can be extended in child classes"""
		return await Db.execute(query)

	#################### SQL OPERATIONS ####################

	@classmethod
	async def create(cls, data: dict) -> dict:
		return cls._decorate_record(await Db.fetch_one(
			insert(cls)
				.values(**data)
				.returning(cls)
		))

	@classmethod
	async def update(cls, pk: Any, to_update: dict) -> dict:
		return await cls.fetch_one(
			update(cls)
				.where(getattr(cls, cls.__pk_field__) == pk)
				.values(**to_update)
				.returning(cls)
		)

	@classmethod
	async def get_by(cls, field: str, value: Any) -> dict | None:
		return await cls.fetch_one(
			select(cls)
				.where(getattr(cls, field) == value)
				.limit(1)
		)

	@classmethod
	async def get_one(cls, filters: Iterable = None) -> dict | None:
		return await cls.fetch_one(
			cls.q_filter(select(cls), filters)
				.limit(1)
		)

	@classmethod
	async def get_one_with_join(cls, tables: Iterable[str], filters: Iterable = None) -> dict | None:
		if res := await cls.fetch_one(
			cls.q_join(tables, filters)
				.limit(1)
		):
			return cls.normalize_joined(tables, res)
		return None

	@classmethod
	async def get_all(cls) -> list[dict]:
		return await cls.fetch_all(select(cls))

	@classmethod
	async def get_many(cls, filters: Iterable = None) -> list[dict]:
		return await cls.fetch_all(cls.q_filter(select(cls), filters))

	@classmethod
	async def get_many_with_join(cls, tables: Iterable[str], filters: Iterable = None) -> list[dict]:
		return cls.normalize_joined_list(tables, await cls.fetch_all(
			cls.q_join(tables, filters)
		))

	@classmethod
	async def get_many_last(cls,
		limit    : int  = None,
		order_by : str  = None,
		asc      : bool = True
	) -> list[dict]:

		if not order_by:
			order_by = cls.__time_order_field__

		order = getattr(cls, order_by)

		if asc : order = order.asc()
		else   : order = order.desc()

		q = select(cls).order_by(order)

		if limit:
			q = q.limit(limit)

		return await cls.fetch_all(q)

	@classmethod
	async def exists(cls, field: str, value: Any) -> bool:
		return await cls.fetch_exists(
			select(
				exists()
					.where(getattr(cls, field) == value)
			)
		)

	@classmethod
	async def delete(cls, pk: Any):
		await cls.execute(
			delete(cls)
				.where(getattr(cls, cls.__pk_field__) == pk)
		)
