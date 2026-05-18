from fastapi import Request
from .models import User, AppRoles
from .main import AuthorizationError
from ...data import db

BAND_CREATE_LIMIT = 10

async def createLimitReached(request: Request, user_info: User):
    if user_info.role < AppRoles.admin:
        created_count = await db.bandCountCreated(user_info.id)
        if BAND_CREATE_LIMIT <= created_count[0]["count"]:
            raise AuthorizationError(f"Cannot create more than {BAND_CREATE_LIMIT} bands!")