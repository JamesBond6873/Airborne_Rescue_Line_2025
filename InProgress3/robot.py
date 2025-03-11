# -------- Robot Actuators/Sensors -------- 
import time
from gpiozero import Button
import numpy as np

import config
from utils import *
from line_cam import camera_x
import mySerial
from mp_manager import *


print("Robot Functions: \t \t OK")

# Situation Vars:
objective = "Follow Line"
lastTurn = "Straight"
rotateTo = "left" # When it needs to do 180 it rotates to ...
inGap = False
lastLineDetected = True  # Assume robot starts detecting a line

# Loop Vars
notWaiting = True
gamepadLoopValue = True
waitingResponse = ""
commandWaitingList = []

# Pin Definitions
SWITCH_PIN = 14
switch = Button(SWITCH_PIN, pull_up=True)  # Uses internal pull-up

# Motor Vars
M1 = M2 = 1520 # Left - Right
oldM1 = oldM2 = M1
error = errorAcc = lastError = 0

timer_manager = TimerManager()

# Command Intrepreter
def intrepretCommand():
    command = commandToExecute.value
    if command == "none":
        return
    print(f"Command to Execute: {command}")
    if command == "Drop Alive": ballRelease("A")
    elif command == "Drop Dead": ballRelease("D")
    elif command == "Close Ball Storage": closeBallStorage()  
    elif command == "Pick Alive": pickVictim("A")
    elif command == "Pick Dead": pickVictim("D")
    elif command == "Camera Evacuation": cameraDefault("Evacuation")
    elif command == "Camera Line": cameraDefault("Line")

    commandToExecute.value = "none"


# Interpret Received Message
def interpretMessage(message):
    global notWaiting, waitingResponse, commandWaitingList
    if "-Nothing-" not in message:
        printDebug(f"Received Message: {message}", config.softDEBUG)
    if "Ok" in message:
        printDebug(f"Command List: {commandWaitingList}", config.softDEBUG)
        if len(commandWaitingList) == 0:
            notWaiting = True
        else:
            mySerial.sendSerial(commandWaitingList[0])
            commandWaitingList.pop(0)


# Send Commands from Waiting List
def sendCommandList(commandList):
    global notWaiting, waitingResponse, commandWaitingList
    notWaiting = False

    for command in commandList:
        commandWaitingList.append(command)

    printDebug(f"Command List: {commandWaitingList}", config.softDEBUG)

    # Do first Cycle
    mySerial.sendSerial(commandWaitingList[0])
    commandWaitingList.pop(0)


# Pick Victim Function (takes "Alive" or "Dead")
def pickVictim(type):
    printDebug(f"Pick {type}", config.softDEBUG)
    
    sendCommandList([f"AD", f"P{type}", "SF,0,F", "SF,1,F", "SF,2,F", "SF,3,F"])


# Drop Function (takes "Alive" or "Dead")
def ballRelease(type):
    printDebug(f"Drop {type}", config.softDEBUG)

    sendCommandList([f"D{type}", f"SF,5,F"])


# Closes Ball Storage
def closeBallStorage():
    printDebug(f"Close Ball Storage", config.softDEBUG)

    sendCommandList([f"BC", f"SF,5,F"])


# Moves Camera to Default Position: Line or Evacuation
def cameraDefault(position):
    if position == "Line":
        printDebug(f"Set Camera to Line Following Mode", config.softDEBUG)
        sendCommandList(["CL", "SF,4,F"])

    elif position == "Evacuation":
        printDebug(f"Set Camera to Evacaution Zone Mode", config.softDEBUG)
        sendCommandList(["CE", "SF,4,F"])


#Returns True if the switch is ON, False otherwise.
def is_switch_on(): 
    return switch.is_pressed


