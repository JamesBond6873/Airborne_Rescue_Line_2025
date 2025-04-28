# -------- Serial Interface -------- 

import sys
import serial
import time

from utils import *
from config import *
from mp_manager import *

print("Serial Interface: \t \t OK")

waitingResponse = False # Flag to indicate if we are waiting for a response
commandConfirmationAborted = False
commandWaitingListConfirmation = [] # List of commands to be sent to the RPi

timer_manager = TimerManager()


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
                printDebug("EXITING - NO SERIAL PORT", DEBUG)
                sys.exit()

        while time.time() <= t1:
            time.sleep(0.1)

        t0 = t1


# Reads the Serial port
def readSerial(debug):
    if debug == True:
        printDebug(f"No Serial Port - Debug = True", DEBUG)
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


# Sends serials and allows for use with no serial port (DEBUG = True)
def sendSerial(message, confirmation = False):
    global waitingResponse, commandConfirmationAborted
    if DEBUG == True:
        printDebug(f"Fake Sent: {message}", DEBUG)
        return
    
    if timer_manager.is_timer_expired("serialCooldownbetweenCommands"):
        printDebug(f"Sent to Serial at {time.perf_counter()}: {message.strip()}", softDEBUG)
        timer_manager.set_timer("serialCooldownbetweenCommands", 0.010) # Wait 10ms before sending the next command
        ser.write(message.encode('utf-8'))

    else:
        if confirmation == True:
            print(f" Did I catch a ball pick up? {message.strip()}")
            waitingResponse = False # We didn't send the command
            commandConfirmationAborted = True

# Interpret Received Message
def interpretMessage(message):
    global waitingResponse, commandWaitingListConfirmation
    if "-Nothing-" not in message:
        printDebug(f"Received Message: {message}", softDEBUG)
    if "Ok" in message:
        commandWaitingListConfirmation.pop(0)
        printDebug(f"Command List: {commandWaitingListConfirmation}", softDEBUG)
        waitingResponse = False
        

def updateCommandWaitingListConfirmation():
    global commandWaitingListConfirmation
    if commandWithConfirmation.value != "none":
        commandWaitingListConfirmation.append(commandWithConfirmation.value)
        commandWithConfirmation.value = "none"
        printDebug(f"Command Waiting List: {commandWaitingListConfirmation}", softDEBUG)


def updateCommandWithoutConfirmation():
    global commandWithoutConfirmation
    if commandWithoutConfirmation.value != "none":
        if not waitingResponse:
            sendSerial(commandWithoutConfirmation.value)
        else:
            print(f"Check Error Why the heck are we sending this command when waiting response? {commandWithoutConfirmation.value}")
        commandWithoutConfirmation.value = "none"

#############################################################################
#                        Serial Communication Loop
#############################################################################


def serialLoop():
    global ser, waitingResponse, commandWaitingListConfirmation, commandConfirmationAborted
    
    # Initialize serial port
    ser = initSerial(SERIAL_PORT, BAUD_RATE, 10, DEBUG)
    
    timer_manager.add_timer("serialCooldownbetweenCommands", 0.05)
    time.sleep(0.05)

    t0 = time.perf_counter()
    while not terminate.value:
        t1 = t0 + serialDelayMS * 0.001


        if commandConfirmationAborted:
            commandConfirmationAborted = False # It will go back to True if needed
            sendSerial(commandWaitingListConfirmation[0], confirmation=True)
            print(f"Correcting Command Confirmation Aborted: {commandWaitingListConfirmation[0]}")
            waitingResponse = True  # We are now waiting for a response


        receivedMessage = readSerial(DEBUG) # Read the serial port
        interpretMessage(receivedMessage) # Interpret the received message
        

        updateCommandWaitingListConfirmation()
        updateCommandWithoutConfirmation()


        # Check if we have a command to send, and we're not already waiting for a response
        if not waitingResponse:
            if len(commandWaitingListConfirmation) > 0:
                sendSerial(commandWaitingListConfirmation[0], confirmation=True)
                waitingResponse = True  # We are now waiting for a response


        while (time.perf_counter() <= t1):
            time.sleep(0.0005)
        
        t0 = t1
    
    sendSerial(f"M({DEFAULT_STOPPED_SPEED}, {DEFAULT_STOPPED_SPEED})")
    print(f"Shutting Down Serial Loop")
