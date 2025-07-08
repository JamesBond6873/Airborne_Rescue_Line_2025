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
commandConfirmationAborted = False # Flag to indicate if we aborted sending a command with confirmation
commandSensorDataAborted = False # Flag to indicate if we aborted sending a sensor data request
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
def sendSerial(message, confirmation = False, dataRequest = False):
    global waitingResponse, commandConfirmationAborted, waitingSensorData, commandSensorDataAborted
    if DEBUG == True:
        printDebug(f"F: Sent to Serial at {time.perf_counter()}: {message.strip()}", serialSoftDEBUG)
        return
    
    if timer_manager.is_timer_expired("serialCooldownbetweenCommands"):
        printDebug(f"Sent to Serial at {time.perf_counter()}: {message.strip()}", serialSoftDEBUG)
        timer_manager.set_timer("serialCooldownbetweenCommands", 0.001) # Wait 1ms before sending the next command
        message += "\n" # is this fixing the problem?
        ser.write(message.encode('utf-8'))

    else:
        if confirmation == True:
            printDebug(f" Did I catch a ball pick up? {message.strip()}", False)
            waitingResponse = False # We didn't send the command
            commandConfirmationAborted = True
            return
        elif dataRequest:
            printDebug(f"Did Not Send data request because of serial cooldown: {message.strip()}", serialSoftDEBUG)
            waitingSensorData = False # We didn't send the sensor data request command
            commandSensorDataAborted = True # Perhaps try again
            return
        
        printDebug(f"Did Not Send because of serial cooldown: {message.strip()}", serialSoftDEBUG)

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
        printDebug(f"Sensor Data 2: {message.strip()} | at {time.perf_counter()}", False)
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
    global lastUnsentCommandWithoutConfirmation

    if commandWithoutConfirmation.value != "none":
        if not waitingResponse and not waitingSensorData:
            sendSerial(commandWithoutConfirmation.value)
            lastUnsentCommandWithoutConfirmation = None  # Clear, it was sent
        else:
            printDebug(f"Check Error Why the heck are we sending this command when waiting response? {commandWithoutConfirmation.value}. Confirmation: {waitingResponse} Sensor Data: {waitingSensorData}", serialSoftDEBUG)
            lastUnsentCommandWithoutConfirmation = commandWithoutConfirmation.value
        commandWithoutConfirmation.value = "none"

    # If nothing new came and one was missed before, try to send it
    elif lastUnsentCommandWithoutConfirmation and not waitingResponse and not waitingSensorData:
        printDebug(f"Retrying last unsent no confirmation command: {lastUnsentCommandWithoutConfirmation}", serialSoftDEBUG)
        sendSerial(lastUnsentCommandWithoutConfirmation)
        lastUnsentCommandWithoutConfirmation = None


def getSensorData(data = "All"):
    global waitingSensorData
    if not waitingResponse and not waitingSensorData:
        if objective.value == "follow_line":
            printDebug(f"Requesting sensor data: {data}", DEBUG)
            if data == "All":
                waitingSensorData = True
                sendSerial(f"ITData", dataRequest=True)
                timer_manager.set_timer("sensorTimeout", 0.05)
            elif data == "IMU":
                waitingSensorData = True
                sendSerial(f"IMU10", dataRequest=True)
                timer_manager.set_timer("sensorTimeout", 0.05)
            elif data == "TOF":
                waitingSensorData = True
                sendSerial(f"ToF5", dataRequest=True)
                timer_manager.set_timer("sensorTimeout", 0.05)
        elif objective.value == "zone" and zoneStatus.value in ["begin", "entry", "exit"]:
            waitingSensorData = True
            sendSerial(f"ToF5", dataRequest=True)
            timer_manager.set_timer("sensorTimeout", 0.05)


