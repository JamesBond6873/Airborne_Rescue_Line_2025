# -------- Serial Interface -------- 

import sys
import serial
import time

from utils import *
from config import *
from mp_manager import *

print("Serial Interface: \t \t OK")

waitingResponse = False # Flag to indicate if we are waiting for a response
waitingSensorData = False # Flag to indicate if we are waiting for sensor data
commandConfirmationAborted = False
commandWaitingListConfirmation = [] # List of commands to be sent to the RPi
lastUnsentCommandWithoutConfirmation = None # Last command that was not sent

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
        printDebug(f"F: Sent to Serial at {time.perf_counter()}: {message.strip()}", serialSoftDEBUG)
        return
    
    if timer_manager.is_timer_expired("serialCooldownbetweenCommands"):
        printDebug(f"Sent to Serial at {time.perf_counter()}: {message.strip()}", serialSoftDEBUG)
        timer_manager.set_timer("serialCooldownbetweenCommands", 0.005) # Wait 5ms before sending the next command
        message += "\n" # is this fixing the problem?
        ser.write(message.encode('utf-8'))

    else:
        if confirmation == True:
            printDebug(f" Did I catch a ball pick up? {message.strip()}", False)
            waitingResponse = False # We didn't send the command
            commandConfirmationAborted = True

# Interpret Received Message
def interpretMessage(message):
    global waitingResponse, waitingSensorData, commandWaitingListConfirmation
    if "-Nothing-" not in message:
        printDebug(f"Received Message at {time.perf_counter()}: {message.strip()}", serialSoftDEBUG)
    if "Ok" in message:
        commandWaitingListConfirmation.pop(0)
        printDebug(f"Command List ({len(commandWaitingListConfirmation)} commands): {commandWaitingListConfirmation}", False)
        waitingResponse = False
    elif "D," in message or "T5," in message:
        parseSensorData(message)
        waitingSensorData = False
    if DEBUG == True:
        commandWaitingListConfirmation.pop(0)
        printDebug(f"Command List ({len(commandWaitingListConfirmation)} commands): {commandWaitingListConfirmation}", False)
        waitingResponse = False


def updateCommandWaitingListConfirmation():
    global commandWaitingListConfirmation
    if commandWithConfirmation.value != "none":
        commandWaitingListConfirmation.append(commandWithConfirmation.value)
        commandWithConfirmation.value = "none"
        printDebug(f"Command Waiting List: {commandWaitingListConfirmation}", False)


def updateCommandWithoutConfirmation():
    global commandWithoutConfirmation, lastUnsentCommandWithoutConfirmation

    if commandWithoutConfirmation.value != "none":
        if not waitingResponse and not waitingSensorData:
            sendSerial(commandWithoutConfirmation.value)
            lastUnsentCommandWithoutConfirmation = None  # Clear, it was sent
        else:
            printDebug(f"Check Error Why the heck are we sending this command when waiting response? {commandWithoutConfirmation.value}", False)
            lastUnsentCommandWithoutConfirmation = commandWithoutConfirmation.value
        commandWithoutConfirmation.value = "none"

    # If nothing new came and one was missed before, try to send it
    elif lastUnsentCommandWithoutConfirmation and not waitingResponse and not waitingSensorData:
        print(f"Retrying last unsent command: {lastUnsentCommandWithoutConfirmation}")
        sendSerial(lastUnsentCommandWithoutConfirmation)
        lastUnsentCommandWithoutConfirmation = None


def getSensorData(data = "All"):
    if not waitingResponse and not waitingSensorData:
        if objective.value == "follow_line":
            printDebug(f"Requesting sensor data: {data}", serialSoftDEBUG)
            if data == "All":
                sendSerial(f"ITData")
            elif data == "IMU":
                sendSerial(f"IMU10")
            elif data == "TOF":
                sendSerial(f"ToF5")
        elif objective.value == "zone":
            sendSerial(f"ToF5")


