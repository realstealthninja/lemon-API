from datetime import timedelta
from uuid import uuid4

from sqlalchemy.orm import Session

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm

from lemonapi.utils.auth import (
    NewUser,
    Token,
    User,
    authenticate_user,
    create_access_token,
    get_current_active_user,
)
from lemonapi.utils import crud
from lemonapi.utils.decorators import limiter
from lemonapi.utils.constants import FormsManager, Server, get_db

router = APIRouter()


@router.post("/token", response_model=Token)
@limiter(max_calls=1, ttl=60)
async def login_for_access_token(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
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
    access_token_expires = timedelta(minutes=Server.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/users/me/", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    return current_user


@router.post("/users/add/")
async def add_user(
    request: Request, user: NewUser = Depends(), db: Session = Depends(get_db)
):
    """Register a new user, add user to dictionary with username and hashed password"""
    db_user = crud.add_user(db, user)
    return db_user


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
