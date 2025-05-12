# -------- Robot Actuators/Sensors -------- 
import time
import random
from gpiozero import Button
import numpy as np

from config import *
from utils import *
from line_cam import camera_x, camera_y
from mp_manager import *


print("Robot Functions: \t \t OK")

# Situation Vars:
#objective = "Follow Line"
lastTurn = "Straight"
rotateTo = "right" # When it needs to do 180 it rotates to ...
inGap = False
lastLineDetected = True  # Assume robot starts detecting a line


pickingVictim = False
pickSequenceStatus = "goingToBall" #goingToBall, startReverse, lowerArm, moveForward, pickVictim
pickVictimType = "none"
dumpedAliveVictims = False
dumpedDeadVictims = False
dropSequenceStatus = "searchGoCorner" #searchGoCorner, startReverse, do180, goBackwards, dropVictim
wiggleStage = 0

# Loop Vars
pendingCommandsConfirmation = []

# Pin Definitions
SWITCH_PIN = 14
switch = Button(SWITCH_PIN, pull_up=True)  # Uses internal pull-up

# Motor Vars
M1 = M2 = 1520 # Left - Right
oldM1 = oldM2 = M1
error = errorAcc = lastError = 0

timer_manager = TimerManager()

# Interpret CLI Commands
def CLIinterpretCommand():
    global MotorOverride, LOPOverride, LOPVirtualState

    message = CLIcommandToExecute.value

    if message == "exit": # Exit command
        print("Exiting...")
        terminate.value = True
        return
    elif message == "list":
        print("Command List: ")
        print(f"  - exit")
        print(f"  - vars")
        print(f"  - nextImage")
        """print(f"  - Drop Alive")
        print(f"  - Drop Dead")
        print(f"  - Close Ball Storage")
        print(f"  - Pick Alive")
        print(f"  - Pick Dead")
        print(f"  - Camera Evacuation")
        print(f"  - Camera Line")"""
        print(f"  - MotorOverride <0 or 1>")
        print(f"  - LOPOverride <0 or 1>")
        print(f"  - LOPState <0 or 1>")
        print(f"  - Objective <FL or EZ>")
        print(f"  - ZoneStatus <notStarted, begin, entry, findVictims, pickup_ball, deposit_red, deposit_green, exit>")
    elif message == "vars":
        print(f"  - LOPOverride: {LOPOverride}")
        print(f"  - LOPVirtualState: {LOPVirtualState}")
        print(f"  - MotorOverride: {MotorOverride}")
        print(f"  - Objective: {objective.value}")
        print(f"  - Zone Status: {zoneStatus.value}")
        print(f"  - Zone Start Time: {round(zoneStartTime.value, 3)}")
        print(f"  - Zone Duration: {round(time.perf_counter() - zoneStartTime.value, 3) if zoneStartTime.value != -1 else 'Not Started'}")
    elif message == "": #Next Image
        printDebug("Next Image", False)
        updateFakeCamImage.value = True
    elif message.startswith("MotorOverride"):
        try:
            MotorOverride = bool(int(message.split()[1]))
            print(f"Motor Override set to {MotorOverride}")
        except (ValueError, IndexError):
            print("Invalid motorOverride command. Use 'motorOverride <0 or 1>'")
    elif message.startswith("LOPOverride"):
        try:
            LOPOverride = bool(int(message.split()[1]))
            print(f"LOP Override set to {LOPOverride}")
        except (ValueError, IndexError):
            print("Invalid LOPOverride command. Use 'LOPOverride <0 or 1>'")
    elif message.startswith("LOPState"):
        try:
            LOPVirtualState = bool(int(message.split()[1]))
            print(f"LOP State set to {LOPVirtualState}")
            if not LOPOverride:
                print(f"LOP Override is OFF. LOP State will not change anything.")
                print(f"Run LOPOverride <1> to be able to change LOP State.")
        except (ValueError, IndexError):
            print("Invalid LOPState command. Use 'LOPState <0 or 1>'")
    elif message.startswith("Objective"):
        try:
            _, objectiveCode = message.split(maxsplit=1)
            objectiveCode = objectiveCode.strip().upper()

            if objectiveCode == "FL":
                objective.value = "follow_line"
                print("Objective set to FOLLOW LINE.")
            elif objectiveCode == "EZ":
                objective.value = "zone"
                print("Objective set to ZONE.")
            else:
                print(f"Unknown Objective '{objectiveCode}'. Use 'FL' or 'EZ'.")
        except (ValueError, IndexError):
            print("Invalid Objective command. Use 'Objective FL' or 'Objective EZ'.")
    elif message.startswith("ZoneStatus"):
        try:
            _, zoneCode = message.split(maxsplit=1)
            zoneCode = zoneCode.strip().lower()

            allowedZoneStatuses = [
                "notstarted", "begin", "entry", "findvictims",
                "pickup_ball", "deposit_red", "deposit_green", "exit"
            ]

            if zoneCode in allowedZoneStatuses:
                zoneStatus.value = zoneCode
                print(f"ZoneStatus set to '{zoneCode}'.")
            else:
                print(f"Unknown ZoneStatus '{zoneCode}'. Allowed: {allowedZoneStatuses}")
        except (ValueError, IndexError):
            print("Invalid ZoneStatus command. Example: 'ZoneStatus begin'")
    CLIcommandToExecute.value = "none" # Reset command to none


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


