# -------- Robot Actuators/Sensors -------- 
import time
import random
from gpiozero import Button
import numpy as np

from config import *
from utils import *
from line_cam import camera_x, camera_y
from mp_manager import *


printConsoles("Robot Functions: \t \t OK")

# Situation Vars:
#objective = "Follow Line"
lastTurn = "Straight"
rotateTo = "right" # When it needs to do 180 it rotates to ...
inGap = False
lastLineDetected = True  # Assume robot starts detecting a line
gapCorrectionStartTime = 0

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
error_x = errorAcc = lastError = 0
avoidingStuck = False
pitch = 0
lastPitch = None
lastPitchTime = None

# Camera Servo Angle
camServoAngle = -1

# Sensor Vars
Accel_X_Array = createEmptyTimeArray()
Accel_Y_Array = createEmptyTimeArray()
Accel_Z_Array = createEmptyTimeArray()
accelAverage_X = accelAverage_Y = accelAverage_Z = 0

Gyro_X_Array = createEmptyTimeArray()
Gyro_Y_Array = createEmptyTimeArray()
Gyro_Z_Array = createEmptyTimeArray()
gyroAverage_X = gyroAverage_Y = gyroAverage_Z = 0

Temp_Array = createEmptyTimeArray()
tempAverage = 0

Tof_1_Array = createEmptyTimeArray()
Tof_2_Array = createEmptyTimeArray()
Tof_3_Array = createEmptyTimeArray()
Tof_4_Array = createEmptyTimeArray()
Tof_5_Array = createEmptyTimeArray()
tofAverage_1 = tofAverage_2 = tofAverage_3 = tofAverage_4 = tofAverage_5 = 0


timer_manager = TimerManager()

# Interpret CLI Commands
def CLIinterpretCommand(mpMessage):
    global MotorOverride, LOPOverride, LOPVirtualState

    message = mpMessage.value

    if message == "exit": # Exit command
        printConsoles("Exiting...")
        terminate.value = True
        return
    elif message == "list":
        printConsoles("Command List: ")
        printConsoles(f"  - exit")
        printConsoles(f"  - vars")
        printConsoles(f"  - nextImage")
        """printConsoles(f"  - Drop Alive")
        printConsoles(f"  - Drop Dead")
        printConsoles(f"  - Close Ball Storage")
        printConsoles(f"  - Pick Alive")
        printConsoles(f"  - Pick Dead")
        printConsoles(f"  - Camera Evacuation")
        printConsoles(f"  - Camera Line")"""
        printConsoles(f"  - MotorOverride <0 or 1>")
        printConsoles(f"  - LOPOverride <0 or 1>")
        printConsoles(f"  - LOPState <0 or 1>")
        printConsoles(f"  - Objective <FL or EZ>")
        printConsoles(f"  - ZoneStatus <notStarted, begin, entry, findVictims, goToBall, depositRed, depositGreen, exit>")
        printConsoles(f"  - cameraFree <15-90>")
        printConsoles(f"  - setLights <0 or 1>")
        printConsoles(f"  - setCustomLights <0-255>")
        printConsoles(f"  - rgbLed <R> <G> <B>  (0-255 each)")
        printConsoles(f"  - PV <Alive|Dead> [step]")
        printConsoles(f"  - DV <Alive|Dead>")
        printConsoles(f"  - BC")
    elif message == "vars":
        printConsoles(f"  - LOPOverride: {LOPOverride}")
        printConsoles(f"  - LOPVirtualState: {LOPVirtualState}")
        printConsoles(f"  - MotorOverride: {MotorOverride}")
        printConsoles(f"  - Objective: {objective.value}")
        printConsoles(f"  - Zone Status: {zoneStatus.value}")
        printConsoles(f"  - Zone Start Time: {round(zoneStartTime.value, 3)}")
        printConsoles(f"  - Zone Duration: {round(time.perf_counter() - zoneStartTime.value, 3) if zoneStartTime.value != -1 else 'Not Started'}")
        printConsoles(f"  - Picked {pickedUpAliveCount.value} Victim(s) and {pickedUpDeadCount.value} Victims(s)")
        printConsoles(f"  - Rescued {dumpedAliveCount.value} Victim(s) and {dumpedDeadCount.value} Victims(s)")
    elif message == "": #Next Image
        printDebug("Next Image", False)
        updateFakeCamImage.value = True
    elif message.startswith("MotorOverride"):
        try:
            MotorOverride = bool(int(message.split()[1]))
            printConsoles(f"Motor Override set to {MotorOverride}")
        except (ValueError, IndexError):
            printConsoles("Invalid motorOverride command. Use 'motorOverride <0 or 1>'")
    elif message.startswith("LOPOverride"):
        try:
            LOPOverride = bool(int(message.split()[1]))
            printConsoles(f"LOP Override set to {LOPOverride}")
        except (ValueError, IndexError):
            printConsoles("Invalid LOPOverride command. Use 'LOPOverride <0 or 1>'")
    elif message.startswith("LOPState"):
        try:
            LOPVirtualState = bool(int(message.split()[1]))
            printConsoles(f"LOP State set to {LOPVirtualState}")
            if not LOPOverride:
                printConsoles(f"LOP Override is OFF. LOP State will not change anything.")
                printConsoles(f"Run LOPOverride <1> to be able to change LOP State.")
        except (ValueError, IndexError):
            printConsoles("Invalid LOPState command. Use 'LOPState <0 or 1>'")
    elif message.startswith("Objective"):
        try:
            _, objectiveCode = message.split(maxsplit=1)
            objectiveCode = objectiveCode.strip().upper()

            if objectiveCode == "FL":
                objective.value = "follow_line"
                cameraDefault("Line")
                printConsoles("Objective set to FOLLOW LINE.")
            elif objectiveCode == "EZ":
                objective.value = "zone"
                zoneStatus.value = "begin"
                cameraDefault("Zone")
                printConsoles("Objective set to ZONE.")
            else:
                printConsoles(f"Unknown Objective '{objectiveCode}'. Use 'FL' or 'EZ'.")
        except (ValueError, IndexError):
            printConsoles("Invalid Objective command. Use 'Objective FL' or 'Objective EZ'.")
    elif message.startswith("ZoneStatus"):
        try:
            _, zoneCode = message.split(maxsplit=1)
            zoneCode = zoneCode.strip()

            allowedZoneStatuses = [
                "notStarted", "begin", "entry", "findVictims",
                "goToBall", "depositRed", "depositGreen", "exit"
            ]

            if zoneCode in allowedZoneStatuses:
                zoneStatus.value = zoneCode
                printConsoles(f"ZoneStatus set to '{zoneCode}'.")
            else:
                printConsoles(f"Unknown ZoneStatus '{zoneCode}'. Allowed: {allowedZoneStatuses}")
        except (ValueError, IndexError):
            printConsoles("Invalid ZoneStatus command. Example: 'ZoneStatus begin'")
    elif message.startswith("cameraFree"):
        try:
            _, posStr = message.split(maxsplit=1)
            pos = int(posStr)
            cameraFree(pos)
        except (ValueError, IndexError):
            printConsoles("Invalid cameraFree command. Use 'cameraFree <15-90>'")
    elif message.startswith("setLights"):
        try:
            _, lightStr = message.split(maxsplit=1)
            lightVal = int(lightStr)
            if lightVal in [0, 1]:
                setLights(lightVal == 1)
            else:
                raise ValueError()
        except (ValueError, IndexError):
            printConsoles("Invalid setLights command. Use 'setLights <0 or 1>'")
    elif message.startswith("setCustomLights"):
        try:
            _, pwmStr = message.split(maxsplit=1)
            pwm = int(pwmStr)
            setCustomLights(pwm)
        except (ValueError, IndexError):
            printConsoles("Invalid setCustomLights command. Use 'setCustomLights <0-255>'")
    elif message.startswith("rgbLed"):
        try:
            parts = message.split()
            r, g, b = int(parts[1]), int(parts[2]), int(parts[3])
            rgbPicoLed(r, g, b)
            printConsoles(f"Set RGB LED to ({r}, {g}, {b})")
        except (ValueError, IndexError):
            printConsoles("Invalid rgbLed command. Use: rgbLed <R> <G> <B> with values 0-255")
    elif message.startswith("PV"):
        try:
            parts = message.split()
            victimType = parts[1].capitalize()
            step = int(parts[2]) if len(parts) > 2 else 0
            if victimType in ["Alive", "Dead"]:
                pickVictim(victimType, step)
                printConsoles(f"pickVictim called with type '{victimType}' and step {step}")
            else:
                printConsoles("Invalid victim type. Use 'Alive' or 'Dead'.")
        except (ValueError, IndexError):
            printConsoles("Invalid pickVictim command. Use: pickVictim <Alive|Dead> [step]")
    elif message.startswith("DV"):
        try:
            parts = message.split()
            victimType = parts[1].capitalize()
            if victimType in ["Alive", "Dead"]:
                ballRelease(victimType)
                printConsoles(f"Dropped victim type '{victimType}'")
            else:
                printConsoles("Invalid victim type. Use 'Alive' or 'Dead'.")
        except (IndexError):
            printConsoles("Invalid dropVictim command. Use: dropVictim <Alive|Dead>")
    elif message == "BC":
        closeBallStorage()
        printConsoles("Ball Storage closed.")


    # Reset command to none
    mpMessage.value = "none"