def parseSensorData(data):
    global waitingSensorData
    try:
        # Split data into lines and look for the first valid one
        for line in data.strip().split('\n'):
            line = line.strip()

            if line.startswith("D,"):
                parts = line[2:].split(",")  # Remove 'D,' and split

                if len(parts) != 15:
                    printDebug(f"Unexpected number of values in D-message: {len(parts)} in line: {line}", True)
                    return

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
                return  # Done parsing

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
                return  # Done parsing

        # If we get here, no valid line was found
        printDebug(f"Ignoring data (no 'D,' or 'T5,'): {data}", True)

    except Exception as e:
        printDebug(f"Error parsing sensor data: {e}", True)
        waitingSensorData = False  # Just safety, shouldn't happen


#############################################################################
#                        Serial Communication Loop
#############################################################################


def serialLoop():
    global ser, waitingResponse, waitingSensorData, commandWaitingListConfirmation, commandConfirmationAborted, commandSensorDataAborted
    
    # Initialize serial port
    ser = initSerial(SERIAL_PORT, BAUD_RATE, 10, DEBUG)
    
    timer_manager.add_timer("serialCooldownbetweenCommands", 0.05)
    timer_manager.add_timer("sensorRequest", 0.025)
    timer_manager.add_timer("sensorTimeout", 0.05)
    time.sleep(0.05)

    t0 = time.perf_counter()
    while not terminate.value:
        t1 = t0 + serialDelayMS * 0.001
        t0Real = time.perf_counter()

        receivedMessage = readSerial(DEBUG) # Read the serial port
        interpretMessage(receivedMessage) # Interpret the received message


        # Deal with aborted commands with confirmation
        if commandConfirmationAborted:
            commandConfirmationAborted = False # It will go back to True if needed
            sendSerial(commandWaitingListConfirmation[0], confirmation=True)
            printDebug(f"Correcting Command Confirmation Aborted: {commandWaitingListConfirmation[0]}", False)
            waitingResponse = True  # We are now waiting for a response
        

        # Update command waiting lists
        updateCommandWaitingListConfirmation()
        updateCommandWithoutConfirmation()
        commandWaitingListLength.value = len(commandWaitingListConfirmation)


        # Check if we have a command to send, and we're not already waiting for a response
        if not waitingResponse:
            if len(commandWaitingListConfirmation) > 0:
                sendSerial(commandWaitingListConfirmation[0], confirmation=True)
                waitingResponse = True  # We are now waiting for a response


        # Request sensor data if timer expired
        if timer_manager.is_timer_expired("sensorRequest") or commandSensorDataAborted:
            commandSensorDataAborted = False
            getSensorData()
            timer_manager.set_timer("sensorRequest", dataRequestDelayMS * 0.001)
            if objective.value == "zone":
                timer_manager.set_timer("sensorRequest", 2 * dataRequestDelayMS * 0.001)
        """if waitingSensorData and timer_manager.is_timer_expired("sensorTimeout"):
            printDebug(f"Sensor data timeout at {time.perf_counter()}. Resetting waitingSensorData.", True)
            waitingSensorData = False """


        while (time.perf_counter() <= t1):
            time.sleep(0.0005)

        elapsed_time = time.perf_counter() - t0Real
        if serialDelayMS * 0.001 - elapsed_time > 0:
            time.sleep(serialDelayMS * 0.001 - elapsed_time)
        
        printDebug(f"Serial Loop: {waitingResponse} | {len(commandWaitingListConfirmation)} | {commandWaitingListConfirmation} | {commandWithoutConfirmation.value} | sensor data: {waitingSensorData}", DEBUG)
        serialAliveIndicator.value = 0 if serialAliveIndicator.value == 1 else 1
        waitingResponseDebug.value = waitingResponse
        waitingSensorDataDebug.value = waitingSensorData

        # === Frequency Measurement ===
        loop_duration = time.perf_counter() - t0Real
        if loop_duration > 0:
            serialLoopFrequency.value = 1.0 / loop_duration
        else:
            serialLoopFrequency.value = 0  # Avoid division by zero

        printDebug(f"Serial Frequency: {serialLoopFrequency.value} Hz", DEBUG)

        
        t0 = t1

    sendSerial(f"M({DEFAULT_STOPPED_SPEED}, {DEFAULT_STOPPED_SPEED})")
    time.sleep(0.1)
    sendSerial(f"L0")
    print(f"Shutting Down Serial Loop")
