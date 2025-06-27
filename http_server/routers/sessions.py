import logging
import bcrypt
import base64
from typing import Annotated
from fastapi import APIRouter, Form, Depends
from fastapi.responses import JSONResponse
from ..data import db
from ..authorization.models import User, AppRoles
from ..authorization.endpoint import AuthorizeEndpoint
from ..middlewares import authentication

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
    user_info: User=Depends(AuthorizeEndpoint(AppRoles.admin))
):
    return await authentication.sessionAll()
    # raise NotImplementedError()

@router.delete("/{name}")
async def logout(
    user_info: User=Depends(AuthorizeEndpoint(AppRoles.admin))
):
    raise NotImplementedError()

@router.get("/{name}")
async def userSession(
    session_id: str,
    user_info: User=Depends(AuthorizeEndpoint(AppRoles.user))
):
    raise NotImplementedError()
    # user_info, session_id = await authentication.sessionGet(session_id=session_id)
    # if not user_info:
    #     return JSONResponse({"message": "Not Found!"}, status_code=404)
    # user_info = user_info.model_dump()
    # user_info["role"] = AppRoles(user_info["role"]).name
    # user_info["session_id"] = session_id
    # return user_info
