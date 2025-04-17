# -------- Robot Actuators/Sensors -------- 
import time
from gpiozero import Button
import numpy as np

import config
from utils import *
from line_cam import camera_x, camera_y
import mySerial
from mp_manager import *


print("Robot Functions: \t \t OK")

# Situation Vars:
#objective = "Follow Line"
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
        if switchState == False: # First time detected as on
            switchState = True
            printDebug(f"LoP Switch is now ON: {switchState}", config.softDEBUG)
            objective.value = "follow_line"
            zoneStatus.value = "notStarted"
            timer_manager.clear_all_timers()
            cameraDefault("Line")
            #message = f"M({1525}, {1524})"
            #mySerial.sendSerial(f"M({1525}, {1524})")
    else:
        if switchState == True:
            switchState = False
            printDebug(f"LoP Switch is now OFF: {switchState}", config.softDEBUG)
            objective.value = "follow_line"
            zoneStatus.value = "notStarted"
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
def setMotorsSpeeds2():
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


def setMotorsSpeeds(guidanceFactor):
    global M1, M2, M1info, M2info, motorSpeedDiference
    
    motorSpeedDiference = PID2(guidanceFactor, lineAngle.value)
    M1, M2 = calculateMotorSpeeds(motorSpeedDiference)

    if redDetected.value and not objective.value == "zone":
        M1, M2 = 1520, 1520

    if inGap:
        M1, M2 = config.DEFAULT_FORWARD_SPEED, config.DEFAULT_FORWARD_SPEED

    elif not timer_manager.is_timer_expired("uTurn"):
        M1, M2 = (1000, 2000) if rotateTo == "left" else (2000, 1000)
    
    elif not timer_manager.is_timer_expired('backwards'):
        M1, M2 = 1000, 1000

    elif -0.2 < timer_manager.get_remaining_time('uTurn') < 0:
        timer_manager.set_timer('backwards', 1.0)

    M1info, M2info = M1, M2


def setManualMotorsSpeeds(M1_manual, M2_manual):
    global M1, M2
    M1, M2 = M1_manual, M2_manual

       
# Control Motors
def controlMotors2():
    global oldM1, oldM2

    if not timer_manager.is_timer_expired("stop"):
        message = f"M({config.DEFAULT_STOPPED_SPEED}, {config.DEFAULT_STOPPED_SPEED})"
        oldM1, oldM2 = 0, 0 # impossible values so it gets reassigned as soon as timer ends
    elif M1 != oldM1 or M2 != oldM2:
        message = f"M({int(M1)}, {int(M2)})"
    else:
        return    
    
    if switchState and (M1 != config.DEFAULT_STOPPED_SPEED or M2 != config.DEFAULT_STOPPED_SPEED): # LOP ON
        message = f"M({config.DEFAULT_STOPPED_SPEED}, {config.DEFAULT_STOPPED_SPEED})"

    mySerial.sendSerial(message)



