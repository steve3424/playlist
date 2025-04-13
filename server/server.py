"""
Websocket server.
"""

import logging
import logging.config
from logging_conf import LOGGING_CONFIG
logging.config.dictConfig(LOGGING_CONFIG)
import asyncio
from websockets.asyncio.server import serve, ServerConnection
from websockets.exceptions import ConnectionClosedOK, ConnectionClosedError

LOGGER = logging.getLogger(f"__main__.{__name__}")
CONNECTIONS = set()

async def recv_handler(websocket: ServerConnection):
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
            asyncio.create_task(send_handler(client, message))
        # TODO: maybe client specific response here.

# TODO: If client closes here, how do we remove from connections set.
#       Do we remove here or propgate up the exception/some return value
#       to close out the connection handler? Maybe this function just
#       reports the results and the calling code is responsible for
#       the removal of the connections.
async def send_handler(websocket: ServerConnection, message: str):
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
    except ConnectionClosedError as ex:
        LOGGER.info(f"Client {websocket.remote_address} connection closed with error: {ex}")
    except ConnectionClosedOK:
        LOGGER.info(f"Client {websocket.remote_address} closed connection.")
    except Exception as ex:
        LOGGER.exception(f"Client {websocket.remote_address} send error: {ex}")

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
    try:
        await recv_handler(websocket)
    finally:
        LOGGER.debug(f"Client {websocket.remote_address} closed connection.")
        CONNECTIONS.remove(websocket)

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
        LOGGER.info(f"Listening on {host}:{port}...")
        # Run forever
        await asyncio.Future()
    finally:
        LOGGER.debug(f"Server stopped closing {len(CONNECTIONS)} connections...")
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
    host = "0.0.0.0"
    port = 8080
    main(host, port)