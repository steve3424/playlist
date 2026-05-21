import logging
from fastapi import Request
from .models import User
from .main import AuthorizationError
from ...data import db

LOGGER = logging.getLogger(f"playlist.{__name__}")
BAND_MEMBERS_MAX = 20
BAND_CREATE_LIMIT = 2

async def createLimitReached(request: Request, user_info: User):
    created_count = await db.bandCountCreated(user_info.id)
    if BAND_CREATE_LIMIT <= created_count[0]["count"]:
        raise AuthorizationError(f"Cannot create more than {BAND_CREATE_LIMIT} bands!")

async def isBandMember(request: Request, user_info: User):
    band_name = request.path_params['name']
    band_id = await db.bandByMemberAndName(band_name, user_info.id)
    if len(band_id) < 1:
        raise AuthorizationError(f"Not a member of '{band_name}'!")

async def isBandLeader(request: Request, user_info: User):
    band_name = request.path_params['name']
    band_leader = await db.bandLeader(band_name)
    if len(band_leader) < 1 or user_info.id != band_leader[0]["leader"]:
        raise AuthorizationError("Only band leader can do this!")

async def maxMembersReached(request: Request, user_info: User):
    band_name = request.path_params['name']
    members = await db.bandMembers(band_name)
    if BAND_MEMBERS_MAX <= len(members):
        raise AuthorizationError(f"Max of {BAND_MEMBERS_MAX} members per band!")

async def isBandLeaderAndNotMaxMembersReached(request: Request, user_info: User):
    await isBandLeader(request, user_info)
    await maxMembersReached(request, user_info)
