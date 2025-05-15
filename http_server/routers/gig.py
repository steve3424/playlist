import logging
import base64
from fastapi import APIRouter, Depends
from ..middlewares.auth import Authenticate
from ..services import redis_service
from common.encryption import CIPHER
from common.tickets import Ticket

LOGGER = logging.getLogger(f"playlist.{__name__}")
TICKET_TTL = 5 # seconds

router = APIRouter(prefix="/gig")

@router.get("/ticket")
async def ticket(
    band: str,
    user_info: dict=Depends(Authenticate(permission_level=1))
):
    global TICKET_TTL
    # TODO: determine if user is allowed to join gig w/ requested
    #       band.
    ticket = Ticket(
        user_id=user_info["id"],
        band=band
    ).model_dump_json().encode("utf-8")

    await redis_service.client.set(f"{band}:{user_info['id']}", ticket)
    await redis_service.client.expire(f"{band}:{user_info['id']}", TICKET_TTL)

    return base64.b16encode(
        CIPHER.encrypt(
            ticket
        )
    ).decode(encoding="utf8")
