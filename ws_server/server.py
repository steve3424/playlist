"""
Websocket server.
"""
import logging
import logging.config
from . import logging_conf
from .logging_conf import LOGGING_CONFIG
logging.config.dictConfig(LOGGING_CONFIG)
import base64
import argparse
import asyncio
import time
import redis.asyncio as redis
from common.encryption import CIPHER
from common.tickets import Ticket
from websockets import Headers, CloseCode
from websockets.asyncio.server import Server, serve, ServerConnection
from websockets.exceptions import ConnectionClosed, ConnectionClosedOK, ConnectionClosedError

LOGGER = logging.getLogger("ws_server")
REDIS_CLIENT: redis.Redis = None
CONNECTIONS = {
    # "<band_name>": <set(websockets)>
}
TICKET_HEADER_NAME = "sec-websocket-protocol"

class TicketError(BaseException):
    pass

async def checkTicket(headers: Headers) -> Ticket:
    global REDIS_CLIENT
    global TICKET_HEADER_NAME
    try:
        time_start_check_ticket = time.perf_counter()
        ticket_enc = headers.get(TICKET_HEADER_NAME, "")
        ticket = ticket_enc.split(",")[0]
        if not ticket:
            raise ValueError("Ticket not found!")
        ticket = Ticket.model_validate_json(
            CIPHER.decrypt(
                base64.b16decode(ticket)
            ).decode(encoding="utf-8")
        )
        cached_ticket = await REDIS_CLIENT.get(str(ticket))
        if not cached_ticket:
            raise Exception("Ticket not found!")
        elif ticket_enc != cached_ticket:
            raise Exception(f"Ticket does not match '{cached_ticket}'!")

        LOGGER.debug(f"Ticket validated in {time.perf_counter() - time_start_check_ticket:.6f}s!")
        return ticket
    except Exception as ex:
        LOGGER.error(f"{TICKET_HEADER_NAME}: '{ticket_enc}'")
        raise TicketError(ex) from ex

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
        ticket = await checkTicket(websocket.request.headers)
        band = ticket.band

        logging_conf.USER_ID.set(ticket.user_id)
        logging_conf.BAND.set(ticket.band)
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
        redisInit(redis_host, redis_port)
        server = await serve(connect, host, port)
        # Run forever
        await asyncio.Future()
    except Exception as ex:
        LOGGER.exception(f"Startup error: {ex}")
    finally:
        await shutdown(server)
        await redisShutdown()

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

def redisInit(host: str, port: int):
    global REDIS_CLIENT
    if not REDIS_CLIENT:
        LOGGER.info(f"Starting redis client on '{host}:{port}'...")
        REDIS_CLIENT = redis.Redis(
            host=host,
            port=port,
            decode_responses=True,
        )

async def redisShutdown():
    global REDIS_CLIENT
    LOGGER.info("Killing redis client...")
    if REDIS_CLIENT:
        await REDIS_CLIENT.aclose()
        REDIS_CLIENT = None

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
