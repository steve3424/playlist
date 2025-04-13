import logging
import base64
import json
from fastapi import APIRouter, Depends, Request
from middlewares.auth import Authenticate

LOGGER = logging.getLogger(f"__main__.{__name__}")

router = APIRouter(prefix="/gig")

@router.get("/ticket")
async def ticket(
    band: str,
    user_info: dict=Depends(Authenticate(permission_level=1))
):
    # TODO: add to cache
    # TODO: return encrypted ticket
    return base64.b64encode(
        json.dumps(
            {"user_id": user_info["id"], "band": band},
            separators=(",", ":")
        ).encode("utf-8")
    ).decode("utf-8")
