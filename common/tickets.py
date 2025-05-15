from typing import Annotated
from pydantic import BaseModel, StringConstraints

class Ticket(BaseModel):
    user_id: Annotated[str, StringConstraints(min_length=1)]
    band: Annotated[str, StringConstraints(min_length=1)]

    def __str__(self):
        return f"{self.user_id}:{self.band}"