# Command Intrepreter
def intrepretCommand():
    command = commandToExecute.value
    if command == "none":
        return
    printConsoles(f"Command to Execute: {command}")
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
        printConsoles(f"Check Error: Command with no confirmation pending: {command} at {time.perf_counter()}, {commandWithoutConfirmation.value}, {commandWaitingListLength.value}, {waitingResponseDebug.value}, {waitingSensorDataDebug.value}")


def updateSensorAverages():
    global Accel_X_Array, Accel_Y_Array, Accel_Z_Array, Gyro_X_Array, Gyro_Y_Array, Gyro_Z_Array, Temp_Array, Tof_1_Array, Tof_2_Array, Tof_3_Array, Tof_4_Array, Tof_5_Array
    global accelAverage_X, accelAverage_Y, accelAverage_Z, gyroAverage_X, gyroAverage_Y, gyroAverage_Z, tempAverage, tofAverage_1, tofAverage_2, tofAverage_3, tofAverage_4, tofAverage_5
    if newSensorData.value:
        Accel_X_Array = addNewTimeValue(Accel_X_Array, Accel_X.value)
        Accel_Y_Array = addNewTimeValue(Accel_Y_Array, Accel_Y.value)
        Accel_Z_Array = addNewTimeValue(Accel_Z_Array, Accel_Z.value)

        Gyro_X_Array = addNewTimeValue(Gyro_X_Array, Gyro_X.value)
        Gyro_Y_Array = addNewTimeValue(Gyro_Y_Array, Gyro_Y.value)
        Gyro_Z_Array = addNewTimeValue(Gyro_Z_Array, Gyro_Z.value)

        Temp_Array = addNewTimeValue(Temp_Array, Temp.value)

        Tof_1_Array = addNewTimeValue(Tof_1_Array, Tof_1.value)
        Tof_2_Array = addNewTimeValue(Tof_2_Array, Tof_2.value)
        Tof_3_Array = addNewTimeValue(Tof_3_Array, Tof_3.value)
        Tof_4_Array = addNewTimeValue(Tof_4_Array, Tof_4.value)
        Tof_5_Array = addNewTimeValue(Tof_5_Array, Tof_5.value)
    
        newSensorData.value = False

        # update sensor variables
        accelAverage_X = calculateAverageArray(Accel_X_Array, 0.25)
        accelAverage_Y = calculateAverageArray(Accel_Y_Array, 0.25)
        accelAverage_Z = calculateAverageArray(Accel_Z_Array, 0.25)
        gyroAverage_X = calculateAverageArray(Gyro_X_Array, 0.25)
        gyroAverage_Y = calculateAverageArray(Gyro_Y_Array, 0.25)
        gyroAverage_Z = calculateAverageArray(Gyro_Z_Array, 0.25)
        tempAverage = calculateAverageArray(Temp_Array, 0.25)
        tofAverage_1 = calculateAverageArray(Tof_1_Array, 0.25)
        tofAverage_2 = calculateAverageArray(Tof_2_Array, 0.25)
        tofAverage_3 = calculateAverageArray(Tof_3_Array, 0.25)
        tofAverage_4 = calculateAverageArray(Tof_4_Array, 0.25) 
        tofAverage_5 = calculateAverageArray(Tof_5_Array, 0.25)


        # Sensor Data for Debug
        AccelXArrayDebug.value = accelAverage_X
        AccelYArrayDebug.value = accelAverage_Y
        AccelZArrayDebug.value = accelAverage_Z
        GyroXArrayDebug.value = gyroAverage_X
        GyroYArrayDebug.value = gyroAverage_Y
        GyroZArrayDebug.value = gyroAverage_Z
        TempArrayDebug.value = tempAverage
        Tof1ArrayDebug.value = tofAverage_1
        Tof2ArrayDebug.value = tofAverage_2
        Tof3ArrayDebug.value = tofAverage_3
        Tof4ArrayDebug.value = tofAverage_4
        Tof5ArrayDebug.value = tofAverage_5


