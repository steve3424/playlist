import logging
import base64
import json
from fastapi import APIRouter, Depends
from middlewares.auth import Authenticate
from services.encryption import CIPHER

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
            json.dumps(
                    {"user_id": user_info["id"], "band": band},
                    separators=(",", ":")
            ).encode("utf8")
        )
    ).decode(encoding="utf8")
