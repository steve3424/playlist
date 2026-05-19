import logging
from fastapi import Request
from .models import User
from .main import AuthorizationError
from ...data import db

LOGGER = logging.getLogger(f"playlist.{__name__}")
BAND_MEMBERS_MAX = 5
BAND_CREATE_LIMIT = 10

async def createLimitReached(request: Request, user_info: User):
    created_count = await db.bandCountCreated(user_info.id)
    if BAND_CREATE_LIMIT <= created_count[0]["count"]:
        raise AuthorizationError(f"Cannot create more than {BAND_CREATE_LIMIT} bands!")

async def isBandLeaderAndMaxMembersEnforce(request: Request, user_info: User):
    band_name = request.path_params['name']
    band_owner = await db.bandLeader(band_name)
    if len(band_owner) < 1 or user_info.id != band_owner[0]["leader"]:
        raise AuthorizationError("Only band owner can add new members!")

    members = await db.bandMembers(band_name)
    if BAND_MEMBERS_MAX <= len(members):
        raise AuthorizationError(f"Max of {BAND_MEMBERS_MAX} members per band!")
