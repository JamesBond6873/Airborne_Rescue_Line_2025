#import pygame
import sys
import serial
import time
from multiprocessing import Process
import multiprocessing as mp
import threading

from utils import printDebug
from gamepad import gamepadLoop
from mySerial import serialLoop
from line_cam import lineCamLoop
from robot import controlLoop
from WebSocket_Server import websocket_process
from mp_manager import *


input_queue = mp.Queue()

def inputThread(queue):
    printDebug(f"Input Thread started -- Inside Main.py", True)
    while True:
        line = sys.stdin.readline()
        if line:
            queue.put(line.strip())
            #printDebug(f"Input Thread: {line.strip()}")
            CLIcommandToExecute.value = line.strip()

 
if __name__ == "__main__":
    processes = [
        Process(target=gamepadLoop, args=()),
        Process(target=serialLoop, args=()),
        Process(target=lineCamLoop, args=()),
        Process(target=controlLoop, args=()),
        Process(target=websocket_process, args=())
    ]

    for process in processes:
        process.start()
        printDebug(process, True)
        time.sleep(0.5)

    threading.Thread(target=inputThread, args=(input_queue,), daemon=True).start()

    try:
        for process in processes:
            process.join()

    except KeyboardInterrupt:
        printDebug(f"KeyboardInterrupt detected. Terminating processes...", True)
        for process in processes:
            process.terminate()
            process.join()
        printDebug(f"Processes terminated.", True)

    finally:
        printDebug(f"", True)
        printDebug(f"", True)
        printDebug(f"-------- Main.py: All processes have finished. --------", True)
        printDebug(f"------------------ Main.py: Exiting. ------------------", True)
        printDebug(f"", True)
