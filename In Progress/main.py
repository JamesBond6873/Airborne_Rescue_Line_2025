import sys
import serial
import time
from multiprocessing import Process

from gamepad import gamepad_loop


# Motor variables
M1, M2, M3, M4 = 0, 0, 0, 0


if __name__ == "__main__":
    processes = [
        Process(target=gamepad_loop, args=())
    ]

    for process in processes:
        process.start()
        print(f"Started Process: {process}")
        time.sleep(0.5)
    
    print("What is going on?!")
    print("\n")