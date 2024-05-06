import datetime
import socket
import logging
import pathlib
import typing

from loguru import logger
from aioprometheus import MetricsMiddleware, REGISTRY, Counter, render
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Depends, Header
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse, Response, FileResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from lemonapi.endpoints import security, shortener, lemons  # moderation
from lemonapi.utils.constants import Server
from lemonapi.utils.auth import get_current_active_user
from lemonapi.utils.database import Connection

# from lemonapi.utils import promthutils

description = """Random API"""

favicon_path = pathlib.Path("./static/images/favicon.ico")


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)

        logger.info(f"Local network: http://{local_ip}:5001")
    except Exception:
        logger.error("Failure to get local network IP address.")
        logger.trace(
            "Startup failed to receive network IP address, proceeding anyways."
        )

    logger.info(f"Server started at: {datetime.datetime.now()}")

    # possible error that might happen: socket.gaierror, if it keeps persisting,
    # try adding try-except block to catch it and re-do the `await Connection.DB_POOL`
    # within the block

    # Create database connection pool
    await Connection.DB_POOL

    yield
    # closing down, anything after yield will be ran as shutdown event.
    await Connection.DB_POOL.close()
    logger.info(f"Server shutting down at: {datetime.datetime.now()}")


app = FastAPI(
    title="API",
    description=description,
    version="0.2",
    terms_of_service="http://example.com/terms/",
    license_info={
        "name": "MIT license",
        "url": "https://github.com/Nipa-Code/lemon-API/blob/main/LICENSE",
    },
    docs_url="/altdocs",  # set docs to None and use custom template
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.mount(
    "/static",
    StaticFiles(directory="lemonapi/static"),
    name="static",
)


# By default this value is set to False and is configured without need of user.
# This is only used for testing purposes during development.
if Server.DEBUG:
    from lemonapi.endpoints import testing

    app.include_router(testing.router, tags=["testing"])

app.include_router(security.router, tags=["security"])
app.include_router(
    lemons.router, tags=["lemons"], dependencies=[Depends(get_current_active_user)]
)
app.include_router(shortener.router, tags=["shortener"])


# Add prometheus middleware
app.add_middleware(MetricsMiddleware)

# Define metrics
app.state.event_counter = Counter("events", "Number of events.", registry=REGISTRY)
app.state.user_created = Counter(
    "users_created", "Number of users created.", registry=REGISTRY
)

# Example query for prometheus to get number of users created in the past week.
# Counter value as is might not be useful for statistics, but using something like
# increase gives it a meaningful value.
# Example query: increase(users_created[1w])

# Other useful stuff to keep in mind:
# increase(users_created[24h]) returns the number of users created in the last 24 hours
# rate(users_created[1h]) returns the average per-second users created rate for last 1h


class EndpointFilter(logging.Filter):
    # Uvicorn endpoint access log filter
    def filter(self, record: logging.LogRecord) -> bool:
        return record.getMessage().find("GET /metrics") == -1


# Filter out /endpoint
logging.getLogger("uvicorn.access").addFilter(EndpointFilter())


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


@app.get("/docs/", include_in_schema=False)
async def get_docs(request: Request):
    """Generate documentation for API instead of using the default documentation."""
    name = "docs.html"
    return Server.TEMPLATES.TemplateResponse(name, {"request": request}, 200)


@app.get("/favicon.ico", response_class=FileResponse, include_in_schema=False)
async def get_favicon(request: Request):
    """This is the favicon.ico file that is returned from the server."""
    return FileResponse(favicon_path)


@app.get("/", include_in_schema=False)
async def home():
    """
    Endpoint to forward requests to documentation instead of empty home page.
    :param request:
    :return: RedirectResponse
    """
    return RedirectResponse("/docs/")


@app.get("/status/")
async def server_status(request: Request) -> Response:
    request.app.state.event_counter.inc(
        {"path": request.scope["path"], "method": request.scope["method"]}
    )
    return Response(content="Server is running.", status_code=200)


@app.get("/metrics/")
async def handle_metrics(
    request: Request,
    accept: typing.List[str] = Header(None),
) -> Response:
    content, http_headers = render(REGISTRY, accept)
    logger.trace(f"Metrics requested from IP: {request.client.host}")
    return Response(content=content, media_type=http_headers["Content-Type"])
