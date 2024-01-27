import validators

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from asyncpg import Connection
from typing import Annotated
from loguru import logger

from lemonapi.utils import crud, schemas
from lemonapi.utils.constants import Server
from lemonapi.utils.constants import get_db

router = APIRouter()


templates = Jinja2Templates(directory="lemonapi/templates")


def raise_bad_request(message):
    raise HTTPException(status_code=400, detail=message)


def raise_not_found(request):
    message = f"URL '{request.url}' does not exist"
    raise HTTPException(status_code=404, detail=message)


@router.get("/{url_key}", include_in_schema=False)
async def forward_to_target_url(
    request: Request, url_key: str, db: Annotated[Connection, Depends(get_db)]
):
    if url_key == "docs":
        return RedirectResponse("/docs/")
    row = await crud.get_db_url_by_key(conn=db, url_key=url_key)

    try:
        url_object = schemas.URL(**dict(row))
    except Exception as e:
        logger.trace(e)
    if row:
        row = await crud.update_db_clicks(conn=db, db_url=url_object)

        return RedirectResponse(row["target_url"])
    else:
        raise_not_found(request)


@router.delete("/admin/{secret_key}")
async def delete_url(
    request: Request, secret_key: str, db: Annotated[Connection, Depends(get_db)]
):
    """Deletes url by it's secret key"""
    if row := await crud.deactivate_db_url_by_secret_key(db, secret_key=secret_key):
        message = f"""
        Deleted URL for '{row['url_key']} -> {row['target_url']}'
        """
        # if message above fails, it is due to row being None as it's inactive and not
        # selected by database query resulting to server raising Internal Server Error
        return {"detail": message}
    else:
        raise_not_found(request)


@router.post("/url/")
async def create_url(url: schemas.URLBase, db: Annotated[Connection, Depends(get_db)]):
    if not validators.url(url.target_url):
        raise HTTPException(status_code=400, detail="Your provided URL is not invalid")
    db_url = await crud.create_db_url(conn=db, url=url)

    return db_url


@router.get("/url/inspect")
async def inspect_url(
    db: Annotated[Connection, Depends(get_db)], url: schemas.URLBase = Depends()
):
    """url is the shortened url.
    for example: 'http://localhost:5000/UEWIS'
    """
    if not validators.url(url.target_url):
        raise HTTPException(status_code=400, detail="Your provided URL is not invalid")

    url_key = url.target_url.split("/")[-1]
    # url key lenght does not match the defined lenght, raise HTTPException
    if len(url_key) != Server.KEY_LENGTH:
        raise HTTPException(status_code=400, detail="Your provided URL is not invalid")

    url_info = crud.get_db_url_by_key(conn=db, url_key=url_key)

    target = url_info["target_url"]  # target where 'url.target_url' redirects
    created_at = url_info["created_at"]

    message = (
        f"URL '{url.target_url}' redirects to '{target}'. Created at: {created_at}"
    )

    return {"detail": message}
