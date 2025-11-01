from .models import User
from .main import AuthorizationError
from fastapi import Request

def checkUserId(request: Request, user_info: User):
    if user_info.id != int(request.path_params["id"]):
        raise AuthorizationError()

def checkUserName(request: Request, user_info: User):
    if user_info.name != request.path_params["name"]:
        raise AuthorizationError()

