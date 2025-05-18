import logging
import base64
import redis.asyncio as redis
from typing import Annotated
from pydantic import BaseModel, StringConstraints
from .encryption import CIPHER

LOGGER = logging.getLogger(f"playlist.{__name__}")
CLIENT: redis.Redis = None
TICKET_TTL = 10 # seconds

class TicketError(Exception):
    pass

class Ticket(BaseModel):
    user_name: Annotated[str, StringConstraints(min_length=1)]
    band: Annotated[str, StringConstraints(min_length=1)]

    def __str__(self):
        return f"{self.user_name}:{self.band}"

async def init(host: str, port: int) -> bool:
    """
    Initializes cache client and pings to check if it
    can connect. We suppress all exceptions and return
    bool indicating successful connection.
    """
    # TODO: should use TLS if going over network.
    global CLIENT
    try:
        if not CLIENT:
            LOGGER.info(f"Starting ticket client on '{host}:{port}'...")
            CLIENT = redis.Redis(
                host=host,
                port=port,
                decode_responses=True,
            )
        await CLIENT.ping()
        return True
    except Exception as ex:
        LOGGER.error(f"Ticket client startup failed: {ex}")
        return False

async def shutdown() -> None:
    global CLIENT
    if CLIENT:
        LOGGER.info("Shutting down ticket client...")
        await CLIENT.aclose()
        CLIENT = None

async def checkTicket(ticket_enc: str) -> Ticket:
    """
    Decrypts ticket, checks against cache, and returns ticket object.
    """
    try:
        ticket = Ticket.model_validate_json(
            CIPHER.decrypt(
                base64.b16decode(ticket_enc)
            ).decode(encoding="utf-8")
        )
        cached_ticket = await CLIENT.get(str(ticket))
        if not cached_ticket:
            raise ValueError("Ticket not found in cache!")
        elif ticket_enc != cached_ticket:
            raise ValueError(f"Ticket received '{ticket_enc}' does not match cached ticket '{cached_ticket}'!")
        return ticket
    except Exception as ex:
        raise TicketError(ex) from ex

async def getTicket(user_name: str, band: str) -> str:
    """
    Creates ticket, adds to cache, and returns encrypted base16 ticket.
    """
    try:
        global TICKET_TTL
        ticket = Ticket(
            user_name=user_name,
            band=band
        )
        ticket_key = str(ticket)
        ticket_enc = base64.b16encode(
            CIPHER.encrypt(
                ticket.model_dump_json().encode("utf-8")
            )
        ).decode(
            encoding="utf-8"
        )
        await CLIENT.set(ticket_key, ticket_enc)
        await CLIENT.expire(ticket_key, TICKET_TTL)
        return ticket_enc
    except Exception as ex:
        raise TicketError(ex) from ex