def updateRampStateAccelOnly():
    global pitch
    # --- PARAMETERS ---
    PITCH_THRESHOLD = 18       # Minimum angle to consider ramp
    STICKY_TIME = 1.0          # Time to remember we were on a ramp
    SMOOTH_TIME = 0.5          # Time window to smooth accel data

    # --- Get Smoothed Accel Values (use Y-Z plane for pitch) ---
    accY = calculateAverageArray(Accel_Y_Array, SMOOTH_TIME)
    accZ = calculateAverageArray(Accel_Z_Array, SMOOTH_TIME)

    if accY == -1 or accZ == -1:
        return  # Not enough data yet

    pitch = np.degrees(np.arctan2(accY, accZ))
    absPitch = abs(pitch)

    pitchDebug.value = pitch  # For debugging or monitoring

    if absPitch > PITCH_THRESHOLD:
        rampDetected.value = True
        timer_manager.set_timer("wasOnRamp", STICKY_TIME)

        # --- Use Sign of Pitch Directly ---
        if pitch < 0:
            rampUp.value = False
            rampDown.value = True
        elif pitch > 0:
            rampUp.value = True
            rampDown.value = False
        else:
            rampUp.value = False
            rampDown.value = False
    else:
        # Flat surface, reset all
        rampDetected.value = False
        rampUp.value = False
        rampDown.value = False

    # --- Sticky ramp memory ---
    wasOnRamp.value = not timer_manager.is_timer_expired("wasOnRamp")
    

def detectSeesaw():
    global lastPitch, lastPitchTime

    currentTime = time.perf_counter()

    if lastPitch is None or lastPitchTime is None:
        # First call, no previous data yet
        lastPitch = pitch
        lastPitchTime = currentTime
        return False

    deltaPitch = pitch - lastPitch
    deltaTime = currentTime - lastPitchTime

    # Update for next call
    lastPitch = pitch
    lastPitchTime = currentTime

    if deltaTime <= 0:
        # avoid divide-by-zero
        return False

    pitchRate = deltaPitch / deltaTime  # °/s
    pitchRateDebug.value = pitchRate

    if abs(pitchRate) > SEESAW_RATE_THRESHOLD:
        printDebug(f"Seesaw Detected at {time.perf_counter()}: {abs(pitchRate)}", True)
        return True
    else:
        return False


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
    global camServoAngle
    if position == "Line":
        printDebug(f"Set Camera to Line Following Mode", softDEBUG)
        sendCommandListWithConfirmation(["CL", "SF,4,F"])
        camServoAngle = 30

    elif position == "Evacuation":
        printDebug(f"Set Camera to Evacaution Zone Mode", softDEBUG)
        sendCommandListWithConfirmation(["CE", "SF,4,F"])
        camServoAngle = 70


def cameraFree(position):
    global camServoAngle
    if position < 15 or position > 90:
        printDebug(f"Invalid Camera Free Position: {position}", softDEBUG)
        return
    command = "SC,4," + str(position)
    sendCommandListWithConfirmation([str(command), "SF,4,F"])
    camServoAngle = position


def setLights(on = True):
    if on:
        sendCommandListWithConfirmation(["L1"])
    else:
        sendCommandListWithConfirmation(["L0"])


def setCustomLights(pwm):
    if 0 <= pwm <= 255:
        command = "LX," + str(pwm)
        sendCommandListWithConfirmation([command])


def rgbPicoLed(r, g, b):
    if r < 0 or r > 255 or g < 0 or g > 255 or b < 0 or b > 255:
        printConsoles(f"Invalid RGB values: {r}, {g}, {b}")
        return
    command = "RGB," + str(r) + "," + str(g) + "," + str(b)
    sendCommandListWithConfirmation([command])


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
            printDebug(f"LoP Switch is now ON at {time.perf_counter()}: {switchState}", softDEBUG)
            
            setManualMotorsSpeeds(DEFAULT_STOPPED_SPEED, DEFAULT_STOPPED_SPEED)
            controlMotors()
            cameraDefault("Line")
            setCustomLights(200)

            objective.value = "follow_line"
            zoneStatus.value = "notStarted"
            pickedUpAliveCount.value = 0
            pickedUpDeadCount.value = 0
            rotateTo = "right" if rotateTo == "left" else "left" # Toggles rotate To
            resetImageSimilarityArrays.value = True
            resetEvacZoneArrays.value = True
            resetBallArrays.value = True

            timer_manager.clear_all_timers()

            lopCounter.value += 1
            
    else:
        if switchState == True:
            switchState = False
            timer_manager.set_timer("avoidStuckCoolDown", 5) # prevent stuck right after starting
            resetImageSimilarityArrays.value = True
            resetEvacZoneArrays.value = True
            resetBallArrays.value = True
            printDebug(f"LoP Switch is now OFF at {time.perf_counter()}: {switchState}", softDEBUG)
            objective.value = "follow_line"
            zoneStatus.value = "notStarted"
            

