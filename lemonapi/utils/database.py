import asyncpg
from decouple import config

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from .config import get_settings


engine = create_engine(get_settings().postgres_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Connection:
    """Connection configuration for postgress database and redis."""

    DATABASE_URL = f"postgres://{config('DB_USER')}:{config('DB_PASSWORD')}@postgres:{config('DB_PORT')}/{config('DB_NAME')}"
    DB_POOL = asyncpg.create_pool(DATABASE_URL)
