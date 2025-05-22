import logging
from typing import Annotated
from enum import IntEnum
from fastapi import Request, HTTPException
from pydantic import BaseModel, StringConstraints, NonNegativeInt

LOGGER = logging.getLogger(f"playlist.{__name__}")

# NOTE: This much match db roles values!!
class AppRoles(IntEnum):
    user=0
    admin=1

class User(BaseModel):
    id: NonNegativeInt
    name: Annotated[str, StringConstraints(min_length=1)]
    role: AppRoles

class AuthorizeAppRole:
    def __init__(self, role: AppRoles):
        self.role = role

    def __call__(
        self,
        request: Request
    ) -> dict:
        user_info: User = request.state.user_info
        if user_info.role < self.role:
            raise HTTPException(403, "Unauthorized")
        return user_info