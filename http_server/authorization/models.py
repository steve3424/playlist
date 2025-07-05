from typing import Annotated, Union, Optional
from enum import IntEnum
from pydantic import BaseModel, StringConstraints, NonNegativeInt, field_serializer, field_validator

# NOTE: This much match db roles values!!
class AppRoles(IntEnum):
    user=0
    admin=1

class User(BaseModel):
    id: NonNegativeInt
    name: Annotated[str, StringConstraints(min_length=1)]
    role: Union[AppRoles, str]
    session_id: Optional[str]=None

    @field_validator("role")
    def roleValidator(value: AppRoles | str) -> AppRoles:
        if isinstance(value, str):
            value = AppRoles[value]
        return value

    @field_serializer("role")
    def roleToString(self, role: AppRoles) -> str:
        return role.name

    def __hash__(self) -> int:
        return self.id
