import pygame
import sys
import serial
import time
from multiprocessing import Process


"""import config
import utils
import mySerial
import robot"""
from gamepad import gamepadLoop



if __name__ == "__main__":

    processes = [
        Process(target=gamepadLoop, args=())
    ]

    for process in processes:
        process.start()
        print(process)
        time.sleep(0.5)

    print(f"Is it working?! \t \t \t :)")

