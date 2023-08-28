from datetime import timedelta
from typing import Annotated
from sqlalchemy.orm import Session

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi import Cookie
from fastapi.security import OAuth2PasswordRequestForm
from starlette.responses import RedirectResponse
from lemonapi.utils.auth import (
    NewUser,
    Token,
    User,
    authenticate_user,
    create_access_token,
    get_current_active_user,
    RequiredScopes,
)
from lemonapi.utils import crud
from lemonapi.utils.constants import FormsManager, Server, get_db

router = APIRouter()


@router.post("/token", response_model=Token)
# @limiter(max_calls=1, ttl=60)
async def login_for_access_token(
    request: Request,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Session = Depends(get_db),
):
    """
    Endpoint to authenticate a user and get access token.
    :param form_data: Form data containing login credentials
    """
    user = authenticate_user(form_data.username, form_data.password, db=db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=Server.ACCESS_EXPIRE_IN)
    access_token = create_access_token(
        data={"sub": user.username, "scopes": Server.SCOPES[0]},
        expires_delta=access_token_expires,
    )
    redirect = RedirectResponse(url="/showtoken")
    redirect.set_cookie(
        key="token",
        value=access_token,
        httponly=True,
        max_age=Server.ACCESS_EXPIRE_IN * 60,
        path="/showtoken",
    )
    # return {"access_token": access_token, "token_type": "bearer"}
    return redirect


@router.get("/showtoken", include_in_schema=False)
async def show_token(request: Request, token: Annotated[str | None, Cookie()] = None):
    info = {"request": request, "token": token}
    return info


@router.get("/users/me/", response_model=User)
async def read_users_me(
    current_user: Annotated[User, Depends(get_current_active_user)],
    authorize: Annotated[
        RequiredScopes, Depends(RequiredScopes(required_scopes=["users:read"]))
    ],
):
    return current_user


@router.post("/users/add/")
async def add_user(
    request: Request, user: NewUser = Depends(), db: Session = Depends(get_db)
):
    """Register a new user, add user to database with username and hashed password."""
    db_user = crud.add_user(db, user)
    return db_user


@router.get("/users/test/login/", include_in_schema=False)
async def test_login(request: Request):
    return Server.TEMPLATES.TemplateResponse("login.html", {"request": request})


@router.post("/users/test/login/", include_in_schema=False)
async def post_test_login(request: Request):
    foo = await request.form()
    bar = FormsManager(
        request, a=foo
    )  # in order to access the data from dictionary, it will be stored in key 'a'
    # please note, this is a testing endpoint and is not meant to be used in production.
    return {"message": f"You are logged in with credentials: {bar.get_data()['a']}"}


@router.get("/users/me/items/")
async def read_own_items(
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """This is a testing endpoint that can be used to test the scopes of the user."""
    return [{"item_id": "Foo", "owner": current_user.username}]


# In this section I will attempt to re-implement security
# Build refresh token and access token.
# Access token will be used to access the API.
# Refresh token will be used to get a new access token.


# Endpoint to create a refrsh token
@router.get("/refresh_token")
async def refresh_token(request: Request):
    ...


@router.get("/callback")
async def auth_callback(request: Request):
    ...


from lemonapi.utils.auth import RefreshToken, AccessToken
from lemonapi.utils import auth


@router.post("/authenticate", response_model=AccessToken)
async def authenticate(request: Request, body: RefreshToken) -> dict:
    """
    Authenticate and request an access token.

    Users should replace their local refresh token with the one returned.
    """
    access, refresh = await auth.generate_access_token(
        request.state.db_conn, body.refresh_token
    )
    return {
        "access_token": access,
        "token_type": "Bearer",
        "expires_in": Server.ACCESS_EXPIRE_IN,  # value in seconds
        # Refresh token for user to refresh access token
        "refresh_token": refresh,
    }
