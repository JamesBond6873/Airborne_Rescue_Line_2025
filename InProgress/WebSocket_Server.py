import asyncio
import websockets
import json
import time
# static_server.py
import http.server
import socketserver
import threading
import os

from utils import *
from mp_manager import *
from config import *


PORT = 8081
DIRECTORY = "/home/raspberrypi/Airborne_Rescue_Line_2025/Latest_Frames"

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
                f"",
                f"",
                f"",
                f"",
                f"{avoidingStuckDebug.value}",
                f"{bool(LOPstate.value)}",
                f"{bool(lopOverride.value)}",
                f"{'Perfect Run' if lopCounter.value == 0 else lopCounter.value}",
                f"{bool(motorOverride.value)}",
                f"{imageSimilarityAverage.value}",
                f"{m1MP.value}",
                f"{m2MP.value}",
                f"{round(motorSpeedDiferenceDebug.value,2)}",
                f"{round(pitchDebug.value,2)}",
                f"{stuckDetected.value}",
                f"{round(AccelXArrayDebug.value,2)}",
                f"{round(AccelYArrayDebug.value,2)}",
                f"{round(AccelZArrayDebug.value,2)}",
                f"{rampDetected.value}",
                f"{wasOnRamp.value}",
                f"{round(GyroXArrayDebug.value,2)}",
                f"{round(GyroXArrayDebug.value,2)}",
                f"{round(GyroXArrayDebug.value,2)}",
                f"{rampUp.value}",
                f"{rampDown.value}",
                f"{round(Tof1ArrayDebug.value,1)}",
                f"{round(Tof2ArrayDebug.value,1)}",
                f"{round(Tof3ArrayDebug.value,1)}",
                f"{round(Tof4ArrayDebug.value,1)}",
                f"{round(Tof5ArrayDebug.value,1)}",
                f"",
                f"",
                f"",
                f"",
                f"",
                f"{lineCenterX.value}",
                f"{round(np.rad2deg(lineAngle.value),2)}",
                f"{lineAngleNormalizedDebug.value}",
                f"{lineStatus.value}",
                f"{turnReason.value}",
                f"{lineBiasDebug.value}",
                f"{AngBiasDebug.value}",
                f"{round(KP_THETA *(- (np.deg2rad(lineAngleNormalizedDebug.value) - np.pi / 2)),2)}",
                f"{markerToHighDebug.value}",
                f"{lineCropPercentage.value}",
                f"{isCropped.value}",
                f"{lineDetected.value}",
                f"{inGapDebug.value}",
                f"{redDetected.value}",
                f"{turnDirection.value}",
                f"{round(gapAngle.value, 2)}",
                f"{round(gapCenterX.value, 2)}",
                f"{round(gapCenterY.value, 2)}",
                f"{gapCorrectionState.value}",
                f"{'Forward' if lastCorrectionDirection.value else 'Backward'}",
                f"{round(silverValueDebug.value,3)}",
                f"{round(silverValueArrayDebug.value,3)}",
                f"{silverLineDetected.value}",
                f"{gapCorrectionActive.value}",
                f"",
                f"{round(silverAngle.value, 2)}",
                f"{round(silverCenterX.value, 2)}",
                f"{round(silverCenterY.value, 2)}",
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
    class Handler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=DIRECTORY, **kwargs)

    def start_static_server():
        with socketserver.TCPServer(("", PORT), Handler) as httpd:
            print(f"Serving static images at http://0.0.0.0:{PORT}")
            httpd.serve_forever()

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

    # Start static file server in a separate thread
    #threading.Thread(target=start_static_server, daemon=True).start()

    asyncio.run(main())

