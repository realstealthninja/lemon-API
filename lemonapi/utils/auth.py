import secrets

from typing import Annotated
from loguru import logger
from passlib.context import CryptContext
from pydantic import BaseModel, ValidationError
from asyncpg import Record
from datetime import datetime, timedelta
from jose import JWTError, jwt

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer

from lemonapi.utils.constants import Server
from lemonapi.utils import dependencies

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
    user_id: str
    email: str | None = None
    full_name: str | None = None
    is_disabled: bool | None = None
    scopes: list[str] = []


class UserInDB(User):
    hashed_password: str


class NewUser(BaseModel):
    username: str
    password: str
    email: str
    full_name: str


class RefreshToken(BaseModel):
    refresh_token: str


class AccessToken(RefreshToken):
    """Used as a response for requesting a new access token."""

    access_token: str
    token_type: str
    expires_in: int
    refresh_token: str


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Function to verify the password.

    Parameters
    ----------
    plain_password : str
        Password in plain text.
    hashed_password : str
        The hashed password

    Returns
    -------
    bool
        True if the password matches, False otherwise.
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Function to hash the password from given string.

    Parameters
    ----------
    password : str
        The password to be hashed.

    Returns
    -------
    str
        The hashed password.
    """
    return pwd_context.hash(password)


async def get_user(username: str, pool: dependencies.PoolDep) -> UserInDB | None:
    """
    Parameters
    ----------
    username : str
        Username of the user.
    db : Annotated[Connection, Depends]
        Database connection from session.

    Returns
    -------
    UserInDB | None
        Return None if user is not found.
    """
    async with pool.acquire() as con:
        row = await con.fetchrow("SELECT * FROM users WHERE username = $1", username)

    if row:
        return UserInDB(**dict(row))
    return None


async def authenticate_user(
    username: str,
    password: str,
    request: Request | None,
    pool: dependencies.PoolDep,
):
    """
    Authenticate the user with username and password.

    Parameters
    ----------
    username : str
        Username of the user.
    password : str
        Password of the user.
    db : Annotated[Connection, Depends
        Database connection from session.

    Returns
    -------
    _type_ missing
        _description_ not sure, missing value
    """
    user = await get_user(username, pool)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        if request:
            logger.warning(f"Password incorrect: {request.headers['host']}")
        else:
            logger.warning("Incorrect password request, host unavailable")
        return False

    return user


async def reset_refresh_token(
    pool: dependencies.PoolDep, user_id: str
) -> tuple[str, Record]:
    """
    Reset the refresh token for the user or receive it.

    Parameters
    ----------
    db : Annotated[Connection, Depends]
        Database connection from session.
    user_id : str
        The id of the user.

    Returns
    -------
    tuple[str, Record]
        Tuple containing the refresh token and the row from the database.
    """
    # Generate 22 char long string
    token_salt = secrets.token_urlsafe(16)

    expiration = datetime.utcnow() + timedelta(seconds=Server.REFRESH_EXPIRE_IN)
    async with pool.acquire() as con:
        row = await con.fetchrow(
            "UPDATE users SET key_salt = $1 WHERE user_id = $2 RETURNING *",
            token_salt,
            user_id,
        )
    token = jwt.encode(
        {
            "id": row["user_id"],
            "grant_type": "refresh_token",
            "expiration": expiration.timestamp(),
            "salt": token_salt,
            "scopes": row["scopes"],
        },
        Server.SECRET_KEY,
        algorithm=Server.ALGORITHM,
    )
    return token, row


async def create_access_token(
    pool: dependencies.PoolDep, refresh_token: str
) -> tuple[str, str]:
    """
    Create access token to be used for authentication.
    Refresh existing refresh token if it is expired.

    Parameters
    ----------
    db : Annotated[Connection, Depends]
        database connection from session.
    refresh_token : str
        refresh token used to create access token.

    Returns
    -------
    tuple[str, str]
        Tuple containing the access token and refresh token.

    Raises
    ------
    HTTPException
        When the refresh token is invalid.
    """
    try:
        token_data = jwt.decode(refresh_token, Server.SECRET_KEY)
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    expire = datetime.utcnow() + timedelta(seconds=Server.ACCESS_EXPIRE_IN)
    async with pool.acquire() as con:
        row = await con.fetchrow(
            "SELECT user_id, key_salt, scopes FROM users WHERE user_id = $1",
            token_data["id"],
        )
        # validate salt
        if row["key_salt"] != token_data["salt"]:
            logger.warning("Invalid salt detected")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if int(token_data["expiration"]) < datetime.utcnow().timestamp():
            refresh_token, row = await reset_refresh_token(con, row["user_id"])

    token = jwt.encode(
        {
            "id": token_data["id"],
            "grant_type": "access_token",
            "expiration": expire.timestamp(),
            "salt": row["key_salt"],
            "scopes": row["scopes"],
        },
        Server.SECRET_KEY,
        algorithm=Server.ALGORITHM,
    )
    return token, refresh_token


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    pool: dependencies.PoolDep,
):
    """
    Get the current user.

    Parameters
    ----------
    token : Annotated[str, Depends]
        Authorization token.
    db : Annotated[Connection, Depends]
        Database connection from session.

    Returns
    -------
    UserInDB
        user object with necessary data.

    Raises
    ------
    credentials_exception
        When any of data is not valid.
    """
    authenticate_value = "Bearer"
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": authenticate_value},
    )
    async with pool.acquire() as con:
        try:
            payload = jwt.decode(
                token, Server.SECRET_KEY, algorithms=[Server.ALGORITHM]
            )
            u_id: str = payload.get("id")
            if u_id is None:
                raise credentials_exception
            username = await con.fetchrow(
                "SELECT username FROM users WHERE user_id = $1", u_id
            )
            token_data = TokenData(username=str(username[0]))
        except (JWTError, ValidationError):
            logger.trace("JWT Error, invalid token")
            raise credentials_exception
        user = await get_user(username=token_data.username, db=con)
    if user is None:
        logger.trace("User not found but ID was in token")
        raise credentials_exception
    return user


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)]
) -> User:
    """
    Get the current active user. This user is authenticated.

    Parameters
    ----------
    current_user : Annotated[User, Depends]
        Current user that is received from get_current_user.

    Returns
    -------
    User
        user object with necessary data.

    Raises
    ------
    HTTPException
        When the user is disabled.
    """
    if current_user.is_disabled:
        logger.trace(f"Inactive user requested: {current_user} ")
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user
