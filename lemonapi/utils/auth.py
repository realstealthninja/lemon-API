from datetime import datetime, timedelta
from typing import Annotated
from loguru import logger

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer, SecurityScopes
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, ValidationError

from sqlalchemy.orm import Session

from lemonapi.utils.constants import Server, get_db
from lemonapi.utils import models

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
# oauth2 security scheme
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="token",
    description="OAuth security scheme",
)


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str
    scopes: list[str] = []


class User(BaseModel):
    username: str
    email: str | None = None
    full_name: str | None = None
    disabled: bool | None = None
    scopes: list[str] = []


class UserInDB(User):
    hashed_password: str


class NewUser(BaseModel):
    username: str
    password: str
    email: str
    full_name: str


def verify_password(plain_password, hashed_password):
    """Verify the password."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    """
    Get the password hash.
    :param password: The password to be hashed.
    """
    return pwd_context.hash(password)


def get_user(username: str, password: str, db: Session = Depends(get_db)):
    """Get user from database."""
    db_user = db.query(models.User).filter(models.User.username == username).first()
    if db_user:
        return UserInDB(**db_user.__dict__)


def authenticate_user(username: str, password: str, db: Session = Depends(get_db)):
    """Authenticates the user."""
    user = get_user(username, password, db)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    """Creates the access token for the API."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, Server.SECRET_KEY, algorithm=Server.ALGORITHM)
    return encoded_jwt


async def get_current_user(
    security_scopes: SecurityScopes,
    request: Request,
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Session = Depends(get_db),
):
    """Get the current user."""
    logger.info(f"User data: {print(i for i in db.query(models.User).all())}")
    logger.info([user.scopes for user in db.query(models.User).all()])
    logger.info(f"More data: {[user for user in db.query(models.User).all()]}")

    authenticate_value = "Bearer"
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": authenticate_value},
    )
    try:
        payload = jwt.decode(token, Server.SECRET_KEY, algorithms=[Server.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
        # DEBUG CODE below for testing
        # user = db.execute(select(models.User).where(
        # models.User.username == token_data.username)
        # )
        # foo = user.first()[0]
        # logger.critical(f"User info: {foo.username}, {foo.scopes}")
        # logger.critical(f"scopes: {request.scope}")
        # logger.info(f"Token data: {token_data}")
        # logger.debug(payload)

    except (JWTError, ValidationError):
        logger.error("JWT Error, invalid token")
        raise credentials_exception
    user = get_user(username=token_data.username, password="", db=db)
    if user is None:
        raise credentials_exception

    return user


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)]
):
    """Get the currently active user."""
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


class RequiredScopes:
    def __init__(self, required_scopes: list[str]) -> None:
        self.required_scopes = required_scopes

    def __call__(self, user: User = Depends(get_current_user)) -> bool:
        for permission in self.required_scopes:
            if permission not in user.scopes:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Not enough permissions",
                    headers={"WWW-Authenticate": "Scopes"},
                )
        return True
