# -------- Robot Actuators/Sensors -------- 
import time
from gpiozero import Button

import config
from utils import *
import mySerial
from MP_Manager import *


print("Robot Functions: \t \t OK")

# Situation Vars:
objective = "Follow Line"

# Loop Vars
notWaiting = True
gamepadLoopValue = True
waitingResponse = ""
commandWaitingList = []

# Pin Definitions
SWITCH_PIN = 14

# Initialize components
switch = Button(SWITCH_PIN, pull_up=True)  # Uses internal pull-up

# Motor Vars
M1 = M2 = 1520 # Left - Right
oldM1 = oldM2 = M1


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
    global switchState

    if is_switch_on():
        if switchState == False:
            switchState = True
            printDebug(f"LoP Switch is now ON: {switchState}", config.softDEBUG)
    else:
        if switchState == True:
            switchState = False
            printDebug(f"LoP Switch is now OFF: {switchState}", config.softDEBUG)
    

# Update Motor Vars accordingly
def setMotorsVars():
    global M1, M2, switchState
    if switchState: #LoP On - GamepadControl
        M1 = gamepadM1.value
        M2 = gamepadM2.value
    else: #LoP Off, auto control
        pass


# Control Motors
def controlMotors():
    global oldM1, oldM2
    if M1 != oldM1 or M2 != oldM2:
        message = f"M({M1}, {M2})"
        mySerial.sendSerial(message)

#############################################################################
#                           Robot Control Loop
#############################################################################

def controlLoop():
    global switchState, M1, M2, oldM1, oldM2

    switchState = is_switch_on()
    sendCommandList(["GR","BC", "SF,5,F", "CL", "SF,4,F"])

    t0 = time.time()
    while not terminate.value:
        t1 = t0 + config.controlDelayMS * 0.001

        # Loop
        LoPSwitchController()

        printDebug(f"Robot Not Waiting: {notWaiting}", config.DEBUG)
        if notWaiting:
            setMotorsVars()
            controlMotors()

        intrepretCommand()
        receivedMessage = mySerial.readSerial(config.DEBUG)
        interpretMessage(receivedMessage)

        oldM1 = M1
        oldM2 = M2


        while (time.time() <= t1):
            time.sleep(0.001)
        t0 = t1