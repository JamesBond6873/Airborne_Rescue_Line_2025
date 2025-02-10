# -------- Robot Actuators/Sensors -------- 

import config
import utils
import mySerial


print("Robot Functions: \t \t OK")


# Loop Vars
notWaiting = True
waitingResponse = ""
commandWaitingList = []


# Interpret Received Message
def interpretMessage(message):
    global notWaiting, waitingResponse, commandWaitingList
    if "-Nothing-" not in message:
        print(f"Received Message: {message}")
    if "Ok" in message:
        print(f"Command List: {commandWaitingList}")
    if len(commandWaitingList) == 0:
        notWaiting = True
    else:
        mySerial.sendSerial(commandWaitingList[0])
        commandWaitingList.pop(0)


# Pick Victim Function (takes "Alive" or "Dead")
def pickVictim(type):
    global notWaiting
    notWaiting = False

    utils.printDebug(f"Pick {type}", config.softDEBUG)

    commandWaitingList.append(f"AD")
    commandWaitingList.append(f"P{type}")

    utils.printDebug(f"Command List: {commandWaitingList}", config.softDEBUG)

    mySerial.sendSerial(commandWaitingList[0]) # Test


# Drop Function (takes "Alive" or "Dead")
def ballRelease(type):
    global notWaiting
    notWaiting = False

    utils.printDebug(f"Drop {type}", config.softDEBUG)

    commandWaitingList.append(f"D{type}")
    commandWaitingList.append(f"SF,5,F")

    utils.printDebug(f"Command List: {commandWaitingList}", config.softDEBUG)

    mySerial.sendSerial(commandWaitingList[0]) # Test


# Closes Ball Storage
def closeBallStorage():
    global notWaiting
    notWaiting = False

    utils.printDebug(f"Close Ball Storage", config.softDEBUG)

    commandWaitingList.append(f"BC")
    commandWaitingList.append(f"SF,5,F")

    utils.printDebug(f"Command List: {commandWaitingList}", config.softDEBUG)

    mySerial.sendSerial(commandWaitingList[0]) # Test