# Calculate motor Speed difference from default
def PID(lineCenterX):
    global error_x, errorAcc, lastError

    # Error
    error_x = lineCenterX - camera_x / 2
    
    # Accumulate error for integral term
    errorAcc += error_x

    motorSpeed = KP * error_x + KD * (error_x - lastError) + KI * errorAcc


    lastError = error_x

    return motorSpeed

def PID2(lineCenterX, lineAngle):
    global error_x, errorAcc, lastError, error_theta
    
    # Errors
    error_x = lineCenterX - camera_x / 2
    error_theta = - (lineAngle - (np.pi/2))  # Angle difference from vertical (pi/2)
    
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
    
    #motorSpeedDiference = PID2(guidanceFactor, lineAngle.value)
    motorSpeedDiference = PID(guidanceFactor)
    motorSpeedDiferenceDebug.value = motorSpeedDiference
    M1, M2 = calculateMotorSpeeds(motorSpeedDiference)

    if redDetected.value and not objective.value == "zone":
        M1, M2 = 1520, 1520

    if inGap and (gapState.value == "Finished"): 
        M1, M2 = DEFAULT_FORWARD_SPEED, DEFAULT_FORWARD_SPEED

    elif not timer_manager.is_timer_expired("uTurn"):
        M1, M2 = (1000, 2000) if rotateTo == "left" else (2000, 1000)
    
    elif not timer_manager.is_timer_expired('backwards'):
        M1, M2 = 1000, 1000

    elif -0.2 < timer_manager.get_remaining_time('uTurn') < 0:
        timer_manager.set_timer('backwards', 0.5)

    M1info, M2info = M1, M2


def setMotorSpeedsAngleYAxis(angle, centerX, forward=True):
    """
    angle: in degrees, relative to Y-axis.
        0 = vertical
        + = tilt right (bottom-left to top-right)
        - = tilt left  (bottom-right to top-left)

    centerX: gap center X position in pixels
    camera_x: total camera width in pixels
    """
    # Normalize angle and centerX
    maxAngle = 45.0  # maximum expected tilt
    maxOffset = camera_x / 2 # max lateral offset (half image width)

    angleComponent = angle / maxAngle
    offsetComponent = (centerX - camera_x / 2) / maxOffset

    # Weighted combination (tune weights as needed)
    correctionFactor = 0.6 * angleComponent + 0.4 * offsetComponent

    # Clamp to [-1.25, 1.25] based on motor speed constants (1000, 1300; 1750, 2000)
    clampValue = min(abs(DEFAULT_BACKWARD_SPEED-MIN_GENERAL_SPEED), abs(DEFAULT_FORWARD_SPEED-MAX_DEFAULT_SPEED)) / (2 * 100)
    correctionFactor = max(min(correctionFactor, clampValue), -clampValue)

    # Convert to motor speed delta
    delta = 100 * correctionFactor  # Gain factor

    if forward:
        left = DEFAULT_FORWARD_SPEED - delta
        right = DEFAULT_FORWARD_SPEED + delta
    else:
        left = DEFAULT_BACKWARD_SPEED + delta
        right = DEFAULT_BACKWARD_SPEED - delta

    # Clamp speeds to motor limits
    left = int(max(MIN_GENERAL_SPEED, min(MAX_DEFAULT_SPEED, left)))
    right = int(max(MIN_GENERAL_SPEED, min(MAX_DEFAULT_SPEED, right)))

    setManualMotorsSpeeds(left, right)


def setManualMotorsSpeeds(M1_manual, M2_manual):
    global M1, M2
    M1, M2 = M1_manual, M2_manual


# Control Motors
def controlMotors(avoidStuck = False):
    global oldM1, oldM2
    def sendMotorsIfNew(m1, m2):
        """Send motor command only if values changed."""
        global oldM1, oldM2
        if m1 != oldM1 or m2 != oldM2:
            printDebug(f"Sent Motor Control to Serial Process: M({int(m1)}, {int(m2)}) at {time.perf_counter()}", True)
            sendCommandNoConfirmation(f"M({int(m1)}, {int(m2)})")
            oldM1, oldM2 = m1, m2
    def canGamepadControlMotors():
        """Determine if user input should control motors."""
        return switchState or MotorOverride

    if (stuckDetected.value or avoidingStuck) and not avoidStuck:
        return

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


def timeInEvacZone() -> float:
    zoneDuration.value = time.perf_counter() - zoneStartTime.value
    return time.perf_counter() - zoneStartTime.value


def timeAfterDeposit() -> float:
    zoneTimeAfterDeposit.value = time.perf_counter() - lastDepositTime.value
    return time.perf_counter() - lastDepositTime.value


# Decide which ball needs to be picked up
def decideVictimType():
    if ballType.value == "silver ball":
        pickVictimType = "A"
    elif ballType.value == "black ball":
        pickVictimType = "D"
    else:
        printConsoles(f"Possible Error: Ball Type is {ballType.value} - Not a ball")
        pickVictimType = "A" # just failsafe for null

    alive = ballType.value == "silver ball"
    if not alive and pickedUpDeadCount.value > 0:
        pickVictimType = "A"
        printConsoles(f"Used extra failsafe: Too many Black Balls")
    elif alive and pickedUpAliveCount.value > 1:
        pickVictimType = "D"
        printConsoles(f"Used extra failsafe: Too many Silver Balls")
    
    return pickVictimType


def needToDepositAlive(zoneStatusLoop):
    if zoneStatusLoop == "depositGreen": # Drop already in Progress
        return True
    
    if pickedUpAliveCount.value >= 2 and pickedUpDeadCount.value >= 1: # Best Case Scenario 2 Silver + 1 Black
        printDebug(f"Ready To Drop Alive Ball - Nominal", softDEBUG)
        printDebug(f"{pickedUpAliveCount.value} {pickedUpDeadCount.value} {zoneStatus.value} {zoneStatusLoop} {pickSequenceStatus}", softDEBUG)
        return True 
    
    elif not ballExists.value: # Only go to safeties if no ball is seen
        if timeInEvacZone() >= 90 and pickedUpAliveCount.value > 0: # If it takes too long to find them all we drop what we have
            printDebug(f"Ready To Drop Alive Ball - Time Safety - {pickedUpAliveCount.value} Alive Victims", softDEBUG)
            return True 