# Controller for LoP
def LoPSwitchController():
    global switchState, rotateTo

    if is_switch_on():
        if switchState == False:
            switchState = True
            printDebug(f"LoP Switch is now ON: {switchState}", config.softDEBUG)
    else:
        if switchState == True:
            switchState = False
            printDebug(f"LoP Switch is now OFF: {switchState}", config.softDEBUG)
            rotateTo = "right" if rotateTo == "left" else "left" # Toggles rotate To
    

# Calculate motor Speed difference from default
def PID(lineCenterX):
    global error, errorAcc, lastError
    error = lineCenterX - 1280 / 2 # Camera view is 1280 pixels
    errorAcc = errorAcc + error

    motorSpeed = config.KP * error + config.KD * (error - lastError) + config.KI * errorAcc

    lastError = error

    return motorSpeed

def PID2(lineCenterX, lineAngle):
    global error_x, errorAcc, lastError, error_theta
    
    # Errors
    error_x = lineCenterX - camera_x / 2  # Camera view is 1280 pixels
    error_theta = lineAngle - (np.pi/2)  # Angle difference from vertical (pi/2)
    
    # Accumulate error for integral term
    errorAcc += error_x

    # Compute motor speed adjustment (mixing both errors)
    motorSpeed = (config.KP * error_x + 
                  config.KD * (error_x - lastError) + 
                  config.KI * errorAcc + 
                  config.KP_THETA * error_theta)  # New term for angle correction

    lastError = error_x  # Only update last error for x

    return motorSpeed


# Calculate motor Speed
def calculateMotorSpeeds(motorSpeed):
    global M1, M2
    m1Speed = config.DEFAULT_FORWARD_SPEED + motorSpeed
    m2Speed = config.DEFAULT_FORWARD_SPEED - motorSpeed

    # Ensure values are within ESC_MIN and ESC_MAX
    m1Speed = max(config.MIN_GENERAL_SPEED, min(config.MAX_DEFAULT_SPEED, m1Speed))
    m2Speed = max(config.MIN_GENERAL_SPEED, min(config.MAX_DEFAULT_SPEED, m2Speed))

    # Adjust for dead zone (avoid 1450-1550)
    if 1450 <= m1Speed <= 1550:
        m1Speed = config.DEFAULT_STOPPED_SPEED + config.ESC_DEADZONE if m1Speed > config.DEFAULT_STOPPED_SPEED else config.DEFAULT_STOPPED_SPEED - config.ESC_DEADZONE
    if 1450 <= m2Speed <= 1550:
        m2Speed = config.DEFAULT_STOPPED_SPEED + config.ESC_DEADZONE if m2Speed > config.DEFAULT_STOPPED_SPEED else config.DEFAULT_STOPPED_SPEED - config.ESC_DEADZONE
    
    #printDebug(f"Line Center: {lineCenterX.value}, Angle: {round(np.rad2deg(lineAngle.value), 0)} motorSpeed: {motorSpeed}, M1: {m1Speed}, M2: {m2Speed}", config.softDEBUG)

    return m1Speed, m2Speed


# Update Motor Vars accordingly
def setMotorsSpeeds():
    global M1, M2, M1info, M2info, switchState, motorSpeedDiference, commandWaitingList
    
    #motorSpeedDiference = PID(lineCenterX.value)
    motorSpeedDiference = PID2(lineCenterX.value, lineAngle.value)
    M1, M2 = calculateMotorSpeeds(motorSpeedDiference)

    if redDetected.value:
        M1, M2 = 1520, 1520

    if inGap: # Currently in gap
        M1, M2 = config.DEFAULT_FORWARD_SPEED, config.DEFAULT_FORWARD_SPEED

    elif not timer_manager.is_timer_expired("uTurn"): # if in uTurn (timer not expired)
        if rotateTo == "left":
            M1, M2 = 1000, 2000
        elif rotateTo == "right":
            M1, M2 = 2000, 1000
    
    elif not timer_manager.is_timer_expired('backwards'):
        M1, M2 = 1000, 1000

    elif timer_manager.get_remaining_time('uTurn') < 0 and timer_manager.get_remaining_time('uTurn') > -0.2:
        # Left uTurn Routine a few moments prior
        timer_manager.set_timer('backwards', 1.0)

    #print(f"Remaining Time: {timer_manager.get_remaining_time('uTurn')}")

    M1info, M2info = M1, M2

    #if True:
    if switchState: #LoP On - GamepadControl
        M1 = gamepadM1.value
        M2 = gamepadM2.value
 
       
