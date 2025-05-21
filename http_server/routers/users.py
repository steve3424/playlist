import os
import logging
import bcrypt
import base64
from typing import Annotated
from fastapi import APIRouter, Form, Request, Depends
from fastapi.responses import JSONResponse
from ..services import db
from ..middlewares.authentication import Authenticate

LOGGER = logging.getLogger(f"playlist.{__name__}")
PASSWORD_MIN_LEN = 8
PASSWORD_MAX_LEN = 32
USERNAME_MIN_LEN = 1
USERNAME_MAX_LEN = 32

router = APIRouter(prefix="/users")

@router.post("")
async def register(
    user_name: Annotated[str, Form()],
    password: Annotated[str, Form()],
):
    if not user_name:
        return JSONResponse({"message": "Password can't be empty!"}, status_code=422)
    user_name = user_name.strip()
    if len(user_name) < USERNAME_MIN_LEN or USERNAME_MAX_LEN < len(user_name):
        return JSONResponse({"message": f"Username length must be {USERNAME_MIN_LEN} <= and <= {USERNAME_MAX_LEN}!"}, status_code=422)
    if await db.userExists(user_name):
        return JSONResponse({"message": f"Username '{user_name}' already taken!"}, status_code=422)

    if not password:
        return JSONResponse({"message": "Password can't be empty!"}, status_code=422)
    password = password.strip()
    if len(password) < PASSWORD_MIN_LEN or PASSWORD_MAX_LEN < len(password):
        return JSONResponse({"message": f"Password length must be {PASSWORD_MIN_LEN} <= and <= {PASSWORD_MAX_LEN}!"}, status_code=422)
    password_enc = base64.b64encode(bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())).decode("utf-8")

    await db.userAdd(user_name, password_enc)
    return JSONResponse({"message": f"Welcome {user_name}!"})

@router.get("")
async def usersAll(
    request: Request,
):
    LOGGER.info(request.state.user_info)
    return await db.usersAll()

@router.get("/{id}")
async def userById(
    request: Request,
    id: int
):
    return id
