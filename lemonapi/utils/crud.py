from fastapi import status, HTTPException
from lemonapi.utils.constants import Server

from sqlalchemy.orm import Session

from . import keygen, schemas, auth

from asyncpg import Connection


"""def get_db_url_by_secret_key(db: Session, secret_key: str) -> models.URL:
    return (
        db.query(models.URL)
        .filter(models.URL.secret_key == secret_key, models.URL.is_active)
        .first()
    )"""


async def get_url_by_secret_key_async(conn: Connection, secret_key: str):
    row = await conn.fetchrow(
        "SELECT * FROM urls WHERE secret_key = $1 AND is_active = $2", secret_key, True
    )
    return row


"""def get_db_url_by_key(db: Session, url_key: str) -> models.URL:
    return (
        db.query(models.URL)
        .filter(models.URL.key == url_key, models.URL.is_active)
        .first()
    )"""


async def get_db_url_by_key_async(conn: Connection, url_key: str):
    row = await conn.fetchrow(
        "SELECT * FROM urls WHERE key = $1 AND is_active = $2", url_key, True
    )
    return row

"""
def deactivate_db_url_by_secret_key(db: Session, secret_key: str) -> models.URL:
    db_url = get_db_url_by_secret_key(db, secret_key)
    if db_url:
        db_url.is_active = False
        db.commit()
        db.refresh(db_url)
    return db_url
"""

async def deactivate_db_url_by_secret_key_async(conn: Connection, secret_key: str):
    db_url = await get_url_by_secret_key_async(conn, secret_key)
    if db_url:
        async with conn.transaction():
            await conn.execute(
                "   UPDATE urls SET is_active = $1 WHERE secret_key = $2",
                False,
                secret_key,
            )
    return db_url

"""
def create_db_url(db: Session, url: schemas.URLBase) -> models.URL:
    key = keygen.create_unique_random_key(db)
    secret_key = f"{key}_{keygen.create_random_key(length=8)}"
    db_url = models.URL(target_url=url.target_url, key=key, secret_key=secret_key)
    db.add(db_url)
    db.commit()
    db.refresh(db_url)
    return db_url
"""

async def create_db_url_async(conn: Connection, url: schemas.URLBase):
    key = await keygen.create_unique_random_key_async(conn)
    secret_key = f"{key}_{await keygen.create_random_key_async(length=8)}"
    async with conn.transaction():
        await conn.execute(
            "INSERT INTO urls (target_url, key, secret_key) VALUES ($1, $2, $3)",
            url.target_url,
            key,
            secret_key,
        )
        row = conn.fetchrow("SELECT secret_key FROM urls WHERE key = $1", key)
    return row

"""
def update_db_clicks(db: Session, db_url: schemas.URL) -> models.URL:
    db_url.clicks += 1
    db.commit()
    db.refresh(db_url)
    return db_url
"""

async def update_db_clicks_async(conn: Connection, db_url: schemas.URL):
    async with conn.transaction():
        await conn.execute(
            "UPDATE urls SET clicks = $1 WHERE key = $2", db_url.clicks + 1, db_url.key
        )
        row = await conn.fetchrow("SELECT * FROM urls WHERE key = $1", db_url.key)
    return row

"""
def get_list_of_usernames(db: Session) -> list[str]:
    return [user.username for user in db.query(models.User).all()]
"""

async def get_list_of_usernames_async(conn: Connection) -> list[str]:
    rows = await conn.fetch("SELECT username FROM users")
    return [row["username"] for row in rows]

"""
def get_list_of_emails(db: Session) -> list[str]:
    return [user.email for user in db.query(models.User).all()]
"""

async def get_list_of_emails_async(conn: Connection) -> list[str]:
    rows = await conn.fetch("SELECT email FROM users")
    return [row["email"] for row in rows]

"""
def add_user(db: Session, user: auth.NewUser) -> models.User:
    if user.username in get_list_of_usernames(db):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already exists.",
        )  # raise exception if username already exists
    elif user.email in get_list_of_emails(db):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already exists.",
        )
    db_user = models.User(
        username=user.username,
        hashed_password=auth.get_password_hash(user.password),
        fullname=user.full_name,
        email=user.email,
        scopes=[Server.SCOPES[0]],
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user"""


async def add_user_async(conn: Connection, user: auth.NewUser):
    if user.username in await get_list_of_usernames_async(conn):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already exists.",
        )  # raise exception if username already exists
    elif user.email in await get_list_of_emails_async(conn):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already exists.",
        )
    async with conn.transaction():
        await conn.execute(
            """INSERT INTO users (
                username, 
                hashed_password, 
                fullname, email, 
                scopes,
                ) VALUES ($1, $2, $3, $4, $5)""",
            user.username,
            auth.get_password_hash(user.password),
            user.full_name,
            user.email,
            [Server.SCOPES[0]],
        )
        row = await conn.fetchrow(
            "SELECT * FROM users WHERE username = $1", user.username
        )
    return row