def needToDepositDead(zoneStatusLoop):
    # Drop already in Progress
    if zoneStatusLoop == "depositRed":
        return True
    
    # Drop the Silver Balls first
    if pickedUpAliveCount.value > 0:
        return False
    
    # Best Case Scenario: Already dropped 2 Silver
    if pickedUpDeadCount.value >= 1 and dumpedAliveCount.value >= 2:
        printDebug(f"Ready To Drop Dead Ball - Nominal", softDEBUG) 
        printDebug(f"{pickedUpAliveCount.value} {pickedUpDeadCount.value} {zoneStatus.value} {zoneStatusLoop} {pickSequenceStatus}", softDEBUG)
        return True

    elif not ballExists.value: # Only go to safeties if no ball is seen
        if timeInEvacZone() >= 100 and pickedUpDeadCount.value > 0:
            printDebug(f"Ready To Drop Dead Ball - Time Safety - {pickedUpDeadCount.value} Dead Victims", softDEBUG)
            return True
   

def readyToLeave(zoneStatusLoop):
    if zoneStatusLoop == "exit":
        if ballExists.value:
            zoneStatus.value = "goToBall"
            printDebug(f"Aborting Leaving the Evacuation Zone - Ball Detected", softDEBUG)
            return False
        else:
            return True
    
    elif zoneStatusLoop == "depositGreen" or zoneStatusLoop == "depositRed": # Still Depositing
        return False


    elif zoneStatusLoop == "findVictims" and timeAfterDeposit() >= 7.5:
        if dumpedAliveCount.value >= 2 and dumpedDeadCount.value >= 1 and not ballExists.value:
            printDebug(f"Ready to Leave Evacuation Zone - Exiting Procedure Start at {time.perf_counter()}", softDEBUG)
            return True


def entryZone():
    def wallCloserLeft():
        return ( tofAverage_4 - tofAverage_2 ) / tofAverage_2 < -0.2
    def wallCloserRight():
        return ( tofAverage_2 - tofAverage_4 ) / tofAverage_4 < -0.2

    if not timer_manager.is_timer_expired("zoneEntry"):
        if wallCloserLeft():
            setManualMotorsSpeeds(1700, 1950)
        elif wallCloserRight():
            setManualMotorsSpeeds(1950, 1700)
        else:
            setManualMotorsSpeeds(1800, 1800)
        controlMotors()

    else: # timer expired
        timer_manager.set_timer("stop", 2.0) # 2.0 seconds to signal that we entered
        zoneStatus.value = "findVictims"


