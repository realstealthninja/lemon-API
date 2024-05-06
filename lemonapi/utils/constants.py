from pydantic_settings import BaseSettings, SettingsConfigDict

from fastapi import Request

from fastapi.templating import Jinja2Templates


class _Server(BaseSettings):
    """Server class to handle the server constant variables."""

    model_config = SettingsConfigDict(
        validate_default=False,
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )
    # the 4 constants below are used in authentication file (auth.py)
    SECRET_KEY: str = "SECRET_KEY"
    ALGORITHM: str = "HS256"
    ACCESS_EXPIRE_IN: int = 3600  # value in seconds
    REFRESH_EXPIRE_IN: int = ACCESS_EXPIRE_IN * 6

    DEBUG: bool = "DEBUG"

    TEMPLATES: Jinja2Templates = Jinja2Templates(directory="lemonapi/templates")

    SCOPES: list[str] = ["users:read"]
    # key length is used for shortened urls.
    # value of default 5 geneerates shortened urls like:
    # http://localhost:5000/UEFIS
    KEY_LENGTH: int = 5
    SECRET_KEY_LENGTH: int = 10


Server = _Server()


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
