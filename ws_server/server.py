"""
Websocket server.
"""

import logging
import logging.config
from logging_conf import LOGGING_CONFIG
logging.config.dictConfig(LOGGING_CONFIG)
import base64
import json
import binascii
import asyncio
from websockets import Headers, CloseCode
from websockets.asyncio.server import serve, ServerConnection
from websockets.exceptions import ConnectionClosedOK, ConnectionClosedError, ConnectionClosed

LOGGER = logging.getLogger(__name__)
CONNECTIONS = set()

class TicketError(BaseException):
    pass

def checkTicket(headers: Headers) -> dict:
    try:
        ticket = headers.get("sec-websocket-protocol", "").split(",")[0]
        if not ticket:
            raise TicketError("Ticket not found!")
        ticket = json.loads(base64.b16decode(ticket).decode("utf-8"))
        if not ticket.get("user_id", None) and not ticket.get("band", None):
            raise TicketError("Invalid ticket!")
        return ticket
    except json.decoder.JSONDecodeError:
        raise TicketError("Ticket is invalid JSON string!")
    except binascii.Error:
        raise TicketError("Ticket is invalid base16 string!")
    except UnicodeDecodeError:
        raise TicketError("Ticket is invalid utf-8 string!")

async def listen(websocket: ServerConnection):
    """
    Awaits for messages incoming on a connection. The loop
    will terminate if a client closes the connection.

    Parameters
    ----------
    websocket
        Connection to single client.
    """
    async for message in websocket:
        LOGGER.debug(f"Broadcasting message from client {websocket.remote_address} to {len(CONNECTIONS)} clients: '{message}'")

        # TODO: analyze message.
        for client in CONNECTIONS:
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
        LOGGER.info(f"Client {websocket.remote_address} sent message!")
    except ConnectionClosed as ex:
        LOGGER.error(f"ConnectionClosed while sending to {websocket.remote_address}: {ex}")
    except Exception as ex:
        LOGGER.error(f"Exception while sending to {websocket.remote_address}: {ex}")

async def connection_handler(websocket: ServerConnection):
    """
    Called when a new connection is made to server.

    Parameters
    ----------
    websocket
        Handle to client-specific connection.
    """
    
    LOGGER.debug(f"Client {websocket.remote_address} connected!")
    CONNECTIONS.add(websocket)
    close_code = 1000
    close_reason = ""
    try:
        ticket = checkTicket(websocket.request.headers)
        # TODO: do something w/ ticket
        await listen(websocket)
    except ConnectionClosedOK:
        LOGGER.info(f"ConnectionClosedOK sent {websocket.remote_address}!")
    except ConnectionClosedError as ex:
        LOGGER.error(f"ConnectionClosedError from {websocket.remote_address}: {ex}")
    except TicketError as ex:
        close_code = CloseCode.INTERNAL_ERROR
        close_reason = str(ex)
        LOGGER.error(close_reason)
    finally:
        await websocket.close(close_code, close_reason)
        CONNECTIONS.remove(websocket)
        LOGGER.debug(f"Client {websocket.remote_address} connection closed.")

async def run_server(host: str, port: int):
    """
    Starts the websocket server.

    Parameters
    ----------
    host
        Hostname to listen on.
    port
        Port to listen on.
    """
    server = None
    try:
        server = await serve(connection_handler, host, port)
        # Run forever
        await asyncio.Future()
    finally:
        await shutdown_server(server)

async def shutdown_server(server: serve | None):
    """
    Shut down server.

    Parameters
    ----------
    server
        Server instance.
    """
    global CONNECTIONS
    LOGGER.debug(f"Shutting down server. Closing {len(CONNECTIONS)} connections...")
    if server:
        server.close(close_connections=True)
        await server.wait_closed()
        LOGGER.debug("Shutdown complete!")

def main(host: str, port: int):
    try:
        asyncio.run(run_server(host, port))
    except KeyboardInterrupt:
        LOGGER.debug("ctrl+c stopped server!")

if __name__ == "__main__":
    main("0.0.0.0", 8080)
