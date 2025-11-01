import logging
from fastapi import APIRouter, Depends, Request
from fastapi.responses import PlainTextResponse
from common import tickets
from ..authorization.models import AppRoles, User
from ..authorization.endpoint import AuthorizeEndpoint

LOGGER = logging.getLogger(f"playlist.{__name__}")

router = APIRouter(prefix="/bands", tags=["bands"])

# @router.get("/ticket")
# async def ticket(
#     request: Request,
#     band: str,
#     user_info: User=Depends(AuthorizeEndpoint(AppRoles.user))
# ) -> PlainTextResponse:
#     # TODO: determine if user is allowed to have ticket for requested band.
#     ticket = await tickets.create(user_info.name, band)
#     return PlainTextResponse(ticket)
