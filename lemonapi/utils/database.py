import asyncpg
from decouple import config


# engine = create_engine(get_settings().postgres_url)
# SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
# Base = declarative_base()


class Connection:
    """Connection configuration for postgress database and redis."""

    DATABASE_URL = f"postgres://{config('DB_USER')}:{config('DB_PASSWORD')}@postgres:{config('DB_PORT')}/{config('DB_NAME')}"
    DB_POOL = asyncpg.create_pool(DATABASE_URL, min_size=2, max_size=8)
