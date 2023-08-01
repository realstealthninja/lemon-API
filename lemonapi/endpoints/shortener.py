from typing import Optional

import validators
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from starlette.datastructures import URL

from lemonapi.utils import crud, models, schemas
from lemonapi.utils.config import get_settings
from lemonapi.utils.database import engine
from lemonapi.utils.constants import get_db

router = APIRouter()

models.Base.metadata.create_all(bind=engine)

templates = Jinja2Templates(directory="lemonapi/templates")


def get_admin_info(db_url: models.URL) -> schemas.URLInfo:
    base_url = URL(get_settings().base_url)
    admin_endpoint = router.url_path_for(
        "administration info", secret_key=db_url.secret_key
    )

    db_url.url = str(base_url.replace(path=db_url.key))
    db_url.admin_url = str(base_url.replace(path=admin_endpoint))
    return db_url


def raise_bad_request(message):
    raise HTTPException(status_code=400, detail=message)


def raise_not_found(request):
    message = f"URL '{request.url}' does not exist"
    raise HTTPException(status_code=404, detail=message)


@router.get("/{url_key}", include_in_schema=False)
def forward_to_target_url(
    url_key: str, request: Request, db: Session = Depends(get_db)
):
    if url_key == "docs":
        return RedirectResponse("/docs/")
    if db_url := crud.get_db_url_by_key(db=db, url_key=url_key):
        crud.update_db_clicks(db=db, db_url=db_url)
        return RedirectResponse(db_url.target_url)
    else:
        raise_not_found(request)


@router.delete("/admin/{secret_key}")
def delete_url(secret_key: str, request: Request, db: Session = Depends(get_db)):
    if db_url := crud.deactivate_db_url_by_secret_key(db, secret_key=secret_key):
        message = f"Successfully deleted shortened URL for '{db_url.target_url}'"
        return {"detail": message}
    else:
        raise_not_found(request)


URLS = []


@router.post("/url/", response_model=schemas.URLInfo)
def create_url(url: schemas.URLBase, db: Session = Depends(get_db)):
    if not validators.url(url.target_url):
        raise HTTPException(status_code=400, detail="Your provided URL is not invalid")
    db_url = crud.create_db_url(db=db, url=url)
    URLS.append(f"{get_settings().base_url}/{db_url.key} redirects to {url.target_url}")
    return get_admin_info(db_url)


@router.get("/api/urls", response_class=HTMLResponse)
def get_urls(request: Request):
    return templates.TemplateResponse("test.html", {"request": request, "urls": URLS})


WOW = []


class FormManager:
    def __init__(self, request: Request):
        self.request: Request = request
        self.url: Optional[str] = None
        self.optional: Optional[str] = None

    async def load(self):
        form = await self.request.form()
        self.url = form.get("url")

    def get_url(self):
        return self.url


@router.post("/create/urls")
async def form_create_url(request: Request, db: Session = Depends(get_db)):
    data = FormManager(request)
    await data.load()
    if not validators.url(data.get_url()):
        return Response(
            status_code=400, content=f"Your provided URL '{data.get_url()}' is invalid"
        )
    url = schemas.URLBase(target_url=data.get_url())
    db_url = crud.create_db_url(db=db, url=url)
    WOW.append(f"{get_settings().base_url}/{db_url.key} redirects to {url.target_url}")
    return templates.TemplateResponse(
        "test.html", {"request": request, "info": get_admin_info(db_url)}
    )


@router.get("/create/urls")
async def test_create_url(request: Request, db: Session = Depends(get_db)):
    return templates.TemplateResponse(
        "foo.html", context={"request": request}
    )  # don't mind the "info: WOW" part, it's just for testing


@router.get(
    "/admin/{secret_key}",
    name="administration info",
    response_model=schemas.URLInfo,
)
def get_url_info(secret_key: str, request: Request, db: Session = Depends(get_db)):
    if db_url := crud.get_db_url_by_secret_key(db, secret_key=secret_key):
        return get_admin_info(db_url)
    else:
        raise_not_found(request)
