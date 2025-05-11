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
import time
from encryption import CIPHER, EncryptionError
from websockets import Headers, CloseCode
from websockets.asyncio.server import serve, ServerConnection
from websockets.exceptions import ConnectionClosedOK, ConnectionClosedError, ConnectionClosed

LOGGER = logging.getLogger(__name__)
CONNECTIONS = {
    # "<band_name>": <set(websockets)>
}

class TicketError(BaseException):
    pass

def checkTicket(headers: Headers) -> dict:
    try:
        time_start_check_ticket = time.perf_counter()
        ticket = headers.get("sec-websocket-protocol", "").split(",")[0]
        if not ticket:
            raise ValueError("Ticket not found!")
        ticket = json.loads(
            CIPHER.decrypt(
                base64.b16decode(ticket)
            ).decode(encoding="utf-8")
        )
        if not ticket.get("user_id", None) and not ticket.get("band", None):
            raise TicketError("Invalid ticket!")
        LOGGER.debug(f"checkTicket took {time.perf_counter() - time_start_check_ticket:.6f}s!")
        return ticket
    except json.decoder.JSONDecodeError as ex:
        raise TicketError("Ticket is invalid JSON string!") from ex
    except binascii.Error as ex:
        raise TicketError("Ticket is invalid base16 string!") from ex
    except UnicodeDecodeError as ex:
        raise TicketError("Ticket is invalid utf-8 string!") from ex
    except EncryptionError as ex:
        raise TicketError("Ticket unable to be decrypted!") from ex
    except ValueError as ex:
        raise TicketError(ex) from ex

async def listen(websocket: ServerConnection, band: str):
    """
    Awaits for messages incoming on a connection. The loop
    will terminate if a client closes the connection.

    Parameters
    ----------
    websocket
        Connection to single client.
    """
    global CONNECTIONS
    async for message in websocket:
        other_band_members = CONNECTIONS[band] - {websocket}
        LOGGER.debug(f"Broadcasting message from client {websocket.remote_address} to {len(other_band_members)} clients: '{message}'")

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
        LOGGER.info(f"Client {websocket.remote_address} sent message!")
    except ConnectionClosed as ex:
        LOGGER.exception(f"ConnectionClosed while sending to {websocket.remote_address}: {ex}")
    except Exception as ex:
        LOGGER.exception(f"Exception while sending to {websocket.remote_address}: {ex}")

async def connect(websocket: ServerConnection):
    """
    Called when a new connection is made to server.

    Parameters
    ----------
    websocket
        Handle to client-specific connection.
    """
    global CONNECTIONS
    LOGGER.info(f"Connect request from {websocket.remote_address}...")
    close_code = 1000
    close_reason = ""
    band = None
    try:
        ticket = checkTicket(websocket.request.headers)
        band = ticket["band"]
        CONNECTIONS[band] = CONNECTIONS.get(band, set()) | {websocket}
        LOGGER.info(f"Connected to {band}!")

        await listen(websocket, band)
    except ConnectionClosedOK:
        # TODO: when is this thrown?
        LOGGER.info(f"ConnectionClosedOK sent {websocket.remote_address}!")
    except ConnectionClosedError as ex:
        # TODO: when is this thrown?
        LOGGER.exception(f"ConnectionClosedError from {websocket.remote_address}: {ex}")
        close_code = CloseCode.INTERNAL_ERROR
        close_reason = "Unknown"
    except TicketError as ex:
        LOGGER.exception(ex)
        close_code = CloseCode.INTERNAL_ERROR
        close_reason = "Invalid ticket!"
    finally:
        await websocket.close(close_code, close_reason)
        if band:
            CONNECTIONS[band].remove(websocket)
        LOGGER.debug(f"Client {websocket.remote_address} connection closed.")

async def startServer(host: str, port: int):
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
        server = await serve(connect, host, port)
        # Run forever
        await asyncio.Future()
    except Exception as ex:
        LOGGER.exception(f"Startup error: {ex}")
    finally:
        await shutdown(server)

async def shutdown(server: serve | None):
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

def main(host: str, port: int):
    try:
        asyncio.run(startServer(host, port))
    except KeyboardInterrupt:
        LOGGER.debug("ctrl+c stopped server!")

if __name__ == "__main__":
    main("0.0.0.0", 8080)
