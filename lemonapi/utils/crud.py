import secrets
import string

from typing import Annotated
from loguru import logger
from ulid import ULID

from fastapi import status, HTTPException, Depends

from . import schemas, auth, dependencies
from .constants import Server


class CrudService:
    def __init__(self, pool: dependencies.PoolDep):
        self.pool = pool

    async def get_url_by_secret_key(self, secret_key: str):
        async with self.pool.acquire() as con:
            row = await con.fetchrow(
                "SELECT * FROM urls WHERE secret_key = $1 AND is_active = $2",
                secret_key,
                True,
            )
        return row

    async def get_db_url_by_key(self, url_key: str):
        async with self.pool.acquire() as con:
            row = await con.fetchrow(
                "SELECT * FROM urls WHERE url_key = $1 AND is_active = $2",
                url_key,
                True,
            )
        return row

    async def deactivate_db_url_by_secret_key(self, secret_key: str):
        async with self.pool.acquire() as con:
            db_url = await self.get_url_by_secret_key(secret_key)
            if db_url:
                await con.execute(
                    "DELETE FROM urls WHERE secret_key = $1 RETURNING *",
                    secret_key,
                )
            logger.info(
                f"URL with secret key '{secret_key}' deactivated and deleted from the database."
            )
        return db_url

    async def create_db_url(self, url: schemas.URLBase):
        secret_key_length = Server.SECRET_KEY_LENGTH

        async with self.pool.acquire() as con:
            key = await self.create_unique_random_key()
            secret_key = (
                f"{key}_{await self.create_random_key(length=secret_key_length)}"
            )

            await con.execute(
                """INSERT INTO urls (
                    target_url,
                    url_key,
                    secret_key) VALUES ($1, $2, $3)""",
                url.target_url,
                key,
                secret_key,
            )
            row = await con.fetchrow(
                "SELECT url_key, target_url, secret_key FROM urls WHERE url_key = $1",
                key,
            )
            logger.info(f"URL created with key '{key}' in the database.")
        return row

    async def update_db_clicks(self, db_url: schemas.URL):
        async with self.pool.acquire() as con:
            await con.execute(
                "UPDATE urls SET clicks = $1 WHERE url_key = $2",
                db_url.clicks + 1,
                db_url.url_key,
            )
            row = await con.fetchrow(
                "SELECT * FROM urls WHERE url_key = $1", db_url.url_key
            )
            return row

    async def get_list_of_usernames(self) -> list[str]:
        async with self.pool.acquire() as con:
            rows = await con.fetch("SELECT username FROM users")
        return [row["username"] for row in rows]

    async def get_list_of_emails(self) -> list[str]:
        async with self.pool.acquire() as con:
            rows = await con.fetch("SELECT email FROM users")
        return [row["email"] for row in rows]

    async def add_user(self, user: auth.NewUser):
        if user.username in await self.get_list_of_usernames():
            logger.info(f"User with username '{user.username}' already exists.")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Username already exists.",
            )  # raise exception if username already exists

        elif user.email in await self.get_list_of_emails():
            logger.info(f"Email '{user.email}' already exists.")

            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already exists.",
            )

        # create user ID
        ulid = ULID()
        user_id_str = str(ulid)
        async with self.pool.acquire() as con:
            await con.execute(
                """INSERT INTO users (
                    user_id,
                    username,
                    hashed_password,
                    fullname,
                    email
                    ) VALUES ($1, $2, $3, $4, $5)""",
                user_id_str,
                user.username,
                auth.get_password_hash(user.password),
                user.full_name,
                user.email,
            )
            row = await con.fetchrow(
                "SELECT * FROM users WHERE username = $1",
                user.username,
            )
        logger.info(
            f"User '{user.username}' created successfully with ID '{user_id_str}'."
        )
        return row

    async def update_password(self, user: auth.User, new_password: str):
        """Update user password, fetch user from db using User object passed"""
        async with self.pool.acquire() as con:
            row = await auth.get_user(user.username, con)
            hashed_password = await auth.get_password_hash(new_password)
            await con.execute(
                "UPDATE users SET hashed_password = $1 WHERE user_id = $2",
                hashed_password,
                row["user_id"],
            )
            row = await con.fetchrow(
                "SELECT * FROM users WHERE user_id = $1",
                row["user_id"],
            )
            logger.info(
                f"User: '{user.username}' ({user.user_id}) updated password successfully"
            )
        return row, f"Password updated to '{new_password}' successfully."

    async def create_random_key(self, length: int = Server.KEY_LENGTH) -> str:
        """Generate random key from given length to be used in url shortener."""
        chars = string.ascii_uppercase + string.digits
        return "".join(secrets.choice(chars) for _ in range(length))

    async def create_unique_random_key(self) -> str:
        """Create unique random key"""
        key = await self.create_random_key()
        foo = await self.get_db_url_by_key(key)
        while foo:
            key = await self.create_random_key()
            foo = await self.get_db_url_by_key(key)
        return key


CrudServiceDep = Annotated[CrudService, Depends(CrudService)]
