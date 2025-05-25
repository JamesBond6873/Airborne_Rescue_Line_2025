import asyncio
import websockets
import json
import time
from mp_manager import *

# Define global set to hold connections
connections = set()

async def handler(websocket):
    print("Client connected")
    connections.add(websocket)
    try:
        while not terminate.value:
            payload = [
                f"{round(time.perf_counter(), 3)} s",
                "True" if terminate.value else "False",
                f"{objective.value}",
                f"{round(time.perf_counter() - runStartTime.value, 0)} s",
                f"{'Not Started' if zoneStartTime.value == -1 else 'Finished' if zoneStatus.value == 'finished' else (round(time.perf_counter() - zoneStartTime.value, 0))}",
                f"{bool(LOPstate.value)}",
                f"{bool(lopOverride.value)}",
                f"{'Perfect Run' if lopCounter.value == 0 else lopCounter.value}",
                f"{bool(motorOverride.value)}",
                f"",
                f"",
                f"{m1MP.value}",
                f"{m2MP.value}"
            ]
            await websocket.send(json.dumps(payload))
            await asyncio.sleep(0.1)
    except websockets.exceptions.ConnectionClosed:
        print("Client disconnected")
    finally:
        connections.remove(websocket)

def websocket_process():
    async def monitor_termination(server):
        while not terminate.value:
            await asyncio.sleep(0.2)
        print("Shutting down Web Socket Loop")
        server.close()
        await server.wait_closed()
        # Cancel all handlers if needed
        for ws in connections:
            await ws.close()

    async def main():
        server = await websockets.serve(handler, "0.0.0.0", 8000)
        await monitor_termination(server)

    asyncio.run(main())
