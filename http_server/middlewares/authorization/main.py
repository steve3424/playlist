import logging
from typing import Callable
from fastapi import Request
from .models import User, AppRoles

LOGGER = logging.getLogger(f"playlist.{__name__}")

class AuthorizationError(Exception):
    def __init__(self, message=None):
        if message is None:
            message = "Unauthorized"
        super().__init__(message)

class Authorize:
    def __init__(self, role: AppRoles=None, endpoint_authorization: Callable | None=None):
        self.role = role if role is not None else AppRoles.admin
        self.endpoint_authorization = endpoint_authorization
        if self.role.value < AppRoles.admin.value and self.endpoint_authorization == None:
            raise Exception(f"Endpoint allows role '{self.role.name}', but has no further authorizations!")

    def __call__(
        self,
        request: Request
    ) -> dict:
        user_info: User = request.state.user_info
        if user_info.role < self.role:
            raise AuthorizationError()
        elif user_info.role < AppRoles.admin.value:
            self.endpoint_authorization(request, user_info)
        return user_info