def parseSensorData(data):
    try:
        # Stop at the first full line
        line = data.strip().split('\n')[0].strip()

        if line.startswith("D,"):
            parts = line[2:].split(",")  # Remove 'D,' and split

            if len(parts) != 15:
                printDebug(f"Unexpected number of values in D-message: {len(parts)} in line: {line}", True)
                return

            # Assign to manager variables
            Accel_X.value = float(parts[0])
            Accel_Y.value = float(parts[1])
            Accel_Z.value = float(parts[2])

            Gyro_X.value = float(parts[3])
            Gyro_Y.value = float(parts[4])
            Gyro_Z.value = float(parts[5])

            Mag_X.value = float(parts[6])
            Mag_Y.value = float(parts[7])
            Mag_Z.value = float(parts[8])

            Temp.value = float(parts[9])

            Tof_1.value = float(parts[10])
            Tof_2.value = float(parts[11])
            Tof_3.value = float(parts[12])
            Tof_4.value = float(parts[13])
            Tof_5.value = float(parts[14])

            newSensorData.value = True

        elif line.startswith("T5,"):
            parts = line[3:].split(",")  # Remove 'T5,' and split

            if len(parts) != 5:
                printDebug(f"Unexpected number of values in T5-message: {len(parts)} in line: {line}", True)
                return

            Tof_1.value = float(parts[0])
            Tof_2.value = float(parts[1])
            Tof_3.value = float(parts[2])
            Tof_4.value = float(parts[3])
            Tof_5.value = float(parts[4])

            newSensorData.value = True

        else:
            printDebug(f"Ignoring line (no 'D,' or 'T5,'): {line}", True)

    except Exception as e:
        printDebug(f"Error parsing sensor data: {e}", True)


#############################################################################
#                        Serial Communication Loop
#############################################################################


def serialLoop():
    global ser, waitingResponse, commandWaitingListConfirmation, commandConfirmationAborted
    
    # Initialize serial port
    ser = initSerial(SERIAL_PORT, BAUD_RATE, 10, DEBUG)
    
    timer_manager.add_timer("serialCooldownbetweenCommands", 0.05)
    timer_manager.add_timer("sensorRequest", 0.025)  # 25ms interval for sensor data
    time.sleep(0.05)

    t0 = time.perf_counter()
    while not terminate.value:
        t1 = t0 + serialDelayMS * 0.001


        if commandConfirmationAborted:
            commandConfirmationAborted = False # It will go back to True if needed
            sendSerial(commandWaitingListConfirmation[0], confirmation=True)
            printDebug(f"Correcting Command Confirmation Aborted: {commandWaitingListConfirmation[0]}", False)
            waitingResponse = True  # We are now waiting for a response


        receivedMessage = readSerial(DEBUG) # Read the serial port
        interpretMessage(receivedMessage) # Interpret the received message
        

        updateCommandWaitingListConfirmation()
        updateCommandWithoutConfirmation()
        commandWaitingListLength.value = len(commandWaitingListConfirmation)


        # Check if we have a command to send, and we're not already waiting for a response
        if not waitingResponse:
            if len(commandWaitingListConfirmation) > 0:
                sendSerial(commandWaitingListConfirmation[0], confirmation=True)
                waitingResponse = True  # We are now waiting for a response


        # Request sensor data if timer expired
        if timer_manager.is_timer_expired("sensorRequest"):
            getSensorData()
            timer_manager.set_timer("sensorRequest", dataRequestDelayMS * 0.001)
            if objective.value == "zone":
                timer_manager.set_timer("sensorRequest", 3 * dataRequestDelayMS * 0.001)


        while (time.perf_counter() <= t1):
            time.sleep(0.0005)
        
        t0 = t1
    
    sendSerial(f"M({DEFAULT_STOPPED_SPEED}, {DEFAULT_STOPPED_SPEED})")
    print(f"Shutting Down Serial Loop")
