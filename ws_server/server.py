"""
Websocket server.
"""
import logging
import logging.config
from . import logging_conf
from .logging_conf import LOGGING_CONFIG
logging.config.dictConfig(LOGGING_CONFIG)
import argparse
import asyncio
import time
from common import tickets
from common.tickets import Ticket, TicketError, checkTicket
from websockets import Headers, CloseCode
from websockets.asyncio.server import Server, serve, ServerConnection
from websockets.exceptions import ConnectionClosed, ConnectionClosedOK, ConnectionClosedError

LOGGER = logging.getLogger("ws_server")
CONNECTIONS = {
    # "<band_name>": <set(websockets)>
}
TICKET_HEADER_NAME = "sec-websocket-protocol"

async def _checkTicket(headers: Headers) -> Ticket:
    global TICKET_HEADER_NAME
    try:
        time_start_check_ticket = time.perf_counter()
        ticket_enc = headers.get(TICKET_HEADER_NAME, "")
        ticket_enc = ticket_enc.split(",")[0]
        if not ticket_enc:
            raise ValueError("Ticket not found in headers!")
    except Exception as ex:
        LOGGER.error(f"{TICKET_HEADER_NAME}: '{ticket_enc}'")
        raise TicketError(ex) from ex

    ticket = checkTicket(ticket_enc)
    LOGGER.debug(f"Ticket validated in {time.perf_counter() - time_start_check_ticket:.6f}s!")
    return ticket

async def listen(websocket: ServerConnection, band: str):
    """
    Awaits for messages incoming on a connection. The loop
    will terminate if a client closes the connection.

    Parameters
    ----------
    websocket
        Connection to single client.
    band
        Name of the band to connect to.
    """
    global CONNECTIONS
    async for message in websocket:
        other_band_members = CONNECTIONS[band] - {websocket}
        LOGGER.debug(f"Broadcasting to {len(other_band_members)} clients...")

        # TODO: analyze message.
        for client in other_band_members:
            asyncio.create_task(send(client, message))
        # TODO: maybe client specific response here.

async def send(websocket: ServerConnection, message: str):
    """
    Sends single message to single client. We may find out here that
    a client disconnected.

    Parameters
    ----------
    websocket
        Connection to single client.
    message
        Message to send.
    """
    try:
        await websocket.send(message)
        LOGGER.debug(f"Message sent to {websocket.remote_address[0]}:{websocket.remote_address[1]}!")
    except ConnectionClosed as ex:
        LOGGER.exception(f"ConnectionClosed while sending to {websocket.remote_address}: {ex}")
    except Exception as ex:
        LOGGER.exception(f"Error while sending to {websocket.remote_address}: {ex}")

async def connect(websocket: ServerConnection):
    """
    Called when a new connection is made to server.

    Parameters
    ----------
    websocket
        Handle to client-specific connection.
    """
    global CONNECTIONS
    logging_conf.IP_PORT.set(f"{websocket.remote_address[0]}:{websocket.remote_address[1]}")

    LOGGER.info("Connecting...")
    close_code = 1000
    close_reason = ""
    band = None
    try:
        ticket = await _checkTicket(websocket.request.headers)
        band = ticket.band

        logging_conf.BAND.set(ticket.band)
        logging_conf.USER_ID.set(ticket.user_id)
        CONNECTIONS[ticket.band] = CONNECTIONS.get(ticket.band, set()) | {websocket}
        LOGGER.info("Connected!")
        await listen(websocket, ticket.band)
    except ConnectionClosedOK as ex:
        # TODO: when is this thrown?
        LOGGER.info(f"ConnectionClosedOK: {ex}!")
    except ConnectionClosedError as ex:
        # NOTE: Called when client dies unexpectedly
        LOGGER.error(f"ConnectionClosedError: {ex}!")
    except TicketError as ex:
        LOGGER.exception(ex)
        close_code = CloseCode.INVALID_DATA
        close_reason = "Invalid ticket!"
    finally:
        await websocket.close(close_code, close_reason)
        if band:
            CONNECTIONS[ticket.band].remove(websocket)
        LOGGER.debug("Connection closed!")

async def startServer(host: str, port: int, redis_host: str, redis_port: int):
    """
    Starts the websocket server and redis client.

    Parameters
    ----------
    host
        Hostname to listen on.
    port
        Port to listen on.
    redis_host
        Redis hostname to connect to.
    redis_port
        Redis port to connect to.
    """
    server = None
    try:
        tickets.init(redis_host, redis_port)
        server = await serve(connect, host, port)
        # Run forever
        await asyncio.Future()
    except Exception as ex:
        LOGGER.exception(f"Startup error: {ex}")
    finally:
        await shutdown(server)
        await tickets.shutdown()

async def shutdown(server: Server | None):
    """
    Shut down server. Server may be none if exception
    is thrown on startup.

    Parameters
    ----------
    server
        Server instance.
    """
    global CONNECTIONS
    if server:
        num_connections = sum(len(conns) for band,conns in CONNECTIONS.items())
        LOGGER.info(f"Shutting down server. Closing {num_connections} connections...")
        server.close(close_connections=True)
        await server.wait_closed()
        LOGGER.info("Shutdown complete!")
    else:
        LOGGER.error("Error on server startup!")

def main(host: str, port: int, redis_host: str, redis_port: int):
    try:
        asyncio.run(startServer(host, port, redis_host, redis_port))
    except KeyboardInterrupt:
        LOGGER.debug("ctrl+c stopped server!")

if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("--host", type=str, default="0.0.0.0")
    arg_parser.add_argument("--port", type=int, default=8080)
    arg_parser.add_argument("--redis-host", type=str, default="localhost")
    arg_parser.add_argument("--redis-port", type=int, default=6379)
    args = arg_parser.parse_args()

    main(args.host, args.port, args.redis_host, args.redis_port)
