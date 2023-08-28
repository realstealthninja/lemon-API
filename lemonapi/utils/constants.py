import asyncpg
from decouple import config
from fastapi import Request
from fastapi.templating import Jinja2Templates

from lemonapi.utils.database import SessionLocal


class Server:
    """Server class to handle the server constant variables."""

    # the 3 constants below are used in authentication file (auth.py)
    SECRET_KEY = config("SECRET_KEY")
    ALGORITHM = "HS256"
    ACCESS_EXPIRE_IN = 3600
    REFRESH_EXPIRE_IN = ACCESS_EXPIRE_IN * 6

    TEMPLATES = Jinja2Templates(directory="lemonapi/templates")
    db_url = config(
        "DATABSE_URL",
        default="postgres://postgres:secretdefaultpassword@127.0.0.1:8000/lemon",
    )
    DB_POOL = asyncpg.create_pool(db_url)

    SCOPES = ["users:read"]


class FormsManager:
    """Handling forms data from request."""

    def __init__(self, request: Request, **kwargs):
        self.__dict__.update(kwargs)
        self.request = request

    def get_data(self):
        """Returns the data of the form as a dictionary."""
        return self.__dict__

    def find_data(self, key: str):
        """Returns the value of given key from the forms data."""
        return self.__dict__[key] if key in self.__dict__ else None

    def get_keys(self):
        """Returns the keys of the forms data. Keys are basically the kwargs."""
        return self.__dict__.keys()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class Analysis:
    """Handling analysis data from request."""

    def __init__(self, request: Request):
        self.request = request
        self.data: dict[str, str] = {}

    def get_request_origin(self):
        """Returns the origin of the request."""
        return self.request.client.host

    def get_request_user_agent(self):
        """Returns the user agent of the request."""
        return self.request.headers["user-agent"]

    def unique_visitors(self):
        """Get the amount of unique visitors to the web server."""
        raise NotImplementedError
