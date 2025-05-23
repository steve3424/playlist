import logging
from typing import Callable
from fastapi import Request, HTTPException
from .models import User, AppRoles

LOGGER = logging.getLogger(f"playlist.{__name__}")

class AuthorizeEndpoint:
    def __init__(self, role: AppRoles, endpoint_authorization: Callable|None=None):
        self.role = role
        self.endpoint_authorization = endpoint_authorization

    def __call__(
        self,
        request: Request
    ) -> dict:
        user_info: User = request.state.user_info
        if user_info.role < self.role:
            raise HTTPException(403, "Unauthorized!")
        elif user_info.role < max(e.value for e in AppRoles) and self.endpoint_authorization:
            # NOTE: user does not have max permissions AND
            #       this endpoint requries further authorization
            self.endpoint_authorization(request, user_info)
        return user_info
