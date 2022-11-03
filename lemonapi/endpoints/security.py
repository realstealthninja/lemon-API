from datetime import timedelta
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm

from lemonapi.utils.auth import (
    NewUser,
    Token,
    User,
    authenticate_user,
    create_access_token,
    fake_users_db,
    get_current_active_user,
    get_password_hash,
)
from lemonapi.utils.constants import FormsManager, Server

router = APIRouter()


@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Endpoint to authenticate a user and get access token.
    :param form_data: Form data containing login credentials
    """
    user = authenticate_user(fake_users_db, form_data.username, form_data.password)
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


@router.post("/users/add/")
async def add_user(request: Request, user: NewUser = Depends()):
    """Register a new user, add user to dictionary with username and hashed password"""
    data = user
    fake_users_db[data.username] = {
        "username": data.username,
        "full_name": data.full_name,
        "email": data.email,
        "hashed_password": get_password_hash(data.password),
        "disabled": False,
        "ip": list(request.client.host),
        "ID": str(uuid4),
        "urls": [],
    }
    return data


@router.get("/users/test/login/")
async def test_login(request: Request):
    return Server.TEMPLATES.TemplateResponse("login.html", {"request": request})


@router.post("/users/test/login/")
async def test_login(request: Request):
    foo = await request.form()
    bar = FormsManager(
        request, a=foo
    )  # in order to access the data from dictionary, it will be stored in key 'a'
    return {
        "message": f"You are logged in with folowing credentials: {bar.get_data()['a']}"
    }
