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
from Line_Cam import lineCamLoop
from robot import controlLoop


 
if __name__ == "__main__":

    processes = [
        Process(target=gamepadLoop, args=()),
        Process(target=lineCamLoop, args=()),
        Process(target=controlLoop, args=())
    ]

    for process in processes:
        process.start()
        print(process)
        time.sleep(0.5)
    for process in processes:
        process.join()

    print(f"Is it working?! \t \t \t :)")

