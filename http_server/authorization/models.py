from typing import Annotated
from enum import IntEnum
from pydantic import BaseModel, StringConstraints, NonNegativeInt

# NOTE: This much match db roles values!!
class AppRoles(IntEnum):
    user=0
    admin=1

class User(BaseModel):
    id: NonNegativeInt
    name: Annotated[str, StringConstraints(min_length=1)]
    role: AppRoles
