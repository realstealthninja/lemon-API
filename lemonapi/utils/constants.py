from decouple import config

from fastapi import Request
from fastapi.templating import Jinja2Templates

from lemonapi.utils import database


class Server:
    """Server class to handle the server constant variables."""

    # the 3 constants below are used in authentication file (auth.py)
    SECRET_KEY = config("SECRET_KEY", cast=str)
    ALGORITHM = "HS256"
    ACCESS_EXPIRE_IN = 3600  # value in seconds
    REFRESH_EXPIRE_IN = ACCESS_EXPIRE_IN * 6

    DEBUG = config("DEBUG", cast=bool, default=False)

    TEMPLATES = Jinja2Templates(directory="lemonapi/templates")

    SCOPES = ["users:read"]
    # key lenght is used for shortened urls.
    # value of default 5 geneerates shortened urls like:
    # http://localhost:5000/UEFIS
    KEY_LENGTH = 5
    SECRET_KEY_LENGTH = 10


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
