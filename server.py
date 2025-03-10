import asyncio
# from asyncio.queues import Queue
from websockets.asyncio.server import serve, ServerConnection
from websockets.exceptions import ConnectionClosedOK, ConnectionClosedError

CONNECTIONS = set()

async def recv_handler(websocket: ServerConnection):
    async for message in websocket:
        if message.startswith("WORK"):
            # Process item
            print(f"[{websocket.remote_address}] Broadcasting '{message}' to {len(CONNECTIONS)} clients!")
            for client in CONNECTIONS:
                asyncio.create_task(send_handler(client, message))

            # if client_needs_specific_response_to_message:
            #   await websocket.send()
        else:
            print(f"[{websocket.remote_address}] Invalid work item {message}")

async def send_handler(websocket: ServerConnection, message: str):
    try:
        await websocket.send(message)
        print(f"[{websocket.remote_address}] Sent {message}!")
    except ConnectionClosedError as ex:
        print(f"[{websocket.remote_address}] Connection closed with error: {ex}")
    except ConnectionClosedOK:
        print(f"[{websocket.remote_address}] Client closed connection.")

async def connection_handler(websocket: ServerConnection):
    """
    Called when a new connection is made to server.

    Parameters
    ----------
    websocket
        Handle to client-specific connection.
    """
    print(f"Connection made from {websocket.remote_address}!")
    CONNECTIONS.add(websocket)
    try:
        await recv_handler(websocket)
    finally:
        print(f"[{websocket.remote_address}] Client closed connection.")
        CONNECTIONS.remove(websocket)

async def main(host: str, port: int):
    async with serve(connection_handler, host, port, ping_interval=10) as server:
        print(f"listening on {host}:{port}")
        await server.serve_forever()

if __name__ == "__main__":
    host = "localhost"
    port = 8080
    asyncio.run(main(host, port))