# Sends command lists to Serial Process (requiring confirmation by RPi Pico)
def sendCommandListWithConfirmation(commandList):
    global pendingCommandsConfirmation
    if commandWithConfirmation.value == "none" and len(pendingCommandsConfirmation) == 0: # Send One Command to mySerial Straight Away
        commandWithConfirmation.value = commandList[0]
        commandList.pop(0)
    for command in commandList: # Add the rest to pending list
        pendingCommandsConfirmation.append(command)


def sendSerialPendingCommandsConfirmation():
    global pendingCommandsConfirmation
    if len(pendingCommandsConfirmation) > 0:
        if commandWithConfirmation.value == "none":
            commandWithConfirmation.value = pendingCommandsConfirmation[0]
            pendingCommandsConfirmation.pop(0)


def sendCommandNoConfirmation(command):
    if commandWithoutConfirmation.value == "none":
        commandWithoutConfirmation.value = command
    else:
        print(f"Check Error: Command with no confirmation pending: {commandWithoutConfirmation.value} at {time.perf_counter()}")

# Pick Victim Function (takes "Alive" or "Dead")
def pickVictim(type, step=0):
    if not LOPstate.value:
        printDebug(f"pickVictim Function: {type} {step}", False)
        if timer_manager.is_timer_expired("armCooldown"): # Only pickVictims every 2.5 seconds 
            if step == 1:
                printDebug(f"Lowering Arm", False)
                sendCommandListWithConfirmation(["AD"])
            elif step == 2:
                printDebug(f"Pick {type}", False)
                sendCommandListWithConfirmation([f"P{type}", "SF,0,F", "SF,1,F", "SF,2,F", "SF,3,F"])
                timer_manager.set_timer("armCooldown", 2.5)
            else:
                printDebug(f"Pick {type}", False)
                sendCommandListWithConfirmation(["AD", f"P{type}", "SF,0,F", "SF,1,F", "SF,2,F", "SF,3,F"])
                timer_manager.set_timer("armCooldown", 2.5)
    else:
        printDebug(f"I Would have Picked {type}", False)
  

# Drop Function (takes "Alive" or "Dead")
def ballRelease(type):
    printDebug(f"Drop {type}", softDEBUG)

    sendCommandListWithConfirmation([f"D{type}", f"SF,5,F"])


# Closes Ball Storage
def closeBallStorage():
    printDebug(f"Close Ball Storage", softDEBUG)

    sendCommandListWithConfirmation([f"BC", f"SF,5,F"])


# Moves Camera to Default Position: Line or Evacuation
def cameraDefault(position):
    if position == "Line":
        printDebug(f"Set Camera to Line Following Mode", softDEBUG)
        sendCommandListWithConfirmation(["CL", "SF,4,F"])

    elif position == "Evacuation":
        printDebug(f"Set Camera to Evacaution Zone Mode", softDEBUG)
        sendCommandListWithConfirmation(["CE", "SF,4,F"])


