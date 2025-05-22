"""
Sample client for connecting to local websocket host
and sending messages from console.
"""
import logging
import logging.config
from logging_conf import LOGGING_CONFIG
logging.config.dictConfig(LOGGING_CONFIG)
import time
import argparse
import requests
import asyncio
import aioconsole
from websockets.exceptions import ConnectionClosedOK, ConnectionClosedError
from websockets.asyncio.client import connect, ClientConnection

LOGGER = logging.getLogger(__name__)

async def wsListener(websocket: ClientConnection):
    LOGGER.info(f"Listening to {websocket.remote_address} for messages...")
    try:
        while True:
            incoming_msg = await websocket.recv()
            LOGGER.info(f"Received message '{incoming_msg}' from {websocket.remote_address}!")
    except ConnectionClosedOK as ex:
        # NOTE: Called when server initiates graceful shutdown
        LOGGER.info(f"ConnectionClosedOk from server: {ex}")
    except ConnectionClosedError as ex:
        # NOTE: Called when server quits unexpectedly
        LOGGER.error(f"ConnectionClosedError from server: {ex}")

async def inputListener(websocket: ClientConnection):
    LOGGER.info("Listening to console for messages...")
    try:
        while True:
            msg_to_send = await aioconsole.ainput()
            LOGGER.info(f"Sending '{msg_to_send}' to {websocket.remote_address}...")
            await websocket.send(msg_to_send)
            LOGGER.info("Message sent!")
    except EOFError as ex:
        LOGGER.info("EOFError stopping input listener...")

async def startClient(host: str, port: int, ticket: str):
    url = f"ws://{host}:{port}"
    LOGGER.info(f"Connecting to '{url}'...")
    async with connect(url, additional_headers={"sec-websocket-protocol": ticket}) as websocket:
        LOGGER.info(f"Connected from '{websocket.local_address[0]}:{websocket.local_address[1]}'!")
        in_task = asyncio.create_task(inputListener(websocket))
        rec_task = asyncio.create_task(wsListener(websocket))
        _, pending = await asyncio.wait(
            [
                in_task,
                rec_task,
            ],
            return_when=asyncio.FIRST_COMPLETED,
        )
        for task in pending:
            task.cancel()

def getTicket(host: str, port: int, band: str) -> str:
    url = f"http://{host}:{port}/band/ticket?band={band}"
    LOGGER.info(f"Requesting ticket from '{url}'...")
    time_start_get_ticket = time.perf_counter()
    response = requests.get(url, timeout=10)
    if response.status_code != 200:
        raise Exception(response.json())
    LOGGER.info(f"Got ticket in {time.perf_counter() - time_start_get_ticket:.3f}s!")
    return response.text

def main(ws_host: str, ws_port: int, ticket_host: str, ticket_port: int, band: str):
    try:
        asyncio.run(startClient(ws_host, ws_port, getTicket(ticket_host, ticket_port, band)))
    except KeyboardInterrupt:
        LOGGER.info("ctrl+c stopped client!")
    except ConnectionRefusedError as ex:
        LOGGER.error(f"Unable to connect: {ex}")

if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("--ws-host", type=str, default="localhost")
    arg_parser.add_argument("--ws-port", type=int, default=8080)
    arg_parser.add_argument("--ticket-host", type=str, default="localhost")
    arg_parser.add_argument("--ticket-port", type=int, default=80)
    arg_parser.add_argument("--band", type=str, required=True)
    args = arg_parser.parse_args()

    ws_host = args.ws_host
    ws_port = args.ws_port
    ticket_host = args.ticket_host
    ticket_port = args.ticket_port
    band = args.band
    main(ws_host, ws_port, ticket_host, ticket_port, band)