def goToBall():
    global pickSequenceStatus, pickVictimType

    if not ballExists.value or not timer_manager.is_timer_expired("pickVictimCooldown"): # No ball or in cooldown
        zoneStatus.value = "findVictims"

    if pickSequenceStatus == "goingToBall":
        setMotorsSpeeds(ballCenterX.value)
        controlMotors()

        if ballBottomY.value >= camera_y * 0.95:
            pickSequenceStatus = "startReverse"
            
            pickVictimType = decideVictimType()

            pickingVictim.value = True
            resetBallArrays.value = True
            printDebug(f" ----- Starting {pickVictimType} Victim Catching ----- ", softDEBUG)
            printDebug(f"Ball detection data: {ballExists.value} {ballCenterX.value} {ballBottomY.value} {ballWidth.value} {ballType.value}", DEBUG)
            printDebug(f"Victim Catching - Reversing", DEBUG)
            timer_manager.set_timer("zoneReverse", 0.5)

    elif pickSequenceStatus == "startReverse":
        setManualMotorsSpeeds(1000, 1000)  # Go backward
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
            timer_manager.set_timer("zoneForward", 0.8)

    elif pickSequenceStatus == "moveForward":
        setManualMotorsSpeeds(1800, 1800)  # Go forward slowly
        controlMotors()
        if timer_manager.is_timer_expired("zoneForward"):
            setManualMotorsSpeeds(1350, 1350)
            controlMotors()
            pickVictim(pickVictimType, step=2)
            printDebug(f"Victim Catching - Picking Victim", False)
            pickSequenceStatus = "finished"

    elif pickSequenceStatus == "finished":
        printDebug(f"Victim Catching - Finished", False)
        pickingVictim.value = False
        resetBallArrays.value = True
        zoneStatus.value = "findVictims"
        pickSequenceStatus = "goingToBall"
        timer_manager.set_timer("pickVictimCooldown", 8)

        if pickVictimType == "A" and pickedUpAliveCount.value < 2:
            pickedUpAliveCount.value += 1
        else:
            pickedUpDeadCount.value += 1

        printDebug(f"Picked up {'alive' if pickVictimType == 'A' else 'dead'} victim, new total: {pickedUpAliveCount.value + pickedUpDeadCount.value} victims", softDEBUG)
        printDebug(f"Picked up {pickedUpAliveCount.value} alive and {pickedUpDeadCount.value} dead", softDEBUG)
        printDebug(f"Ball detection data 2: {ballExists.value} {ballCenterX.value} {ballBottomY.value} {ballWidth.value} {ballType.value}", True)


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
            if cornerHeight.value >= camera_y * 0.65: # Close to Corner
                printDebug(f"Victim Dropping - Going Back 1", softDEBUG)
                dropSequenceStatus = "startReverse"
                wiggleStage = 0
                timer_manager.set_timer("zoneReverse", 0.5)
    def dropVictim():
        global dropSequenceStatus, wiggleStage
        if wiggleStage == 0:
            ballRelease(type)  # "A" Or "D" based on the victim
            printDebug("Victim Dropping - Opening Ball Storage", softDEBUG)
            wiggleStage = 1
            timer_manager.set_timer("wiggle", 0.2)  # Short delay before first wiggle

        elif wiggleStage == 1:
            setManualMotorsSpeeds(1800, 1800)  # Small forward movement
            controlMotors()
            if timer_manager.is_timer_expired("wiggle"):
                wiggleStage = 2
                timer_manager.set_timer("wiggle", 0.5)

        elif wiggleStage == 2:
            setManualMotorsSpeeds(1200, 1200)  # Small backward movement
            controlMotors()
            if timer_manager.is_timer_expired("wiggle"):
                wiggleStage = 3
                timer_manager.set_timer("wiggle", 0.2)

        elif wiggleStage == 3:
            setManualMotorsSpeeds(1800, 1800)  # Second wiggle forward
            controlMotors()
            if timer_manager.is_timer_expired("wiggle"):
                wiggleStage = 4
                timer_manager.set_timer("wiggle", 0.5)

        elif wiggleStage == 4:
            setManualMotorsSpeeds(1200, 1200)  # Small backward movement
            controlMotors()
            if timer_manager.is_timer_expired("wiggle"):
                wiggleStage = 5
                timer_manager.set_timer("wiggle", 0.2)
                printDebug("Victim Dropping - Finished Wiggle", softDEBUG)
                dropSequenceStatus = "goForward"
                timer_manager.set_timer("zoneForward", 1)
                wiggleStage = 0
            
    if dropSequenceStatus == "searchGoCorner":
        #printDebug(f"Victim Dropping - Searching for Green Evacuation Point", False)
        searchGoCorner()
    elif dropSequenceStatus == "startReverse":
        setManualMotorsSpeeds(1300, 1300)  # Go backward
        controlMotors()
        if timer_manager.is_timer_expired("zoneReverse"):
            setManualMotorsSpeeds(1000 if rotateTo == "left" else 2000, 2000 if rotateTo == "left" else 1000)
            controlMotors()
            printDebug(f"Victim Dropping - doing 180", softDEBUG)
            dropSequenceStatus = "do180"
            timer_manager.set_timer("do180", 1.5)
    elif dropSequenceStatus == "do180":
        setManualMotorsSpeeds(1000 if rotateTo == "left" else 2000, 2000 if rotateTo == "left" else 1000)
        controlMotors()
        if timer_manager.is_timer_expired("do180"):
            setManualMotorsSpeeds(1000, 1000)  # Go backward
            controlMotors()
            printDebug(f"Victim Dropping - Going Back 2", softDEBUG)
            dropSequenceStatus = "goBackwards"
            timer_manager.set_timer("zoneReverse", 2.0)
    elif dropSequenceStatus == "goBackwards":
        setManualMotorsSpeeds(1000, 1000)  # Go backward
        controlMotors()
        if timer_manager.is_timer_expired("zoneReverse"):
            setManualMotorsSpeeds(DEFAULT_STOPPED_SPEED, DEFAULT_STOPPED_SPEED)  # Stop motors
            controlMotors()
            printDebug(f"Victim Dropping - Dropping Victim", softDEBUG)
            dropSequenceStatus = "dropVictim"
            #timer_manager.set_timer("do180", 4.5)
    elif dropSequenceStatus == "dropVictim":
        dropVictim()
    elif dropSequenceStatus == "goForward":
        setManualMotorsSpeeds(1800, 1800)  # Go forward slowly
        controlMotors()
        if timer_manager.is_timer_expired("zoneForward"):
            setManualMotorsSpeeds(DEFAULT_STOPPED_SPEED, DEFAULT_STOPPED_SPEED)
            controlMotors()
            dropSequenceStatus = "finished"
    elif dropSequenceStatus == "finished":
        setManualMotorsSpeeds(DEFAULT_STOPPED_SPEED, DEFAULT_STOPPED_SPEED)  # Stop motors
        controlMotors()
        closeBallStorage()
        dropSequenceStatus = "searchGoCorner"  # Reset to searchGoCorner for next victim
        resetEvacZoneArrays.value = True
        lastDepositTime.value = time.perf_counter()

        if type == "A":
            #dumpedAliveVictims = True # Previous version
            dumpedAliveCount.value += pickedUpAliveCount.value
            printDebug(f"Finished Dropping {pickedUpAliveCount.value} Alive victims, Total Deposit {dumpedAliveCount.value + dumpedDeadCount.value}  ( {dumpedAliveCount.value} + {dumpedDeadCount.value} )", softDEBUG)
            pickedUpAliveCount.value = 0
            zoneStatus.value = "findVictims"
            
        elif type == "D":
            #dumpedDeadVictims = True
            dumpedDeadCount.value += pickedUpDeadCount.value
            printDebug(f"Finished Dropping {pickedUpDeadCount.value} Dead victims, Total Deposit {dumpedAliveCount.value + dumpedDeadCount.value}  ( {dumpedAliveCount.value} + {dumpedDeadCount.value} ) ", softDEBUG)
            pickedUpDeadCount.value = 0
            zoneStatus.value = "findVictims"
            printDebug(f"Finished Evacuation - Leaving", False) # Wrong Positioning
            printDebug(f"Finished the Evacuation Zone in {round(time.perf_counter() - zoneStartTime.value, 3)} s", False) # Wrong Positioning


def intersectionController():
    global lastTurn
    if turnDirection.value != lastTurn:
        printDebug(f"New Turn direction {turnDirection.value} {lastTurn}", DEBUG)
        
        if turnDirection.value == "uTurn":
            if timer_manager.is_timer_expired("uTurn"):
                timer_manager.set_timer("uTurn", 1.5) # Give 1.5 s for 180degree turn

        lastTurn = turnDirection.value


