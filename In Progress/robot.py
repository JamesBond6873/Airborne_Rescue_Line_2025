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
    utils.printDebug("---------------Here1", config.softDEBUG)
    global notWaiting, waitingResponse, commandWaitingList
    if "-Nothing-" not in message:
        print(f"Received Message: {message}")
    if "Ok" in message:
        utils.printDebug(f"Command List1: {commandWaitingList}", config.softDEBUG)
        commandWaitingList.pop(0)
        utils.printDebug(f"Command List2: {commandWaitingList}", config.softDEBUG)
        mySerial.sendSerial(commandWaitingList[0])
        
    if len(commandWaitingList) == 0:
        notWaiting = True
    else:
        pass
        #print(f"Command List: {commandWaitingList}")
        
        

# Send Commands from Waiting List
def sendCommandList(commandList):
    global notWaiting, waitingResponse, commandWaitingList
    notWaiting = False

    for command in commandList:
        commandWaitingList.append(command)

    utils.printDebug(f"Command List: {commandWaitingList}", config.softDEBUG)

    mySerial.sendSerial(commandWaitingList[0]) # Test


# Pick Victim Function (takes "Alive" or "Dead")
def pickVictim(type):
    utils.printDebug(f"Pick {type}", config.softDEBUG)
    
    sendCommandList([f"AD", f"P{type}", "SF,0,F", "SF,1,F", "SF,2,F", "SF,3,F"])


# Drop Function (takes "Alive" or "Dead")
def ballRelease(type):
    utils.printDebug(f"Drop {type}", config.softDEBUG)

    sendCommandList([f"D{type}", f"SF,5,F"])


# Closes Ball Storage
def closeBallStorage():
    utils.printDebug(f"Close Ball Storage", config.softDEBUG)

    sendCommandList([f"BC", f"SF,5,F"])


# Moves Camera to Default Position: Line or Evacuation
def cameraDefault(position):
    if position == "Line":
        utils.printDebug(f"Set Camera to Line Following Mode", config.softDEBUG)
        sendCommandList(["CL", "SF,4,F"])

    elif position == "Evacuation":
        utils.printDebug(f"Set Camera to Evacaution Zone Mode", config.softDEBUG)
        sendCommandList(["CE", "SF,4,F"])
