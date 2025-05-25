# -------- Serial Interface -------- 

import sys
import serial
import time

import utils
import config

print("Serial Interface: \t \t OK")


# Initialize Serial
def initSerial(SERIAL_PORT, BAUD_RATE, timeout, debug):
    initT0 = time.time()
    t0 = initT0

    while True:
        if debug == True: # Debugging Purposes, no serial, can be run off RPi
            return None

        t1 = t0 + 0.5

        try:
            ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
            print(f"Connected to {SERIAL_PORT} at {BAUD_RATE} baud.")
            time.sleep(2)
            
            return ser

        except serial.SerialException as e:
            print(f"Error opening serial port: {e}")
            
            if time.time() - initT0 >= timeout:
                utils.printDebug("EXITING - NO SERIAL PORT", config.DEBUG)
                sys.exit()

        while time.time() <= t1:
            time.sleep(0.1)

        t0 = t1


# Sends serials and allows for use with no serial port (DEBUG = True)
def sendSerial(message):
    if config.DEBUG == True:
        utils.printDebug(f"Fake Sent: {message}", config.DEBUG)
        return
    
    utils.printDebug(f"Sent to Serial: {message.strip()}", config.softDEBUG)
    ser.write(message.encode('utf-8'))


# Reads Serial port
def readSerial(debug):
    if debug == True:
        utils.printDebug(f"No Serial Port - Debug = True", config.DEBUG)
        time.sleep(0.5)
        return "Give Up"
    
    messageReceived = "-Nothing-"

    if ser.in_waiting <= 0:
        return messageReceived
    
    messageReceived = ""

    while True:
        c = ser.read()
        if c == 0 or c == 0x0A or c == 0x0D:
            break

        messageReceived = messageReceived + str(c.decode('utf-8'))

        if ser.in_waiting <= 0:
            time.sleep(0.001)
            if ser.in_waiting <= 0:
                break

    return messageReceived


ser = initSerial(config.SERIAL_PORT, config.BAUD_RATE, 10, config.DEBUG)