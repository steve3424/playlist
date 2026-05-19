import logging
from typing import Annotated
from fastapi import APIRouter, Form, Depends
from fastapi.responses import JSONResponse
from sqlite3.dbapi2 import IntegrityError
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
async def all(user_info: User=Depends(Authorize(AppRoles.user, main_auth.noop))):
    if user_info.role == AppRoles.admin:
        return await db.bandsAll()
    elif user_info.role == AppRoles.user:
        return await db.bandByMember(user_info.id)
    raise NotImplementedError()

@router.get("/{name}")
async def getBandInfo():
    raise NotImplementedError()

@router.delete("/{name}")
async def delete(user_info: User=Depends(Authorize())):
    raise NotImplementedError()

@router.get("/{name}/members")
async def getBandMembers():
    raise NotImplementedError()

@router.post("/{name}/members")
async def addBandMember(
    name: str,
    user_name: Annotated[str, Form()],
    user_info: User=Depends(Authorize(AppRoles.user, band_auth.isBandLeaderAndMaxMembersEnforce))
):
    member_inserted = await db.bandAddMember(name, user_name)
    if not member_inserted:
        raise Exception(f"Member {user_name} not inserted into {name} :(")
    return f"{user_name} added to {name}!"

@router.delete("/{name}/members")
async def removeBandMember():
    raise NotImplementedError()
