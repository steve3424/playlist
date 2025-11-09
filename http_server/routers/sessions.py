import logging
import bcrypt
import base64
from typing import Annotated
from fastapi import APIRouter, Form, Depends
from fastapi.responses import JSONResponse
from ..data import db
from ..middlewares import authentication
from ..middlewares.authorization import user as user_auth
from ..middlewares.authorization.models import User, AppRoles
from ..middlewares.authorization.main import Authorize

LOGGER = logging.getLogger(f"playlist.{__name__}")

router = APIRouter(prefix="/sessions", tags=["sessions"])

@router.post("")
async def login(
    user_name: Annotated[str, Form()],
    password: Annotated[str, Form()],
):
    results = await db.userAndPasswordByName(user_name)
    if not results:
        return JSONResponse({"message": "User name or password incorrect!"}, status_code=401)
    user = dict(results[0])
    if not bcrypt.checkpw(password.encode("utf-8"), base64.b64decode(user["password"])):
        return JSONResponse({"message": "User name or password incorrect!"}, status_code=401)
    del user["password"]
    return user

@router.get("")
async def all(
    user_info: User=Depends(Authorize())
):
    return await authentication.sessionAll()

@router.delete("/{name}")
async def logout(
    name: str,
    user_info: User=Depends(Authorize(AppRoles.user, user_auth.checkUserName))
):
    await authentication.sessionDelete(name)
    return JSONResponse({"message": f"'{name}' logged out!"}, status_code=200)

# TODO: allow session_id and create new auth method to check name/session_id
@router.get("/{name}")
async def userSession(
    name: str,
    user_info: User=Depends(Authorize(AppRoles.user, user_auth.checkUserName))
):
    return await authentication.sessionGet(name)