def gapCorrectionController(inGap, gapAngle, gapCenterX):
    global gapCorrectionStartTime

    currentTime = time.perf_counter()

    if not inGap and not gapCorrectionActive.value:
        return

    if not gapCorrectionActive.value and timer_manager.is_timer_expired("gapCooldown"):
        if inGap and abs(gapAngle) > ANGLE_THRESHOLD:
            print(f" Here 1 ")
            gapCorrectionActive.value = True
            gapCorrectionStartTime = currentTime
            lastCorrectionDirection.value = False  # Start by reversing
            gapCorrectionState.value = "Starting Gap Correction"
        else:
            if inGap:
                gapCorrectionState.value = "We were already alligned"
            else:
                gapCorrectionState.value = "Not in a gap"
    else:
        if abs(gapAngle) <= ANGLE_THRESHOLD:
            # Aligned — stop correcting and drive forward
            setManualMotorsSpeeds(DEFAULT_FORWARD_SPEED, DEFAULT_FORWARD_SPEED)
            #controlMotors() # Control in Loop
            gapCorrectionActive.value = False
            gapCorrectionState.value = "Aligned - Going Forward"
            timer_manager.set_timer("gapCooldown", 1.5)
            return

        if currentTime - gapCorrectionStartTime > GAP_CORRECTION_TIMEOUT:
            # Timed out — just go forward
            setManualMotorsSpeeds(DEFAULT_FORWARD_SPEED, DEFAULT_FORWARD_SPEED)
            #controlMotors() # Control in Loop
            gapCorrectionActive.value = False
            gapCorrectionState.value = "Align Timeout - Going Forward"
            timer_manager.set_timer("gapCooldown", 1.5)
            return

        # Still correcting — run one step
        direction = lastCorrectionDirection.value
        M1_temp, M2_temp = setMotorSpeedsAngleYAxis(gapAngle, gapCenterX, forward=direction)
        setManualMotorsSpeeds(M1_temp, M2_temp)
        #controlMotors() # Control in Loop
        if gapCenterY.value < camera_y * 0.10: # Going forward, barely no gap
            lastCorrectionDirection.value = True
        else: # Going backward, gap is on the bottom
            lastCorrectionDirection.value = False

        gapCorrectionState.value = "Correcting Gap"


def gapController():
    global inGap, lastLineDetected

    #gapCorrectionController(inGap, gapAngle.value, gapCenterX.value)

    if not lineDetected.value: # No line detected
        if lastLineDetected: # Just lost the line (last state was true)
            timer_manager.set_timer("noLine", 0.60) # Start a timer 600ms after last seeing it
        elif timer_manager.is_timer_expired("noLine"): # Timer expired
            inGap = True # Confirm gap

    else:  # Line detected
        inGap = False  # Here to reset flag
        timer_manager.set_timer("noLine", 0)  # Force timer expiration

    lastLineDetected = lineDetected.value  # Update previous state

    if inGap:
        setManualMotorsSpeeds(DEFAULT_FORWARD_SPEED, DEFAULT_FORWARD_SPEED)


def silverLineController():
    def readyToEnterZone():
        if lineDetected.value:
            return abs( 90 - abs(silverAngle.value)) < SILVER_ANGLE_THRESHOLD and abs(camera_x / 2 - silverCenterX.value) < camera_x * 0.15
        else:
            return True # Failsafe for line not detected

    silverLine = silverValue.value > 0.6
    if silverLine:
        printDebug(f"Silver Line Detected: {silverValue.value} | Entering Zone", False)
        
        if silverLineDetected.value == False and not LOPstate.value: # First Time detection
            silverLineDetected.value = True

        elif silverLineDetected.value == True and not LOPstate.value:
            if readyToEnterZone():
                objective.value = "zone"
                zoneStatus.value = "begin"
                silverValue.value = -2
            else: # not ready to enter zone -  Go back to allign
                setMotorSpeedsAngleYAxis(silverAngle.value, silverCenterX.value, forward=False)
                print(f"Silver Line not Ready to Enter Zone: {silverAngle.value} | {silverCenterX.value} | {M1} | {M2}")
    else:
        silverLineDetected.value = False


def redLineController():
    def endOfRunStop():
        if timer_manager.is_timer_expired("redLineCooldown"):
            return False
        elif redDetected.value and not timer_manager.is_timer_expired("redLine"):
            return True # Stopped for red line timer
        elif redDetected.value and timer_manager.is_timer_expired("redLine"):
            timer_manager.set_timer("redLineCooldown", 1.5)
            return False # Stopped for red line timer
        

    if redValue.value > 0.5 and not redDetected.value:
        redDetected.value = True
        timer_manager.set_timer("redLine", redLineStopTime)
        printDebug(f"Red Line Detected at {time.perf_counter()}, gonna wait {redLineStopTime}", softDEBUG)
    elif redValue.value < 0.5 and redDetected.value:
        redDetected.value = True
    else: # not red
        redDetected.value = False
    
    if endOfRunStop():
        setManualMotorsSpeeds(DEFAULT_STOPPED_SPEED, DEFAULT_STOPPED_SPEED)


def areWeStuck(): 
    return imageSimilarityAverage.value >= .95 and (timer_manager.is_timer_expired("avoidStuckCoolDown") or avoidingStuck) and not LOPstate.value and not computerOnlyDebug


def avoidStuck():
    global avoidingStuck
    if timer_manager.is_timer_expired("avoidStuck") and not avoidingStuck:
        printDebug(f"Avoiding Stuck 1st Time", True)
        timer_manager.set_timer("avoidStuck", 1.0)
        avoidingStuck = True
        avoidingStuckDebug.value = True

    elif timer_manager.is_timer_expired("avoidStuck") and avoidingStuck:
        printDebug(f"Finished Avoiding Stuck", True)
        avoidingStuck = False
        avoidingStuckDebug.value = False
        stuckDetected.value = False
        resetImageSimilarityArrays.value = True
        timer_manager.set_timer("avoidStuckCoolDown", 4)

    else:
        setManualMotorsSpeeds(1000, 1000)
        controlMotors(avoidStuck = True)


#############################################################################
#                           Robot Control Loop
#############################################################################

