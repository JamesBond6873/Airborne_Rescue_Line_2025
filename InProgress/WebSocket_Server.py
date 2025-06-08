import asyncio
import websockets
import json
import time
from utils import *
from mp_manager import *

# Define global set to hold connections
connections = set()

async def handler(websocket):
    printConsoles("Client connected")
    connections.add(websocket)


    async def receive_commands():
        async for message in websocket:
            printConsoles(f"Command received: {message}")
            CLIWebSocketCommand.value = message  # Store the received command
            # Optionally: parse or act on the command here
            # Example:
            # if message == "stop":
            #     terminate.value = True

    async def send_status():
        while not terminate.value:
            payload = [
                f"{round(time.perf_counter(), 3)} s",
                "True" if terminate.value else "False",
                f"{round(time.perf_counter() - runStartTime.value, 0)} s",
                f"{objective.value}",
                f"",
                f"{bool(LOPstate.value)}",
                f"{bool(lopOverride.value)}",
                f"{'Perfect Run' if lopCounter.value == 0 else lopCounter.value}",
                f"{bool(motorOverride.value)}",
                f"",
                f"{m1MP.value}",
                f"{m2MP.value}",
                f"",
                f"",
                f"",
                f"{AccelXArrayDebug.value}",
                f"{AccelYArrayDebug.value}",
                f"{AccelZArrayDebug.value}",
                f"",
                f"",
                f"{GyroXArrayDebug.value}",
                f"{GyroXArrayDebug.value}",
                f"{GyroXArrayDebug.value}",
                f"",
                f"",
                f"{Tof1ArrayDebug.value}",
                f"{Tof1ArrayDebug.value}",
                f"{Tof1ArrayDebug.value}",
                f"{Tof1ArrayDebug.value}",
                f"{Tof1ArrayDebug.value}",
                f"-!-",
                f"",
                f"",
                f"",
                f"",
                f"",
                f"",
                f"",
                f"",
                f"",
                f"{'Not Started' if zoneStartTime.value == -1 else 'Finished' if zoneStatus.value == 'finished' else (round(time.perf_counter() - zoneStartTime.value, 0))}",
                f"{dumpedAliveCount.value} Victim(s)",
                f"{dumpedDeadCount.value} Victim(s)",
                f"{pickedUpAliveCount.value} Victim(s)",
                f"{pickedUpDeadCount.value} Victim(s)",
                f"{zoneStatus.value}",
                f"{zoneStatusLoopDebug.value}",
                f"{pickSequenceStatusDebug.value}",
                f"{pickingVictimDebug.value}",
                f"",
                f"",
            ]
            
            await websocket.send(json.dumps(payload))

            while consoleLines:
                line = consoleLines.pop(0)
                await websocket.send(json.dumps({ "type": "console", "content": line }))

            await asyncio.sleep(0.01)


    try:
        await asyncio.gather(receive_commands(), send_status())
    except websockets.exceptions.ConnectionClosed:
        print("Client disconnected")
    finally:
        connections.remove(websocket)

def websocket_process():
    async def monitor_termination(server):
        while not terminate.value:
            await asyncio.sleep(0.2)
        print("Shutting Down Web Socket Loop")
        server.close()
        await server.wait_closed()
        # Cancel all handlers if needed
        for ws in connections:
            await ws.close()

    async def main():
        server = await websockets.serve(handler, "0.0.0.0", 8000)
        await monitor_termination(server)

    asyncio.run(main())