#Returns True if the switch is ON, False otherwise.
def isSwitchOn():
    if not LOPOverride: # Not LOP Override
        return switch.is_pressed
    else: # LOP Override == True
        return LOPVirtualState


# Controller for LoP
def LoPSwitchController():
    global switchState, rotateTo
    
    if LOPOverride: # LOP Override == True
        switchState = LOPVirtualState
        return # Skips updates

    if isSwitchOn():
        if switchState == False: # First time detected as on
            switchState = True
            printDebug(f"LoP Switch is now ON: {switchState}", softDEBUG)
            objective.value = "follow_line"
            zoneStatus.value = "notStarted"
            timer_manager.clear_all_timers()
            cameraDefault("Line")
            #message = f"M({1525}, {1524})"
            #mySerial.sendSerial(f"M({1525}, {1524})")
    else:
        if switchState == True:
            switchState = False
            printDebug(f"LoP Switch is now OFF: {switchState}", softDEBUG)
            objective.value = "follow_line"
            zoneStatus.value = "notStarted"
            rotateTo = "right" if rotateTo == "left" else "left" # Toggles rotate To


# Calculate motor Speed difference from default
def PID(lineCenterX):
    global error, errorAcc, lastError
    error = lineCenterX - 1280 / 2 # Camera view is 1280 pixels
    errorAcc = errorAcc + error

    motorSpeed = KP * error + KD * (error - lastError) + KI * errorAcc

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
    motorSpeed = (KP * error_x + 
                  KD * (error_x - lastError) + 
                  KI * errorAcc + 
                  KP_THETA * error_theta)  # New term for angle correction

    lastError = error_x  # Only update last error for x

    return motorSpeed


# Calculate motor Speed
def calculateMotorSpeeds(motorSpeed):
    global M1, M2
    m1Speed = DEFAULT_FORWARD_SPEED + motorSpeed
    m2Speed = DEFAULT_FORWARD_SPEED - motorSpeed

    # Ensure values are within ESC_MIN and ESC_MAX
    m1Speed = max(MIN_GENERAL_SPEED, min(MAX_DEFAULT_SPEED, m1Speed))
    m2Speed = max(MIN_GENERAL_SPEED, min(MAX_DEFAULT_SPEED, m2Speed))

    # Adjust for dead zone (avoid 1450-1550)
    if 1450 <= m1Speed <= 1550:
        m1Speed = DEFAULT_STOPPED_SPEED + ESC_DEADZONE if m1Speed > DEFAULT_STOPPED_SPEED else DEFAULT_STOPPED_SPEED - ESC_DEADZONE
    if 1450 <= m2Speed <= 1550:
        m2Speed = DEFAULT_STOPPED_SPEED + ESC_DEADZONE if m2Speed > DEFAULT_STOPPED_SPEED else DEFAULT_STOPPED_SPEED - ESC_DEADZONE
    
    #printDebug(f"Line Center: {lineCenterX.value}, Angle: {round(np.rad2deg(lineAngle.value), 0)} motorSpeed: {motorSpeed}, M1: {m1Speed}, M2: {m2Speed}", softDEBUG)

    return m1Speed, m2Speed


