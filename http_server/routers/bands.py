import logging
from fastapi import APIRouter, Depends, Request
from fastapi.responses import PlainTextResponse
from common import tickets
from ..services.authorization import AuthorizeAppRole, AppRoles, User

LOGGER = logging.getLogger(f"playlist.{__name__}")

router = APIRouter(prefix="/band")

@router.get("/ticket")
async def ticket(
    request: Request,
    band: str,
    user_info: User=Depends(AuthorizeAppRole(AppRoles.user))
) -> PlainTextResponse:
    # TODO: determine if user is allowed to have ticket for requested band.
    ticket = await tickets.create(user_info.name, band)
    return PlainTextResponse(ticket)
