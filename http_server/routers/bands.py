import logging
import os
import aiosqlite as asql
from pathlib import Path
from typing import Annotated
from fastapi import APIRouter, Form, Depends, Query, UploadFile, File
from fastapi.responses import JSONResponse
from sqlite3.dbapi2 import IntegrityError, SQLITE_CONSTRAINT_UNIQUE, SQLITE_CONSTRAINT_NOTNULL
from ..data import db, files
from ..middlewares.authorization import band as band_auth
from ..middlewares.authorization import main as main_auth
from ..middlewares.authorization.main import Authorize
from ..middlewares.authorization.models import User, AppRoles

LOGGER = logging.getLogger(f"playlist.{__name__}")
BAND_NAME_MIN_LEN = 1
BAND_NAME_MAX_LEN = 64
SONG_NAME_MIN_LEN = 1
SONG_NAME_MAX_LEN = 64
FILE_SIZE_MAX = 1024 * 1024 * 50 # 50mb

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
        if include_members:
            return processBandMembers(await db.bandsAllWithMembers())
        return await db.bandsAll()
    elif user_info.role == AppRoles.user:
        if include_members:
            return processBandMembers(await db.bandByMemberWithMembers(user_info.id))
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
                return JSONResponse({"message": f"{name} not found!"}, status_code=404)
        raise ex

@router.delete("/{name}/members/{user_name}")
async def removeBandMember(
    name: str,
    user_name: str,
    user_info: User=Depends(Authorize(AppRoles.user, band_auth.isBandLeader))
):
    band_info = await db.bandByName(name)
    if not band_info:
        return JSONResponse({"message": f"{name} not found"}, status_code=404)
    if user_name == band_info[0]["leader"]:
        return JSONResponse({"message": "Cannot delete band leader!"}, status_code=422)
    num_deleted = await db.bandMemberDelete(name, user_name)
    if num_deleted == 0:
        return f"{user_name} not in band!"
    return f"Removed {user_name}!"

@router.post("/{name}/songs/{song_name}")
async def addSong(
    name: str,
    song_name: str,
    file: UploadFile = File(...),
    user_info: User=Depends(Authorize(AppRoles.user, band_auth.isBandMember))
):
    try:
        # TODO: should we make song_name param optional and
        #       use filename if not provided?
        if not song_name:
            song_name = ""
        song_name = song_name.strip()
        if len(song_name) < SONG_NAME_MIN_LEN:
            return JSONResponse({"message": f"Song name must be at least {SONG_NAME_MIN_LEN} characters, but was {len(song_name)}!"}, status_code=422)
        if SONG_NAME_MAX_LEN < len(song_name):
            return JSONResponse({"message": f"Song name can't be longer than {SONG_NAME_MAX_LEN} characters, but was {len(song_name)}"}, status_code=422)

        if file.size == 0:
            return JSONResponse({"message": "File is empty!"}, status_code=422)
        if FILE_SIZE_MAX < file.size:
            return JSONResponse({"message": f"File must be < {FILE_SIZE_MAX} bytes, but is {file.size} bytes!"}, status_code=413)

        # TODO: limit number of songs
        # TODO: detect and enforce file type
        file_dir = files.DATA_DIR / name
        file_dir.mkdir(exist_ok=True)
        await files.save(file, file_dir / f"{song_name}.pdf")
        await db.songAdd(song_name, name, user_info.id)
        return f"{song_name} added!"
    except IntegrityError as ex:
        if ex.sqlite_errorcode == SQLITE_CONSTRAINT_NOTNULL:
            return JSONResponse({"message": f"{name} not found!"}, status_code=404)
        if ex.sqlite_errorcode == SQLITE_CONSTRAINT_UNIQUE:
            return JSONResponse({"message": f"{song_name} already exists!"}, status_code=422)
        raise ex
# func: check band exists
#       check song exists
# @router.get("/{name}/songs")
# auth: must be member of band
# func: check band exists
# @router.get("/{name}/songs/{song_name}")
# auth: must be member of band
# func: check band exists
#       check song exists
# @router.delete("/{name}/songs/{song_name}")
# auth: must be member of band
#       TODO: anything else ?
# func: check band exists
#       check song exists
# TODO: add include_songs in band endpoints for admin?

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