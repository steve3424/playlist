import logging
import time
from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from common.tickets import TicketError, getTicket
from ..middlewares.authentication import Authenticate

LOGGER = logging.getLogger(f"playlist.{__name__}")

router = APIRouter(prefix="/band")

@router.get("/ticket")
async def ticket(
    request: Request,
    band: str,
    user_info: dict={"name": "steve"}
):
    try:
        time_ticket_start = time.perf_counter()
        # TODO: determine if user is allowed to have ticket for requested band.
        ticket = await getTicket(user_info["name"], band)
        LOGGER.info(f"{request.url.path} took {time.perf_counter() - time_ticket_start}s!")
        return ticket
    except TicketError as ex:
        LOGGER.exception(ex)
        return JSONResponse({"message": "Error getting ticket!"}, status_code=500)