def controlLoop():
    global switchState, M1, M2, M1info, M2info, oldM1, oldM2, motorSpeedDiference, error_theta, error_x, errorAcc, lastError, inGap
    global pickSequenceStatus, pickVictimType, DEFAULT_FORWARD_SPEED

    sendCommandListWithConfirmation(["GR","BC", "SF,5,F", "CL", "SF,4,F", "AU", "PA", "SF,0,F", "SF,1,F", "SF,2,F", "SF,3,F", "LX,200", "RGB,255,255,255"])

    if False: # True if only testing Evac
        objective.value = "zone"
        zoneStatus.value = "begin"
        time.sleep(5)
        cameraDefault("Evacuation")
        setLights(on=False)

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
    timer_manager.add_timer("zoneForward", 0.05)
    timer_manager.add_timer("wasOnRamp", 0.05)
    timer_manager.add_timer("avoidStuck", 0.05)
    timer_manager.add_timer("avoidStuckCoolDown", 0.05)
    timer_manager.add_timer("gapCooldown", 0.05)
    timer_manager.add_timer("pickVictimCooldown", 0.05)
    timer_manager.add_timer("redLine", 0.05)
    timer_manager.add_timer("redLineCooldown", 0.05)
    time.sleep(0.1)


    # Wait for all serial initialization commands to be sent
    while commandWaitingListLength.value != 0 or len(pendingCommandsConfirmation) != 0: 
        time.sleep(0.05)
        sendSerialPendingCommandsConfirmation()
        #printConsoles(f"Waiting for command list to be empty: {commandWaitingListLength.value}")


    resetBallArrays.value = True
    resetEvacZoneArrays.value = True
    time.sleep(5 * lineDelayMS * 0.001) # wait for 5 cam loops to register

    printConsoles(f"")
    printConsoles(f"")
    printConsoles(f"-------- Robot.py: All Setup Procedures have finished. --------")
    printConsoles(f"------------------ Robot.py: Starting Loop. ------------------")
    printConsoles(f"")
    printConsoles(f"")

    counter = 0
    runStartTime.value = time.perf_counter()
    t0 = time.perf_counter()
    while not terminate.value:
        t1 = t0 + controlDelayMS * 0.001
        t0Real = time.perf_counter()

        # Loop
        updateSensorAverages()
        LoPSwitchController()
        LOPstate.value = 1 if switchState == True else 0

        if not pickingVictim.value:
            zoneStatusLoop = zoneStatus.value
        objectiveLoop = objective.value

        stuckDetected.value = areWeStuck()
        if stuckDetected.value:
            avoidStuck()


        # ----- LINE FOLLOWING ----- 
        if objectiveLoop == "follow_line":
            updateRampStateAccelOnly()
            seesawDetected.value = detectSeesaw()

            # Update Because of Ramps DEFAULT_FORWARD_SPEED
            if rampDetected.value and rampUp.value:
                DEFAULT_FORWARD_SPEED = 1850
            elif rampDetected.value and rampDown.value:
                DEFAULT_FORWARD_SPEED = 1600
                if camServoAngle != 55:
                    cameraFree(55)
            else:
                DEFAULT_FORWARD_SPEED = 1700
                if camServoAngle != 35:
                    cameraFree(35)

            if seesawDetected.value:
                timer_manager.set_timer("backwards", 1.0)
               
            intersectionController()
            setMotorsSpeeds(lineCenterX.value)

            gapController()
            silverLineController()
            redLineController()

            controlMotors()


        # ----- EVACUATION ZONE ----- 
        elif objectiveLoop == "zone":
            timeInEvacZone()
            timeAfterDeposit()

            if needToDepositAlive(zoneStatusLoop):
                zoneStatus.value = "depositGreen"
                zoneStatusLoop = "depositGreen"
            elif needToDepositDead(zoneStatusLoop):
                zoneStatus.value = "depositRed"
                zoneStatusLoop = "depositRed"
            elif readyToLeave(zoneStatusLoop):
                zoneStatus.value = "exit"
                zoneStatusLoop = "exit"

            if zoneStatusLoop == "begin":
                timer_manager.set_timer("stop", 5.0) # 5 seconds to signal that we entered
                timer_manager.set_timer("zoneEntry", 6.5) # 1.5 (5+1.5) seconds to entry the zone

                cameraDefault("Evacuation")
                setLights(on=False)

                if zoneStartTime.value == -1:
                    zoneStartTime.value = time.perf_counter()

                zoneStatus.value = "entry" # go to next Step

            elif zoneStatusLoop == "entry":
                entryZone()
            
            elif zoneStatusLoop == "findVictims":
                setManualMotorsSpeeds(1230 if rotateTo == "left" else 1750, 1750 if rotateTo == "left" else 1230)
                controlMotors()
            
                if ballExists.value:
                    zoneStatus.value = "goToBall"

            elif zoneStatusLoop == "goToBall":
                goToBall()

            elif zoneStatusLoop == "depositGreen":
                zoneDeposit("A")

            elif zoneStatusLoop == "depositRed":
                zoneDeposit("D")

            elif zoneStatusLoop == "exit":
                pass

            elif zoneStatusLoop == "finishEvacuation":
                pass
                

        CLIinterpretCommand(CLIcommandToExecute)
        CLIinterpretCommand(CLIWebSocketCommand)
        intrepretCommand()
        sendSerialPendingCommandsConfirmation()

        if len(pendingCommandsConfirmation) > 5:
            printConsoles(f"We have {len(pendingCommandsConfirmation)} pending commands: {commandWithConfirmation.value} + {pendingCommandsConfirmation}")     

        M1info = M1
        M2info = M2

        lastObjective = objective.value
        
        # Debugging
        lopOverride.value = LOPOverride
        motorOverride.value = MotorOverride
        m1MP.value = M1info
        m2MP.value = M2info
        lineBiasDebug.value = int(KP * error_x + KD * (error_x - lastError) + KI * errorAcc)
        AngBiasDebug.value = round(KP_THETA*error_theta,2)
        inGapDebug.value = inGap
        # Evac Zone
        zoneStatusLoopDebug.value = zoneStatusLoop
        pickSequenceStatusDebug.value = pickSequenceStatus
        pickingVictimDebug.value = pickingVictim.value
    

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
                f"Silver: {round(float(silverValue.value),3)} \t"
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
                f"pickVictim: {pickingVictim.value}"
                #f"Commands: {commandWaitingList}"
            )
            counter += 1
            if counter % 5 == 0:
                #printDebug(f"{debugMessage}", softDEBUG)
                pass


        while (time.perf_counter() <= t1):
            time.sleep(0.0005)

        elapsed_time = time.perf_counter() - t0Real
        if controlDelayMS * 0.001 - elapsed_time > 0:
            time.sleep(controlDelayMS * 0.001 - elapsed_time)

        loop_duration = time.perf_counter() - t0Real
        if loop_duration > 0:
            controlLoopFrequency.value = 1.0 / loop_duration
        else:
            controlLoopFrequency.value = 0  # Avoid division by zero

        printDebug(f"Control Frequency: {controlLoopFrequency.value} Hz", DEBUG)
    
        t0 = t1

    printConsoles(f"Shutting Down Robot Control Loop")