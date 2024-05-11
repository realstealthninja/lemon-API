from typing import Annotated
from loguru import logger

from fastapi import APIRouter, Depends, HTTPException, Request, status, Cookie
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm

from lemonapi.utils import auth
from lemonapi.utils import dependencies

from lemonapi.utils.constants import Server
from lemonapi.utils.crud import CrudServiceDep


from lemonapi.utils.auth import (
    User,
    get_current_active_user,
    RefreshToken,
    AccessToken,
)

router = APIRouter()


@router.get("/showtoken")
async def show_token(request: Request, token: Annotated[str | None, Cookie()] = None):
    context = {"request": request}
    if token:
        context["token"] = token
        template_name = "api_token.html"
        return Server.TEMPLATES.TemplateResponse(template_name, context)

    else:
        return {"detail": "No token found"}


@router.post("/token")
async def login_for_refresh_token(
    request: Request,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    pool: dependencies.PoolDep,
):
    """
    Endpoint to receive a refresh token. This token does not grant user
    permissions.

    Requires username and password.

    Returns
    -------
        refresh token and token type.

    Raises
    ------
    HTTPException
        When incorrect username or password is provided.
    """
    async with pool.acquire() as con:
        user = await auth.authenticate_user(
            form_data.username, form_data.password, request=request, pool=con
        )
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        user_id = await con.fetchrow(
            "SELECT user_id FROM users WHERE username = $1", user.username
        )
        refresh_token, _ = await auth.reset_refresh_token(
            con=con,
            user_id=user_id[0],
        )
    log_user = user_id["user_id"]
    ip = request.client.host
    logger.info(f"Successful login from: user_id={log_user} | client_ip={ip}")
    redirect = RedirectResponse(url="/showtoken", status_code=303)
    redirect.set_cookie(
        key="token",
        value=refresh_token,
        httponly=True,
        max_age=10,
        path="/showtoken",
    )
    headers = request.headers

    # If the request comes from docs, we want to give the access token upon
    # request so that we can test the API endpoint in the docs. If the
    # access_token would not be provided like this you would be unable to
    # test protected endpoints in the docs.
    if "referer" in headers and "/docs" in request.headers["referer"]:
        token = await authenticate(
            request, RefreshToken(refresh_token=refresh_token), pool=pool
        )
        return {
            "access_token": token["access_token"],
            "token_type": token["token_type"],
        }
    elif "referer" in headers and "/login" in request.headers["referer"]:
        return redirect
    else:
        return {"refresh": refresh_token, "token_type": "bearer"}


@router.post("/authenticate", response_model=AccessToken)
async def authenticate(
    request: Request,
    body: RefreshToken,
    pool: dependencies.PoolDep,
) -> dict:
    """
    Authenticate and get an access token.

    Users should replace their local refresh token with the one returned.

    Returns
    -------
    dict
        containing access token, token type, refresh token, and expiration time.
        Response model is AccessToken.
    """
    async with pool.acquire() as con:
        access, refresh = await auth.create_access_token(
            con=con,
            refresh_token=body.refresh_token,
            request=request,
        )
    return {
        "access_token": access,
        "token_type": "Bearer",
        "expires_in": Server.ACCESS_EXPIRE_IN,  # value in seconds
        "refresh_token": refresh,
    }


@router.post("/users/add/")
async def add_user(
    request: Request, crud_service: CrudServiceDep, user: auth.NewUser = Depends()
):
    """Register a new user, add user to database with username and hashed password."""
    added_user = await crud_service.add_user(user)

    return added_user


@router.patch("/users/update/password")
async def update_password(
    request: Request,
    user: Annotated[User, Depends(get_current_active_user)],
    new_password: str,
    crud_service: CrudServiceDep,
):
    """Update user password."""
    row, message = await crud_service.update_password(user, new_password)
    return {"detail": row, "dt": message}


@router.get("/users/me", response_model=User)
async def read_users_me(
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    return current_user


@router.get("/login", include_in_schema=False)
async def login(request: Request):
    context = {"request": request}
    template_name = "login.html"
    return Server.TEMPLATES.TemplateResponse(template_name, context)
