import os
import asyncio
import aioconsole
from websockets.asyncio.client import connect, ClientConnection
from websockets.exceptions import ConnectionClosed

async def process_message_from_server(msg: str):
    pass

async def rec_handler(websocket: ClientConnection):
    print(f"Listening to {websocket.remote_address} for messages...")
    while True:
        incoming_msg = await websocket.recv()
        print(f"Received message '{incoming_msg}' from {websocket.remote_address}!")

async def input_listener(websocket: ClientConnection):
    print("Listening to console for messages...")
    while True:
        msg_to_send = await aioconsole.ainput()
        print(f"Sending '{msg_to_send}' to {websocket.remote_address}...")
        await websocket.send(msg_to_send)
        print("Message sent!")

async def main(host: str, port: int):
    async with connect(f"ws://{host}:{port}") as websocket:
        print(f"Connected to {host}:{port} on local port {websocket.local_address[1]}!")
        in_task = asyncio.create_task(input_listener(websocket))
        rec_task = asyncio.create_task(rec_handler(websocket))
        done, pending = await asyncio.wait(
            [
                in_task,
                rec_task,
            ],
            return_when=asyncio.FIRST_COMPLETED,
        )
        for task in pending:
            task.cancel()

if __name__ == "__main__":
    host = "localhost"
    port = 8080
    asyncio.run(main(host, port))