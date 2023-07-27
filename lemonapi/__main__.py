import datetime
import socket

import uvicorn
from decouple import config
from fastapi import Depends, FastAPI, Request
from fastapi.responses import RedirectResponse, Response, FileResponse
from loguru import logger
from starlette.exceptions import HTTPException as StarletteHTTPException

from lemonapi.endpoints import lemons, security, shortener, testing, moderation
from lemonapi.utils.auth import get_current_active_user
from lemonapi.utils.constants import Server

description = """
Nipa-API helps you do awesome stuff. 🚀
"""

favicon_path = "/static/images/favicon.ico"

app = FastAPI(
    title="API",
    description=description,
    version="0.2",
    terms_of_service="http://example.com/terms/",
    contact={
        "name": config("NAME", default="Nipa"),
        "url": config("YOUR_URL", default="http://127.0.0.1:5001"),
        "email": config("EMAIL", default="test-email"),
    },
    license_info={
        "name": "MIT license",
        "url": "https://github.com/Nipa-Code/lemon-API/blob/master/LICENSE",
    },
    docs_url=None,  # set docs to None and use custom template
    redoc_url=None,
)


# add routers to API
app.include_router(security.router, tags=["security"])
app.include_router(moderation.router, tags=["moderation"])
app.include_router(
    lemons.router, tags=["lemons"], dependencies=[Depends(get_current_active_user)]
)
app.include_router(shortener.router, tags=["shortener"])
app.include_router(testing.router, tags=["testing"], include_in_schema=True)


# used for frontend, has no purpose yet here.
origins = [
    "http://127.0.0.1:5001",  # example origin
    "http://localhost:5001",  # example origin
]

"""app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)"""


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    # doing bunch of logging for later, will be used for analytics
    # once I figure out how.
    """logger.debug(f"Request method: {request.method}")
    logger.debug(f"Request url: {request.url}")
    logger.debug(f"Request base: {request.base_url}")
    logger.debug(f"Request client: {request.client}")
    logger.debug(f"Request client host: {request.client.host}")
    logger.debug(f"Request query: {request.query_params}")
    logger.debug(f"Request path param: {request.path_params}")
    logger.debug(f"Request cookies: {request.cookies}")

    logger.debug(f"Request headers: {request.headers}")"""
    # logger.debug(f"Request client host: {request.client.host}")
    """print(moderation.banned)
    print(request.client.host in moderation.banned)
    print(str(request.client.host) in moderation.banned)"""
    # simple IP ban check, if IP is banned then return 403
    if (
        str(request.client.host) in moderation.banned
        and moderation.banned[str(request.client.host)] == True
    ):
        return Response(
            content="You are banned from this server.",
            status_code=403,
        )
    else:
        response = await call_next(request)
        return response


@app.exception_handler(StarletteHTTPException)
async def my_exception_handler(request: Request, exception: StarletteHTTPException):
    """Custom exception handler for 404 error."""
    if exception.status_code == 404:
        name = "error.html"
        return Server.TEMPLATES.TemplateResponse(
            name=name, context={"request": request}, status_code=404
        )

    else:
        return Response(
            content=str(exception.detail), status_code=exception.status_code
        )


@app.on_event("startup")
async def startup() -> None:
    """Startup event for the server."""
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)
    logger.info(f"Local network: http://{local_ip}:5001")

    logger.info(f"Server started at: {datetime.datetime.now()}")


@app.get("/docs/", include_in_schema=False)
async def get_docs(request: Request):
    """Generate documentation for API instead of using the default documentation"""
    name = "docs.html"
    return Server.TEMPLATES.TemplateResponse(name, {"request": request}, 200)


@app.get("/favicon.ico", response_class=FileResponse, include_in_schema=False)
async def get_favicon(request: Request):
    """This is the favicon.ico file that is returned from the server"""
    return favicon_path


@app.get("/", include_in_schema=False)
async def home(request: Request):
    """
    Endpoint to forward requests to documentation instead of home page that has nothing in it.
    :param request:
    :return: RedirectResponse
    """
    return RedirectResponse("/docs/")


if __name__ == "__main__":
    uvicorn.run(
        "lemonapi.__main__:app",
        host="0.0.0.0",
        port=5001,
        log_level="info",
        reload=True,  # True for testing
    )
