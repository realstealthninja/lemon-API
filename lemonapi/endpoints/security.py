from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm

from lemonapi.utils.auth import (
    Token,
    User,
    authenticate_user,
    create_access_token,
    fake_users_db,
    get_current_active_user,
)
from lemonapi.utils.constants import Server

router = APIRouter()


@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Endpoint to authenticate a user and get access token.
    :param form_data: Form data containing login credentials
    """
    user = authenticate_user(fake_users_db, form_data.username, form_data.password)
    print("Log", user)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=Server.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/users/me/", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    return current_user


@router.get("users/add", response_model=User, include_in_schema=True)
async def add_user(request: Request, user: User):
    fake_users_db[user.username] = user
    return {"succeeded": "True"}
