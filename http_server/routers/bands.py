import logging
from typing import Annotated
from fastapi import APIRouter, Form, Depends, Query
from fastapi.responses import JSONResponse
import aiosqlite as asql
from sqlite3.dbapi2 import IntegrityError, SQLITE_CONSTRAINT_UNIQUE, SQLITE_CONSTRAINT_NOTNULL
from ..data import db
from ..middlewares.authorization import band as band_auth
from ..middlewares.authorization import main as main_auth
from ..middlewares.authorization.main import Authorize
from ..middlewares.authorization.models import User, AppRoles

LOGGER = logging.getLogger(f"playlist.{__name__}")
BAND_NAME_MIN_LEN = 1
BAND_NAME_MAX_LEN = 64

router = APIRouter(prefix="/bands", tags=["bands"])

@router.post("")
async def createBand(
    band_name: Annotated[str, Form()],
    user_info: User=Depends(Authorize(AppRoles.user, band_auth.createLimitReached))
) -> JSONResponse:
    if band_name is None:
        band_name = ""
    band_name = band_name.strip()
    if len(band_name) < BAND_NAME_MIN_LEN:
        return JSONResponse({"message": f"Username must be at least {BAND_NAME_MIN_LEN} characters, but was {len(band_name)}!"}, status_code=422)
    if BAND_NAME_MAX_LEN < len(band_name):
        return JSONResponse({"message": f"Username can't be longer than {BAND_NAME_MAX_LEN} characters, but was {len(band_name)}"}, status_code=422)

    try:
        await db.bandAdd(band_name, user_info.id)
        band = await db.bandByName(band_name)
        return band[0]
    except IntegrityError as ex:
        return JSONResponse({"message": f"Band name '{band_name}' already taken!"}, status_code=422)

@router.get("")
async def all(
    include_members: Annotated[bool, Query()]=False,
    user_info: User=Depends(Authorize(AppRoles.user, main_auth.noop))
):
    # TODO: include_members param
    if user_info.role == AppRoles.admin:
        return await db.bandsAll()
    elif user_info.role == AppRoles.user:
        return await db.bandByMember(user_info.id)

@router.get("/{name}")
async def getBand(
    name: str,
    include_members: Annotated[bool, Query()]=False,
    user_info: User=Depends(Authorize(AppRoles.user, band_auth.isBandMember))
):
    results = None
    if include_members:
        results = processBandMembers(await db.bandByNameWithMembers(name))
    else:
        results = await db.bandByName(name)

    if not results:
        return JSONResponse({"message": "Not found!"}, status_code=404)
    return results

@router.delete("/{name}")
async def deleteBand(
    name: str,
    user_info: User=Depends(Authorize(AppRoles.user, band_auth.isBandLeader))
):
    # NOTE: test cases
    # 1. admin can delete band with only owner member
    # 2. admin cannot delete band with multiple members
    # 3. admin can delete own band with only owner member
    # 4. admin cannot delete own band with only owner member
    # 5. user cannot delete band with only owner member
    # 6. user cannot delete band with multiple members
    # 7. user can delete own band with only owner member
    # 8. user cannot delete own band with multiple members
    members = await db.bandMembers(name)
    leader = await db.bandLeader(name)
    if 1 < len(members) or members[0]["id"] != leader[0]["leader"]:
        return JSONResponse({"message": "Band leader must remove all other members in order to delete band!"}, status_code=422)
    await db.bandDelete(name, leader[0]["leader"])
    return f"'{name}' deleted!"

@router.post("/{name}/members/{user_name}")
async def addBandMember(
    name: str,
    user_name: str,
    user_info: User=Depends(Authorize(AppRoles.user, band_auth.isBandLeaderAndNotMaxMembersReached))
):
    # NOTE: test cases
    # 1. insert member twice
    # 2. band not found
    # 3. user not found
    # 4. user cannot add to not-leader band
    # 5. user cannot break member limit
    try:
        member_inserted = await db.bandAddMember(name, user_name)
        if not member_inserted:
            raise Exception("DB error!")
        return f"{user_name} added to {name}!"
    except IntegrityError as ex:
        if ex.sqlite_errorcode == SQLITE_CONSTRAINT_UNIQUE:
            return JSONResponse({"message": f"{user_name} is already a member of {name}!"}, status_code=422)
        elif ex.sqlite_errorcode == SQLITE_CONSTRAINT_NOTNULL:
            if str(ex).endswith("user_id"):
                return JSONResponse({"message": f"{user_name} not found!"}, status_code=422)
            elif str(ex).endswith("band_id"):
                return JSONResponse({"message": f"{name} not found!"}, status_code=422)
        raise ex

# @router.delete("/{name}/members/{user_name}")
# async def removeBandMember():
#     raise NotImplementedError()


def processBandMembers(members: list[asql.Row]) -> list[dict]:
    bands = {}
    for m in members:
        if m["id"] not in bands:
            bands[m["id"]] = {
                "id": m["id"],
                "name": m["band_name"],
                "leader": m["leader"],
                "created_by": m["created_by"],
                "created_ts": m["created_ts"],
                "updated_ts": m["updated_ts"],
                "members": []
            }
        bands[m["id"]]["members"].append(
            {
                "id": m["user_id"],
                "name": m["user_name"]
            }
        )
    
    return [key for _,key in bands.items()]