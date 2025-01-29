import pygame
import sys
import serial
import time

# Is it DEBUG?
DEBUG = False

SERIAL_PORT = '/dev/ttyACM0'
BAUD_RATE = 115200

# Constants for speed factors and motor default values
delayTimeMS = 100
MAX_DEFAULT_SPEED = 2000
MIN_DEFAULT_SPEED = 1800
SPEED_STEP = 25
FACTOR_STEP = 25
MAX_SPEED_FACTOR_LIMIT = 200
MIN_SPEED_FACTOR_LIMIT = 50

# Variables that can be updated
maxSpeedFactor = 100
reverseSpeedFactor = -100
defaultSpeed = 1800

# Motor variables
M1, M2, M3, M4 = 0, 0, 0, 0
speedFactor = 0

# Makes printDebug dependent on DEBUG flag
def printDebug(text):
    if DEBUG:
        print(text)


def initSerial():
    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
        print(f"Connected to {SERIAL_PORT} at {BAUD_RATE} baud.")
        time.sleep(2)
        
        return ser
    except serial.SerialException as e:
        print(f"Eror opening serial port: {e}")
        sys.exit()


# Main loop for handling joystick input and updating motor speeds
def mainLoop(ser):
    try:
        while True:

            # Print motor speeds for debugging
            print(f"M({M1}, {M2})")
            message = f"M(2000, 2000)"
            ser.write(message.encode('utf-8'))
            
            print(f"Sent to Serial: {message.strip()}")
            #print(f"M1: {M1}, M2: {M2}, M3: {M3}, M4: {M4}")
            
            time.sleep(0.2)

    except KeyboardInterrupt:
        sys.exit()

if __name__ == "__main__":
    ser = initSerial()
    mainLoop(ser)

