"""Client using the asyncio API."""

import asyncio
from websockets.asyncio.client import connect


async def hello():
    async with connect("ws://localhost:8080") as websocket:
        await websocket.send(["hey", "there"])
        message = await websocket.recv()
        print(f"CLIENT: {message}")


if __name__ == "__main__":
    asyncio.run(hello())