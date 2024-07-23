from typing     import Any

from sqlalchemy import (
    insert,
    update,
    select,
    exists,
    delete
)

from .db import Db


class Model:
    __pk_field__  = 'id'

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
