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

@router.get("/gig")
async def gig(
    band: str,
    user_info: dict=Depends(Authenticate(permission_level=1))
):
    global TICKET_TTL

    # TODO: determine if user is allowed to join gig w/ requested band.
    ticket = Ticket(
        user_id=user_info["id"],
        band=band
    )
    ticket_key = str(ticket)
    ticket_enc = base64.b16encode(
        CIPHER.encrypt(
            ticket.model_dump_json().encode("utf-8")
        )
    ).decode(encoding="utf-8")

    await redis_service.client.set(ticket_key, ticket_enc)
    await redis_service.client.expire(ticket_key, TICKET_TTL)

    return ticket_enc
