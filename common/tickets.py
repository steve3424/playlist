import logging
import base64
import os
import redis.asyncio as redis
from typing import Annotated
from pydantic import BaseModel, StringConstraints
from .encryption import AESCipher

LOGGER = logging.getLogger(f"playlist.{__name__}")
CLIENT: redis.Redis = None
TICKET_TTL = 10 # seconds
TICKET_PREFIX = "ticket"
CIPHER = None

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
    global CIPHER
    try:
        if not CIPHER:
            secret = os.environ.get("TICKET_SECRET", None)
            salt = os.environ.get("TICKET_SECRET_SALT", None)
            if not secret:
                raise ValueError("TICKET_SECRET not found in env!")
            elif not salt:
                raise ValueError("TICKET_SECRET_SALT not found in env!")
            CIPHER = AESCipher(secret.encode(encoding="utf-8"), salt.encode(encoding="utf-8"))

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

async def redeem(ticket_enc: str) -> Ticket:
    """
    Decrypts ticket, checks against cache, and returns ticket object.
    """
    global CLIENT
    global CIPHER
    global TICKET_PREFIX
    try:
        ticket = Ticket.model_validate_json(
            CIPHER.decrypt(
                base64.b16decode(ticket_enc)
            ).decode(encoding="utf-8")
        )
        ticket_key = f"{TICKET_PREFIX}:{str(ticket)}"
        cached_ticket = await CLIENT.get(ticket_key)
        if not cached_ticket:
            raise ValueError("Ticket not found in cache!")
        elif ticket_enc != cached_ticket:
            raise ValueError(f"Ticket received '{ticket_enc}' does not match cached ticket '{cached_ticket}'!")
        await CLIENT.delete(ticket_key)
        return ticket
    except Exception as ex:
        raise TicketError(ex) from ex

async def create(user_name: str, band: str) -> str:
    """
    Creates ticket, adds to cache, and returns encrypted base16 ticket.
    """
    global TICKET_TTL
    global CIPHER
    global TICKET_PREFIX
    try:
        ticket = Ticket(
            user_name=user_name,
            band=band
        )
        ticket_key = f"{TICKET_PREFIX}:{str(ticket)}"
        ticket_enc = base64.b16encode(
            CIPHER.encrypt(
                ticket.model_dump_json().encode("utf-8")
            )
        ).decode(
            encoding="utf-8"
        )
        # TODO: transactions
        await CLIENT.set(ticket_key, ticket_enc)
        await CLIENT.expire(ticket_key, TICKET_TTL)
        return ticket_enc
    except Exception as ex:
        raise TicketError(ex) from ex
