import logging
import base64
import time
from fastapi import APIRouter, Depends, HTTPException
from ..middlewares.auth import Authenticate
from ..services import redis_service
from common.encryption import CIPHER
from common.tickets import Ticket

LOGGER = logging.getLogger(f"playlist.{__name__}")
TICKET_TTL = 5 # seconds

router = APIRouter(prefix="/band")

@router.get("/gig")
async def gig(
    band: str,
    user_info: dict=Depends(Authenticate(permission_level=1))
):
    global TICKET_TTL

    try:
        time_gig_start = time.perf_counter()
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

        await redis_service.addKey(ticket_key, ticket_enc, TICKET_TTL)

        LOGGER.info(f"Ticket took {time.perf_counter() - time_gig_start}s!")
        return ticket_enc
    except redis_service.RedisError as ex:
        LOGGER.exception(ex)
        return HTTPException(500, "Error getting ticket.")