from fastapi import APIRouter, Request

from lemonapi.utils.constants import Server

router = APIRouter()


@router.get("/admin/dashboard/")
async def dashboard(request: Request):
    name = "admin.html"
    return Server.TEMPLATES.TemplateResponse(
        name=name, context={"request": request}, status_code=200
    )