# Update Motor Vars accordingly
def setMotorsSpeeds(guidanceFactor):
    global M1, M2, M1info, M2info, motorSpeedDiference
    
    motorSpeedDiference = PID2(guidanceFactor, lineAngle.value)
    M1, M2 = calculateMotorSpeeds(motorSpeedDiference)

    if redDetected.value and not objective.value == "zone":
        M1, M2 = 1520, 1520

    if inGap:
        M1, M2 = DEFAULT_FORWARD_SPEED, DEFAULT_FORWARD_SPEED

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
def controlMotors():
    global oldM1, oldM2
    def sendMotorsIfNew(m1, m2):
        """Send motor command only if values changed."""
        global oldM1, oldM2
        if m1 != oldM1 or m2 != oldM2:
            sendCommandNoConfirmation(f"M({int(m1)}, {int(m2)})")
            oldM1, oldM2 = m1, m2
    def canGamepadControlMotors():
        """Determine if user input should control motors."""
        return switchState or MotorOverride

    if not canGamepadControlMotors():
        # No gamepad control
        if not timer_manager.is_timer_expired("stop"): # Force Automatic Stop
            printDebug("Motors: LOP OFF + No Override -> TIMER active -> STOP Motors", False) # Debug
            sendMotorsIfNew(DEFAULT_STOPPED_SPEED, DEFAULT_STOPPED_SPEED)
        else:
            sendMotorsIfNew(int(M1), int(M2)) # Default Autonumous control
        return

    # Gamepad control allowed
    printDebug("Motors: Gamepad Control Active (LOP ON or Override ON)", False) # Debug
    sendMotorsIfNew(gamepadM1.value, gamepadM2.value)

# Decide which ball needs to be picked up
def decideVictimType():
    if ballType.value == "silver ball":
        pickVictimType = "A"
    elif ballType.value == "black ball":
        pickVictimType = "D"
    else:
        print(f"Possible Error: Ball Type is {ballType.value} - Not a ball")
        pickVictimType = "A" # just failsafe for null

    alive = ballType.value == "silver ball"
    if not alive and pickedUpDeadCount.value > 0:
        pickVictimType = "A"
        print(f"Used extra failsafe: Too many Black Balls")
    elif alive and pickedUpAliveCount.value > 1:
        pickVictimType = "D"
        print(f"Used extra failsafe: Too many Silver Balls")
    
    return pickVictimType


def needToDeposit():
    pass


def zoneDeposit(type):
    global dropSequenceStatus, dumpedAliveVictims, dumpedDeadVictims

    def searchGoCorner():
        global dropSequenceStatus, wiggleStage

        if cornerHeight.value == 0: # No corner detected
            setManualMotorsSpeeds(1230 if rotateTo == "left" else 1750, 1750 if rotateTo == "left" else 1230)
            controlMotors()
        else: # Corner detected
            setMotorsSpeeds(cornerCenter.value)
            controlMotors()
            if cornerHeight.value >= camera_y * 0.45: # Close to Corner
                printDebug(f"Victim Dropping - Going Back 1", softDEBUG)
                dropSequenceStatus = "startReverse"
                wiggleStage = 0
                timer_manager.set_timer("zoneReverse", 1.0)
    def dropVictim():
        global dropSequenceStatus, wiggleStage
        if wiggleStage == 0:
            ballRelease(type)  # "A" Or "D" based on the victim
            printDebug("Victim Dropping - Opening Ball Storage", softDEBUG)
            wiggleStage = 1
            timer_manager.set_timer("wiggle", 0.3)  # Short delay before first wiggle

        elif wiggleStage == 1:
            setManualMotorsSpeeds(1800, 1800)  # Small forward movement
            controlMotors()
            if timer_manager.is_timer_expired("wiggle"):
                wiggleStage = 2
                timer_manager.set_timer("wiggle", 0.3)

        elif wiggleStage == 2:
            setManualMotorsSpeeds(1200, 1200)  # Small backward movement
            controlMotors()
            if timer_manager.is_timer_expired("wiggle"):
                wiggleStage = 3
                timer_manager.set_timer("wiggle", 0.3)

        elif wiggleStage == 3:
            setManualMotorsSpeeds(1800, 1800)  # Second wiggle forward
            controlMotors()
            if timer_manager.is_timer_expired("wiggle"):
                wiggleStage = 4
                timer_manager.set_timer("wiggle", 0.3)

        elif wiggleStage == 4:
            setManualMotorsSpeeds(1200, 1200)  # Small backward movement
            controlMotors()
            if timer_manager.is_timer_expired("wiggle"):
                wiggleStage = 5
                timer_manager.set_timer("wiggle", 0.3)
                printDebug("Victim Dropping - Finished Wiggle", softDEBUG)
                dropSequenceStatus = "finished"
                wiggleStage = 0
            
    if dropSequenceStatus == "searchGoCorner":
        #printDebug(f"Victim Dropping - Searching for Green Evacuation Point", False)
        searchGoCorner()
    elif dropSequenceStatus == "startReverse":
        setManualMotorsSpeeds(1300, 1300)  # Go backward
        controlMotors()
        if timer_manager.is_timer_expired("zoneReverse"):
            setManualMotorsSpeeds(1230 if rotateTo == "left" else 1750, 1750 if rotateTo == "left" else 1230)
            controlMotors()
            printDebug(f"Victim Dropping - doing 180", softDEBUG)
            dropSequenceStatus = "do180"
            timer_manager.set_timer("do180", 1.0)
    elif dropSequenceStatus == "do180":
        setManualMotorsSpeeds(1230 if rotateTo == "left" else 1750, 1750 if rotateTo == "left" else 1230)
        controlMotors()
        if timer_manager.is_timer_expired("do180"):
            setManualMotorsSpeeds(1300, 1300)  # Go backward
            controlMotors()
            printDebug(f"Victim Dropping - Going Back 2", softDEBUG)
            dropSequenceStatus = "goBackwards"
            timer_manager.set_timer("zoneReverse", 1.0)
    elif dropSequenceStatus == "goBackwards":
        setManualMotorsSpeeds(1300, 1300)  # Go backward
        controlMotors()
        if timer_manager.is_timer_expired("zoneReverse"):
            setManualMotorsSpeeds(DEFAULT_STOPPED_SPEED, DEFAULT_STOPPED_SPEED)  # Stop motors
            controlMotors()
            printDebug(f"Victim Dropping - Dropping Victim", softDEBUG)
            dropSequenceStatus = "dropVictim"
            timer_manager.set_timer("do180", 1.0)
    elif dropSequenceStatus == "dropVictim":
        dropVictim()
    elif dropSequenceStatus == "finished":
        setManualMotorsSpeeds(DEFAULT_STOPPED_SPEED, DEFAULT_STOPPED_SPEED)  # Stop motors
        controlMotors()
        closeBallStorage()
        dropSequenceStatus = "searchGoCorner"  # Reset to searchGoCorner for next victim

        if type == "A":
            dumpedAliveVictims = True
            pickedUpAliveCount.value = 0
            zoneStatus.value = "depositRed"

        elif type == "D":
            dumpedDeadVictims = True
            pickedUpDeadCount.value = 0
            zoneStatus.value = "finishEvacuation"

        


