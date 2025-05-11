from pydantic import BaseModel

class Ticket(BaseModel):
    user_id: str
    band: str
