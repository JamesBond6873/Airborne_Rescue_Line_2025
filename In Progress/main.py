import sys
import serial
import time
from multiprocessing import Process, shared_memory

from gamepad import gamepad_loop
from line_cam import line_cam_loop
from control import control_loop


if __name__ == "__main__":
    processes = [
        #Process(target=gamepad_loop, args=()),
        Process(target=line_cam_loop, args=()),
        #Process(target=control_loop, args=())
    ]

    for process in processes:
        process.start()
        print(f"Started Process: {process}")
        time.sleep(0.5)
    
    print("What is going on?!")
    print("\n")