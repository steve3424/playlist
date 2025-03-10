import os
import asyncio
import aioconsole
from asyncio.queues import Queue
from websockets.asyncio.client import connect, ClientConnection
from websockets.exceptions import ConnectionClosed

work_queue = Queue()
print(id(work_queue))

async def work_processor(item: str):
    await asyncio.sleep(10.0)

async def send_handler(websocket: ClientConnection):
    while True:
        print(f"[send] ({os.getpid()}) waiting for work item...")
        message_to_send = await work_queue.get()
        print(f"[send] ({os.getpid()}) found work item '{message_to_send}'...")
        if message_to_send == "x":
            raise Exception("Closing...")
        print(f"[send] ({os.getpid()}) sending '{message_to_send}'...")
        await websocket.send(message_to_send)
        print(f"[send] ({os.getpid()}) sent '{message_to_send}'!")

async def rec_handler(websocket: ClientConnection):
    while True:
        print(f"[recv] ({os.getpid()}) waiting for server data...")
        incoming = await websocket.recv()
        print(f"[recv] ({os.getpid()}) found '{incoming}'")
        print(f"[recv] ({os.getpid()}) processing '{incoming}'")
        res = await work_processor(incoming)
        print(f"[recv] ({os.getpid()}) processed '{incoming}'!")

async def input_listener():
    while True:
        print(f"[input] ({os.getpid()}) waiting for console input...")
        i = await aioconsole.ainput()
        print(f"[input] ({os.getpid()}) found {i}")
        await work_queue.put(i)
        print(f"[input] ({os.getpid()}) put {i} on work queue")

async def main(host: str, port: int):
    async with connect(f"wss://{host}:{port}") as websocket:
        print(f"[client] ({os.getpid()}) Connected to {host}:{port}!")
        in_task = asyncio.create_task(input_listener())
        rec_task = asyncio.create_task(rec_handler(websocket))
        send_task = asyncio.create_task(send_handler(websocket))
        done, pending = await asyncio.wait(
            [
                in_task,
                send_task,
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