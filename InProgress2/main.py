#import pygame
import sys
import serial
import time
from multiprocessing import Process


from gamepad import gamepadLoop
from line_cam import lineCamLoop
from robot import controlLoop
#from zone_cam import zoneCamLoop


 
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
    for process in processes:
        process.join()

    print(f"Is it working?! \t \t \t :)")

