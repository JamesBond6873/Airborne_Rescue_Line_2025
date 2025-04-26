#import pygame
import sys
import serial
import time
from multiprocessing import Process
import multiprocessing as mp
import threading


from gamepad import gamepadLoop
from line_cam import lineCamLoop
from robot import controlLoop
#from zone_cam import zoneCamLoop

input_queue = mp.Queue()

def inputThread(queue):
    print(f"Input Thread started -- Inside Main.py")
    while True:
        line = sys.stdin.readline()
        if line:
            queue.put(line.strip())
            print(f"Input Thread: {line.strip()}")

 
if __name__ == "__main__":

    

    processes = [
        Process(target=gamepadLoop, args=()),
        Process(target=lineCamLoop, args=()),
        Process(target=controlLoop, args=())
        #Process(target=zoneCamLoop, args=())
    ]

    for process in processes:
        process.start()
        print(process)
        time.sleep(0.5)

    threading.Thread(target=inputThread, args=(input_queue,), daemon=True).start()

    try:
        for process in processes:
            process.join()

    except KeyboardInterrupt:
        print(f"KeyboardInterrupt detected. Terminating processes...")
        for process in processes:
            process.terminate()
            process.join()
        print(f"Processes terminated.")

    finally:
        print(f"")
        print(f"")
        print(f"-------- Main.py: All processes have finished. --------")
        print(f"------------------ Main.py: Exiting. ------------------")

