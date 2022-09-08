import datetime

import uvicorn
from decouple import config
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from lemonapi.endpoints import chat, lemons, security, shortener, testing
from lemonapi.utils.constants import Server

description = """
Nipa-API helps you do awesome stuff. 🚀
"""

app = FastAPI(
    title="Nipa API",
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

# used for frontend, has no purpose yet here.
origins = [
    "http://127.0.0.1:5001",  # example origin
    "http://localhost:5001",  # example origin
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/docs")
async def get_docs(request: Request):
    """Generate documentation for API instead of the default one"""
    name = "docs.html"
    return Server.TEMPLATES.TemplateResponse(name, {"request": request}, 200)


# add routers to API
app.include_router(testing.router, tags=["testing"], include_in_schema=False)
app.include_router(security.router, tags=["security"])
app.include_router(lemons.router, tags=["lemons"])
app.include_router(shortener.router, tags=["shortener"])
app.include_router(chat.router, tags=["chat"], include_in_schema=False)


@app.exception_handler(StarletteHTTPException)
async def my_exception_handler(request: Request, exception: StarletteHTTPException):
    """Custom exception handler for 404 error."""
    if exception.status_code == 404:
        name = "error.html"
        return Server.TEMPLATES.TemplateResponse(
            name=name, context={"request": request}, status_code=404
        )


@app.on_event("startup")
async def startup() -> None:
    """
    Startup event for the server.
    """
    print("Server started at:", datetime.datetime.now())
    # create connection to postgres DB server and create required tables if they don't exist


@app.get("/")
async def home(request: Request):
    """
    Endpoint to forward requests to documentation instead of home page that has nothing in it
    :param request:
    :return: RedirectResponse
    """
    return RedirectResponse("/docs")


if __name__ == "__main__":
    uvicorn.run(
        "lemonapi.__main__:app",
        host="0.0.0.0",
        port=5001,
        log_level="info",
        reload=True,
    )
