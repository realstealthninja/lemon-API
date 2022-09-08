import asyncpg
from decouple import config
from fastapi.templating import Jinja2Templates


class Server:
    """
    Server class to handle the server constant variables
    """

    # the 3 constants below are used in authentication file (auth.py)
    SECRET_KEY = config("SECRET_KEY")
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 30

    TEMPLATES = Jinja2Templates(directory="lemonapi/templates")
    db_url = config(
        "DATABSE_URL",
        default="postgres://postgres:secretdefaultpassword@127.0.0.1:8000/lemon",
    )
    DB_POOL = asyncpg.create_pool(db_url)
