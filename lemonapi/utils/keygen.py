import secrets
import string

from sqlalchemy.orm import Session
from asyncpg import Connection

from . import crud


def create_random_key(length: int = 5) -> str:
    chars = string.ascii_uppercase + string.digits
    return "".join(secrets.choice(chars) for _ in range(length))


def create_unique_random_key(db: Session) -> str:
    key = create_random_key()
    while crud.get_db_url_by_key(db, key):
        key = create_random_key()
    return key


# Rewriting the above code to async and use asyncpg


async def create_random_key_async(length: int = 5) -> str:
    chars = string.ascii_uppercase + string.digits
    return "".join(secrets.choice(chars) for _ in range(length))


async def create_unique_random_key_async(conn: Connection) -> str:
    key = await create_random_key()
