import logging
import base64
import json
from fastapi import APIRouter, Depends
from ..middlewares.auth import Authenticate
from common.encryption import CIPHER
from common.tickets import Ticket

LOGGER = logging.getLogger(f"__main__.{__name__}")

router = APIRouter(prefix="/gig")

@router.get("/ticket")
async def ticket(
    band: str,
    user_info: dict=Depends(Authenticate(permission_level=1))
):
    # TODO: add to cache
    # TODO: determine if user is allowed to join gig w/ requested
    #       band.
    return base64.b16encode(
        CIPHER.encrypt(
            Ticket(
                user_id=user_info["id"],
                band=band
            ).model_dump_json().encode("utf-8")
        )
    ).decode(encoding="utf8")
