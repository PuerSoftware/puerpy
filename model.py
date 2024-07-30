from typing     import Any

from sqlalchemy import (
    Table,
    insert,
    update,
    select,
    exists,
    delete
)
from sqlalchemy.orm import aliased

from .db import Db


class Model:
    __aliases_cache: dict = None

    __pk_field__  = 'id'
    __related__   = {}
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
    @classmethod
    def _aliases(cls) -> dict:
        if not cls.__aliases_cache:
            cls.__aliases_cache = {
                name: aliased(Table(cls.__related__[name]['table'], cls.metadata))
                for name in cls.__related__
            }
        return cls.__aliases_cache

    @classmethod
    async def create(cls, data: dict) -> dict:
        return await Db.fetch_one(
            insert(cls)
                .values(**data)
                .returning(cls)    
        )
    
    @classmethod
    async def update(cls, pk: Any, to_update: dict) -> dict:
        return await Db.fetch_one(
            update(cls)
                .where(getattr(cls, cls.__pk_field__) == pk)
                .values(**to_update)
                .returning(cls)
        )

    @classmethod
    async def get_by(cls, field: str, value: Any) -> dict | None:
        return await Db.fetch_one(
            select(cls)
                .where(getattr(cls, field) == value)
                .limit(1)
        )
        
    @classmethod
    async def get_all(cls) -> list[dict]:
        return await Db.fetch_all(
            select(cls)
        )
    
    @classmethod
    async def get_all_join(cls, *tables) -> list[dict]:
        aliases = cls._aliases()
        labels = [
            getattr(aliases[t].c, c.key).label(f'{t}__{c.key}')
            for t in tables    
            for c in aliases[t].c
        ]
        q = select(cls, *labels).select_from(cls)

        for t in tables:
            on = cls.__related__[t]['on']
            q = q.join(
                aliases[t],
                getattr(cls, on[0]) == getattr(aliases[t].c, on[1])
            )
        return await Db.fetch_all(q)
    
    @classmethod
    async def exists(cls, field: str, value: Any) -> bool:
        return await Db.fetch_one(
            select(
                exists()
                    .where(getattr(cls, field) == value)
            ),
            query_exists = True
        )
    
    @classmethod
    async def delete(cls, pk: Any):
        await Db.execute(
            delete(cls)
                .where(getattr(cls, cls.__pk_field__) == pk)
        )
