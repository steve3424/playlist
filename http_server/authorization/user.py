from .models import User
from fastapi import Request, HTTPException

def checkUserId(request: Request, user_info: User):
    if user_info.id != int(request.path_params["id"]):
        raise HTTPException(403, "Unauthorized access to resource!")

def checkUserName(request: Request, user_info: User):
    if user_info.name != request.path_params["name"]:
        raise HTTPException(403, "Unauthorized access to resource!")