def controlMotors():
    global oldM1, oldM2

    if switchState:
        if gamepadM1.value != oldM1 or gamepadM2.value != oldM2:
            mySerial.sendSerial(f"M({gamepadM1.value}, {gamepadM2.value})")
            oldM1, oldM2 = gamepadM1.value, gamepadM2.value
        return

    if not timer_manager.is_timer_expired("stop"):
        mySerial.sendSerial(f"M({config.DEFAULT_STOPPED_SPEED}, {config.DEFAULT_STOPPED_SPEED})")
        oldM1, oldM2 = 0, 0  # Force re-evaluation when the timer ends
        return

    # Only send a new command if motor values changed
    if M1 != oldM1 or M2 != oldM2:
        mySerial.sendSerial(f"M({int(M1)}, {int(M2)})")
    
    oldM1, oldM2 = M1, M2



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
            timer_manager.set_timer("noLine", 0.60) # Start a timer 600ms after last seeing it
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
    global switchState, M1, M2, M1info, M2info, oldM1, oldM2, motorSpeedDiference, error_theta, error_x, errorAcc, lastError, inGap, switchState

    sendCommandList(["GR","BC", "SF,5,F", "CL", "SF,4,F", "AU", "PA", "SF,0,F", "SF,1,F", "SF,2,F", "SF,3,F"])

    if True: # True if only testing Evac
        objective.value = "zone"
        zoneStatus.value = "findVictims"
        time.sleep(5)
        cameraDefault("Evacuation")

    switchState = is_switch_on()
    motorSpeedDiference = 0
    M1info = 0
    M2info = 0
    error_theta = 0
    error_x = 0
    lastError = 0
    errorAcc = 0

    debugMessage = ""

    # Timers
    timer_manager.add_timer("stop", 0.05)
    timer_manager.add_timer("uTurn", 0.05)
    timer_manager.add_timer("backwards", 0.05)
    timer_manager.add_timer("noLine", 0.05)
    timer_manager.add_timer("zoneEntry", 0.05)
    time.sleep(0.1)

    t0 = time.perf_counter()
    while not terminate.value:
        t1 = t0 + config.controlDelayMS * 0.001

        # Loop
        LoPSwitchController()
        LOPstate.value = 1 if switchState == True else 0
        zoneStatusLoop = zoneStatus.value
        objectiveLoop = objective.value
        
        printDebug(f"Robot Not Waiting: {notWaiting}", config.DEBUG)
        if notWaiting:

            # ----- LINE FOLLOWING ----- 
            if objectiveLoop == "follow_line":
                gapController()

                setMotorsSpeeds(lineCenterX.value)
                intersectionController()
                controlMotors()
            
            # ----- EVACUATION ZONE ----- 
            elif objectiveLoop == "zone":

                if zoneStatusLoop == "begin":
                    #print(f"Here 1-----------------")
                    timer_manager.set_timer("stop", 5.0) # 10 seconds to signal that we entered
                    timer_manager.set_timer("zoneEntry", 8.0) # 3 (5+3) seconds to entry the zone
                    cameraDefault("Evacuation")
                    #sendCommandList(["CE","SF,4,F"])
                    silverValue.value = -1
                    zoneStatus.value = "entry" # go to next Step

                elif zoneStatusLoop == "entry":
                # print(f"Here 2-----------------")
                    if not timer_manager.is_timer_expired("zoneEntry"):
                        M1, M2 = 1800, 1800
                        controlMotors()
                    else: # timer expired
                        #print(f"Here 3-----------------")
                        timer_manager.set_timer("stop", 5.0) # 10 seconds to signal that we entered
                        zoneStatus.value = "findVictims"
                
                elif zoneStatusLoop == "findVictims":
                    #print(f"Here 4-----------------")
                    setManualMotorsSpeeds(1250 if rotateTo == "left" else 1750, 1750 if rotateTo == "left" else 1250)
                    controlMotors()
                
                elif zoneStatusLoop == "goToBall":
                    setMotorsSpeeds(ballCenterX.value)
                    #M1, M2 = 1520, 1520
                    controlMotors()
                    print(f"here 3 {ballBottomY.value} {ballBottomY.value >= camera_y * 0.95}")
                    if ballBottomY.value >= camera_y * 0.80 and not LOPstate.value:
                        print(f"Here?? {ballBottomY.value} {ballType.value}")
                        if ballType.value == "silver ball":
                            print(f"Here1")
                            pickVictim("A")
                        elif ballType.value == "black ball":
                            print(f"Here2")
                            pickVictim("D")
                        zoneStatus.value = "findVictim"
                        


        intrepretCommand()
        receivedMessage = mySerial.readSerial(config.DEBUG)
        interpretMessage(receivedMessage)


        #oldM1 = M1
        #oldM2 = M2

        M1info = M1
        M2info = M2

        lastObjective = objective.value
        
        if objectiveLoop == "follow_line" and notWaiting:
            debugMessage = (
                f"Center: {lineCenterX.value} \t"
                #f"Angle: {round(np.rad2deg(lineAngle.value),2)} \t"
                f"LineBias: {int(config.KP * error_x + config.KD * (error_x - lastError) + config.KI * errorAcc)}   \t"
                f"AngBias: {round(config.KP_THETA*error_theta,2)}     \t"
                f"Reason: {turnReason.value} \t"
                #f"isCrop: {isCropped.value} \t"
                #f"line: {lineDetected.value} \t"
                f"inGap: {inGap}\t"
                #f"Turn: {turnDirection.value}     \t"
                #f"Motor D: {round(motorSpeedDiference, 2)}   \t"
                f"Siver: {round(float(silverValue.value),3)} \t"
                f"M1: {int(M1info)} \t"
                f"M2: {int(M2info)} \t"
                f"LOP: {switchState} \t"
                f"Loop: {objective.value}\t"
                f"var: {zoneStatus.value}  "
                #f"Commands: {commandWaitingList}"
                #f"LOP: {LOPstate.value}"
            )
            #printDebug(f"{debugMessage}", config.softDEBUG)
        if objectiveLoop == "zone" and notWaiting:
            debugMessage = (
                #f"Center: {lineCenterX.value} \t"
                #f"LineBias: {int(config.KP * error_x + config.KD * (error_x - lastError) + config.KI * errorAcc)}   \t"
                f"ballType: {ballType.value} \t"
                f"ballCenter: {ballCenterX.value} \t"
                f"ballBottom: {ballBottomY.value} {ballBottomY.value >= camera_y * 0.95}\t"
                f"ballWidth: {ballWidth.value} \t"
                f"M1: {int(M1info)} \t"
                f"M2: {int(M2info)} \t"
                #f"LOP: {switchState} \t"
                #f"Loop: {objective.value}\t"
                f"var: {zoneStatus.value}  "
                #f"Commands: {commandWaitingList}"
            )
            #printDebug(f"{debugMessage}", config.softDEBUG)
        #if not notWaiting:
         #   printDebug(f"Not Waiting: {notWaiting}", config.softDEBUG)
        


        while (time.perf_counter() <= t1):
            time.sleep(0.0005)
        t0 = t1