# Control Motors
def controlMotors():
    global oldM1, oldM2
    if M1 != oldM1 or M2 != oldM2:
        message = f"M({int(M1)}, {int(M2)})"
        mySerial.sendSerial(message)


def intersectionController():
    global lastTurn
    if turnDirection.value != lastTurn:
        printDebug(f"New Turn direction {turnDirection.value} {lastTurn}", config.DEBUG)
        
        if turnDirection.value == "uTurn":
            if timer_manager.is_timer_expired("uTurn"):
                timer_manager.set_timer("uTurn", 1.5) # Give 1.5 s for 180degree turn

        lastTurn = turnDirection.value


def gapController():
    global inGap, lastLineDetected

    if not lineDetected.value: # No line detected
        if lastLineDetected: # Just lost the line (last state was true)
            timer_manager.set_timer("noLine", 0.35) # Start a timer
        elif timer_manager.is_timer_expired("noLine"): # Timer expired
            inGap = True # Confirm gap

    else:  # Line detected
        inGap = False  # Here to reset flag
        timer_manager.set_timer("noLine", 0)  # Force timer expiration

    lastLineDetected = lineDetected.value  # Update previous state


#############################################################################
#                           Robot Control Loop
#############################################################################

def controlLoop():
    global switchState, M1, M2, M1info, M2info, oldM1, oldM2, motorSpeedDiference, error_theta, error_x, errorAcc, lastError, inGap

    switchState = is_switch_on()
    motorSpeedDiference = 0
    M1info = 0
    M2info = 0
    error_theta = 0
    error_x = 0
    lastError = 0
    errorAcc = 0
    sendCommandList(["GR","BC", "SF,5,F", "CL", "SF,4,F"])

    # Timers
    timer_manager.add_timer("uTurn", 0.05)
    timer_manager.add_timer("backwards", 0.05)
    timer_manager.add_timer("noLine", 0.05)
    time.sleep(0.1)

    t0 = time.perf_counter()
    while not terminate.value:
        t1 = t0 + config.controlDelayMS * 0.001

        # Loop
        LoPSwitchController()
        gapController()

        printDebug(f"Robot Not Waiting: {notWaiting}", config.DEBUG)
        if notWaiting:
            setMotorsSpeeds()
            intersectionController()
            controlMotors()

        intrepretCommand()
        receivedMessage = mySerial.readSerial(config.DEBUG)
        interpretMessage(receivedMessage)


        oldM1 = M1
        oldM2 = M2


        debugMessage = (
            f"Center: {lineCenterX.value} \t"
            f"Angle: {round(np.rad2deg(lineAngle.value),2)} \t"
            f"LineBias: {int(config.KP * error_x + config.KD * (error_x - lastError) + config.KI * errorAcc)}   \t"
            f"AngBias: {round(config.KP_THETA*error_theta,2)}     \t"
            f"Reason: {turnReason.value} \t"
            #f"isCrop: {isCropped.value} \t"
            f"line: {lineDetected.value} \t"
            f"inGap: {inGap}"
            f"Turn: {turnDirection.value}     \t"
            f"Motor D: {round(motorSpeedDiference, 2)}   \t"
            f"M1: {int(M1info)} \t"
            f"M2: {int(M2info)} \t"
            f"LOP: {switchState} \t"
            #f"Commands: {commandWaitingList}"
        )
        printDebug(f"{debugMessage}", config.softDEBUG)


        while (time.perf_counter() <= t1):
            time.sleep(0.0005)
        t0 = t1