from pydantic import BaseModel

class Ticket(BaseModel):
    user_id: str
    band: str

    def __str__(self):
        return f"{self.user_id}:{self.band}"