def intersectionController():
    global lastTurn
    if turnDirection.value != lastTurn:
        printDebug(f"New Turn direction {turnDirection.value} {lastTurn}", DEBUG)
        
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
    global switchState, M1, M2, M1info, M2info, oldM1, oldM2, motorSpeedDiference, error_theta, error_x, errorAcc, lastError, inGap
    global pickingVictim, pickSequenceStatus, pickVictimType

    sendCommandListWithConfirmation(["GR","BC", "SF,5,F", "CL", "SF,4,F", "AU", "PA", "SF,0,F", "SF,1,F", "SF,2,F", "SF,3,F"])

    if True: # True if only testing Evac
        objective.value = "zone"
        zoneStatus.value = "begin"
        time.sleep(5)
        cameraDefault("Evacuation")

    switchState = isSwitchOn()
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
    timer_manager.add_timer("armCooldown", 0.05)
    timer_manager.add_timer("zoneReverse", 0.05)
    timer_manager.add_timer("lowerArm", 0.05)
    timer_manager.add_timer("zoneForward", 0.05)
    timer_manager.add_timer("do180", 0.05)
    timer_manager.add_timer("wiggle", 0.05)
    time.sleep(0.1)


    # Wait for all serial initialization commands to be sent
    while commandWaitingListLength.value != 0 or len(pendingCommandsConfirmation) != 0: 
        time.sleep(0.05)
        sendSerialPendingCommandsConfirmation()
        #print(f"Waiting for command list to be empty: {commandWaitingListLength.value}")


    resetBallArrays.value = True
    time.sleep(5 * lineDelayMS * 0.001) # wait for 5 cam loops to register

    print(f"")
    print(f"")
    print(f"-------- Robot.py: All Setup Procedures have finished. --------")
    print(f"------------------ Robot.py: Starting Loop. ------------------")
    print(f"")
    print(f"")

    counter = 0
    t0 = time.perf_counter()
    while not terminate.value:
        t1 = t0 + controlDelayMS * 0.001

        # Loop
        LoPSwitchController()
        LOPstate.value = 1 if switchState == True else 0
        if not pickingVictim:
            zoneStatusLoop = zoneStatus.value
        objectiveLoop = objective.value
        

        # ----- LINE FOLLOWING ----- 
        if objectiveLoop == "follow_line":
            gapController()

            setMotorsSpeeds(lineCenterX.value)
            intersectionController()
            controlMotors()
        
        # ----- EVACUATION ZONE ----- 
        elif objectiveLoop == "zone":
            if pickedUpAliveCount.value > 1 and not dumpedAliveVictims and zoneStatusLoop != "depositGreen": # 2 (or maybe more if mistake)
                zoneStatus.value = "depositGreen"
            
            elif pickedUpDeadCount.value > 0 and not dumpedDeadVictims and zoneStatusLoop != "depositRed": # 1 (ormaybe more if mistake)
                zoneStatus.value = "depositRed"

            if zoneStatusLoop == "begin":
                timer_manager.set_timer("stop", 5.0) # 10 seconds to signal that we entered
                timer_manager.set_timer("zoneEntry", 8.0) # 3 (5+3) seconds to entry the zone
                cameraDefault("Evacuation")
                silverValue.value = -1
                if zoneStartTime.value == -1:
                    zoneStartTime.value = time.perf_counter()
                zoneStatus.value = "entry" # go to next Step

            elif zoneStatusLoop == "entry":
                if not timer_manager.is_timer_expired("zoneEntry"):
                    M1, M2 = 1800, 1800
                    controlMotors()
                else: # timer expired
                    timer_manager.set_timer("stop", 5.0) # 10 seconds to signal that we entered
                    zoneStatus.value = "findVictims"
            
            elif zoneStatusLoop == "findVictims":
                #print(f"Here 4-----------------")
                setManualMotorsSpeeds(1230 if rotateTo == "left" else 1750, 1750 if rotateTo == "left" else 1230)
                controlMotors()
            
                if ballExists.value:
                    zoneStatus.value = "goToBall"

            elif zoneStatusLoop == "goToBall":
                if not ballExists.value:
                    zoneStatus.value = "findVictims"

                if pickSequenceStatus == "goingToBall":
                    setMotorsSpeeds(ballCenterX.value)
                    controlMotors()

                    if ballBottomY.value >= camera_y * 0.95:
                        pickSequenceStatus = "startReverse"
                        
                        pickVictimType = decideVictimType()

                        pickingVictim = True
                        printDebug(f" ----- Starting {pickVictimType} Victim Catching ----- ", softDEBUG)
                        printDebug(f"Victim Catching - Reversing", False)
                        timer_manager.set_timer("zoneReverse", 1.0)

                elif pickSequenceStatus == "startReverse":
                    setManualMotorsSpeeds(1300, 1300)  # Go backward
                    controlMotors()
                    if timer_manager.is_timer_expired("zoneReverse"):
                        setManualMotorsSpeeds(DEFAULT_STOPPED_SPEED, DEFAULT_STOPPED_SPEED)  # Stop motors
                        controlMotors()
                        printDebug(f"Victim Catching - Lowering Arm", False)
                        pickVictim(pickVictimType, step=1) # Lower Arm
                        pickSequenceStatus = "loweringArm"
                        timer_manager.set_timer("lowerArm", 2.0)
                
                elif pickSequenceStatus == "loweringArm":
                    setManualMotorsSpeeds(DEFAULT_STOPPED_SPEED, DEFAULT_STOPPED_SPEED)
                    controlMotors()
                    if timer_manager.is_timer_expired("lowerArm"):
                        printDebug(f"Victim Catching - Moving Forward", False)
                        pickSequenceStatus = "moveForward"
                        timer_manager.set_timer("zoneForward", 1.0)

                elif pickSequenceStatus == "moveForward":
                    setManualMotorsSpeeds(1800, 1800)  # Go forward slowly
                    controlMotors()
                    if timer_manager.is_timer_expired("zoneForward"):
                        setManualMotorsSpeeds(DEFAULT_STOPPED_SPEED, DEFAULT_STOPPED_SPEED)
                        controlMotors()
                        pickVictim(pickVictimType, step=2)
                        printDebug(f"Victim Catching - Picking Victim", False)
                        pickSequenceStatus = "finished"

                elif pickSequenceStatus == "finished":
                    printDebug(f"Victim Catching - Finished", False)
                    pickingVictim = False
                    resetBallArrays.value = True
                    zoneStatus.value = "findVictims"
                    pickSequenceStatus = "goingToBall"

                    if pickVictimType == "A" and pickedUpAliveCount.value < 2:
                        pickedUpAliveCount.value += 1
                    else:
                        pickedUpDeadCount.value += 1

                    printDebug(f"Picked up {'alive' if pickVictimType == 'A' else 'dead'} victim, new total: {pickedUpAliveCount.value + pickedUpDeadCount.value} victims", softDEBUG)
                    printDebug(f"Picked up {pickedUpAliveCount.value} alive and {pickedUpDeadCount.value} dead", softDEBUG)

                    if pickedUpAliveCount.value + pickedUpDeadCount.value == 3:
                        zoneStatus.value = "depositGreen"
                        continue

            elif zoneStatusLoop == "depositGreen":
                zoneDeposit("A")

            elif zoneStatusLoop == "depositRed":
                zoneDeposit("D")

            elif zoneStatusLoop == "finishEvacuation":
                printDebug(f"Finished Evacuation - Leaving", softDEBUG)
                printDebug(f"Finished the Evacuation Zone in {time.perf_counter() - zoneStartTime.value} s", softDEBUG)

        CLIinterpretCommand()
        intrepretCommand()
        sendSerialPendingCommandsConfirmation()

        if len(pendingCommandsConfirmation) > 5:
            print(f"We have {len(pendingCommandsConfirmation)} pending commands: {commandWithConfirmation.value} + {pendingCommandsConfirmation}")     

        M1info = M1
        M2info = M2

        lastObjective = objective.value
        
        if objectiveLoop == "follow_line":
            debugMessage = (
                f"Center: {lineCenterX.value} \t"
                #f"Angle: {round(np.rad2deg(lineAngle.value),2)} \t"
                f"LineBias: {int(KP * error_x + KD * (error_x - lastError) + KI * errorAcc)}   \t"
                f"AngBias: {round(KP_THETA*error_theta,2)}     \t"
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
            #printDebug(f"{debugMessage}", softDEBUG)
        if objectiveLoop == "zone":
            debugMessage = (
                #f"Center: {lineCenterX.value} \t"
                #f"LineBias: {int(KP * error_x + KD * (error_x - lastError) + KI * errorAcc)}   \t"
                f"ballExists: {ballExists.value} "
                #f"ballType: {ballType.value} "
                #f"ballCenter: {int(ballCenterX.value)} \t"
                #f"ballBottom: {int(ballBottomY.value)} {ballBottomY.value >= camera_y * 0.95}\t"
                #f"ballWidth: {ballWidth.value} \t"
                f"M1: {int(M1info)} "
                f"M2: {int(M2info)} \t"
                #f"LOP: {switchState} \t"
                #f"Loop: {objective.value}\t"
                f"var: {zoneStatus.value} {zoneStatusLoop} {pickSequenceStatus} "
                f"pickVictim: {pickingVictim}"
                #f"Commands: {commandWaitingList}"
            )
            counter += 1
            if counter % 5 == 0:
                #printDebug(f"{debugMessage}", softDEBUG)
                pass
        
        #print(f"ballBottom: {int(ballBottomY.value)} {ballBottomY.value >= camera_y * 0.95} ballType {ballType.value} \t")


        while (time.perf_counter() <= t1):
            time.sleep(0.0005)
        t0 = t1
    
    print(f"Shutting Down Robot Control Loop")