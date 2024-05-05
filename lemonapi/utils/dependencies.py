from . import database
import asyncpg

from typing import Annotated

from fastapi import Depends


async def get_pool():
    return database.Connection.DB_POOL


PoolDep = Annotated[asyncpg.Pool, Depends(get_pool)]


async def protected():
    """Protected route. Require checks to pass."""
    raise NotImplementedError
