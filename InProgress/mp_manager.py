import time
import numpy as np
from multiprocessing import Manager

print("MultiProcessing Manager: \t OK")


manager = Manager()

terminate = manager.Value("i", False)
updateFakeCamImage = manager.Value("i", True)
runStartTime = manager.Value("i", -1)
zoneStartTime = manager.Value("i", -1)

commandWithConfirmation = manager.Value("i", "none")
commandWithoutConfirmation = manager.Value("i", "none")
commandWaitingListLength = manager.Value("i", -1)

gamepadM1 = manager.Value("i", 1520)
gamepadM2 = manager.Value("i", 1520)
commandToExecute = manager.Value("i", "none") #"none",""
CLIcommandToExecute = manager.Value("i", "none")
CLIWebSocketCommand = manager.Value("i", "none")
consoleLines = manager.list()
consoleLines.append("Sensor timeout!")


# Sensor Data
newSensorData = manager.Value("i", False)

Accel_X = manager.Value("i", -1)
Accel_Y = manager.Value("i", -1)
Accel_Z = manager.Value("i", -1)

Gyro_X = manager.Value("i", -1)
Gyro_Y = manager.Value("i", -1)
Gyro_Z = manager.Value("i", -1)

Mag_X = manager.Value("i", -1)
Mag_Y = manager.Value("i", -1)
Mag_Z = manager.Value("i", -1)

Temp = manager.Value("i", -1)

Tof_1 = manager.Value("i", -1) # Back Right Side
Tof_2 = manager.Value("i", -1) # Front Right Side
Tof_3 = manager.Value("i", -1) # Front
Tof_4 = manager.Value("i", -1) # Front Left Side
Tof_5 = manager.Value("i", -1) # Back Left Side


lineStatus = manager.Value("i", "line_detected")  # "line_detected"; "gap_detected"; "gap_avoid"; "obstacle_detected"; "obstacle_avoid"; "obstacle_orientate"; "check_silver"; "position_entry"; "position_entry_1"; "position_entry_2"; "stop"
lineCenterX = manager.Value("i", 224)
lineAngle = manager.Value("i", 0.)
line_angle_y = manager.Value("i", -1)
lineDetected = manager.Value("i", False)
turnReason = manager.Value("i", 0)
redDetected = manager.Value("i", False)
silverValue = manager.Value("i", 0) # 0 = Line, 1 = Silver
silverLineDetected = manager.Value("i", False)
silverAngle = manager.Value("i", 0)
silverCenterX = manager.Value("i", 0)
silverCenterY = manager.Value("i", 0)
gapAngle = manager.Value("i", 0)
gapCenterX = manager.Value("i", 0)
gapCenterY = manager.Value("i", 0)
gapCorrectionActive = manager.Value('b', False)
lastCorrectionDirection = manager.Value('b', False)  # False = backward, True = forward
gapCorrectionState = manager.Value('i', 0)
gapState = manager.Value("i", "Not_Started")

rampDetected = manager.Value("i", False)
rampUp = manager.Value("i", False)
rampDown = manager.Value("i", False)
wasOnRamp = manager.Value("i", False)

ballCenterX = manager.Value("i", -1) # Average
ballBottomY = manager.Value("i", -1) # Average
ballWidth = manager.Value("i", -1) # Average
ballType = manager.Value("i", "none") # Average # "none"; "silver ball"; "black ball"
ballExists = manager.Value("i", False) # Average
resetBallArrays = manager.Value("i", False) # Reset the ball arrays
resetEvacZoneArrays = manager.Value("i", False) # Reset the Evacuation Zone Corener Vars
ballConfidence = manager.Value("i", -1)
pickedUpAliveCount = manager.Value("i", 0)
pickedUpDeadCount = manager.Value("i", 0)
dumpedAliveCount = manager.Value("i", 0)
dumpedDeadCount = manager.Value("i", 0)
cornerCenter = manager.Value("i", -181)
cornerHeight = manager.Value("i", 0)
zoneFoundGreen = manager.Value("i", False)
zoneFoundRed = manager.Value("i", False)

imageSimilarityAverage = manager.Value("i", -1)
stuckDetected = manager.Value("i", False)
resetImageSimilarityArrays = manager.Value("i", False)
isCropped = manager.Value("i", False)
lineCropPercentage = manager.Value("i", 0.6)
onIntersection = manager.Value("i", False)
turnDirection = manager.Value("i", "straight") # "straight", "left", "right", "uTurn"
objective = manager.Value("i", "follow_line")  # "follow_line"; "zone"; "debug"
zoneStatus = manager.Value("i", "notStarted")  # "notStarted"; "begin"; "entry"; "findVictims"; "pickup_ball"; "deposit_red"; "deposit_green"; "exit"; finished
# WARNING -- SHOULD BE NOT STARTED
LOPstate = manager.Value("i", 0)


status = manager.Value("i", "Stopped")
saveFrame = manager.Value("i", False)


# Only for Debugging Purposes
lopOverride = manager.Value("i", 0)
lopCounter = manager.Value("i", 0)
motorOverride = manager.Value("i", 0)
m1MP = manager.Value("i", 1500)
m2MP = manager.Value("i", 1500)
lineBiasDebug = manager.Value("i", -1)
AngBiasDebug = manager.Value("i", -1)
lineAngleNormalizedDebug = manager.Value("i", -1)
motorSpeedDiferenceDebug = manager.Value("i", -1)
inGapDebug = manager.Value("i", False)
markerToHighDebug = manager.Value("i", False)
zoneStatusLoopDebug = manager.Value("i", "notStarted")
pickSequenceStatusDebug = manager.Value("i", "goingToBall")
pickingVictimDebug = manager.Value("i", False)
AccelXArrayDebug = manager.Value("i", -1)
AccelYArrayDebug = manager.Value("i", -1)
AccelZArrayDebug = manager.Value("i", -1)
GyroXArrayDebug = manager.Value("i", -1)
GyroYArrayDebug = manager.Value("i", -1)
GyroZArrayDebug = manager.Value("i", -1)
TempArrayDebug = manager.Value("i", -1)
Tof1ArrayDebug = manager.Value("i", -1)
Tof2ArrayDebug = manager.Value("i", -1)
Tof3ArrayDebug = manager.Value("i", -1)
Tof4ArrayDebug = manager.Value("i", -1)
Tof5ArrayDebug = manager.Value("i", -1)
pitchDebug = manager.Value("i", -1)
silverValueDebug = manager.Value("i", -1)
silverValueArrayDebug = manager.Value("i", -1)
avoidingStuckDebug = manager.Value("i", False)

# ARRAY FUNCTIONS
def createEmptyTimeArray(length: int = 240):
    """ Create a new empty time-value array of given length. Each row: [timestamp, value] """
    return np.zeros((length, 2))


def createFilledArray(value: int, length: int = 240, fill_time: int = 0):
    """ Create a time-value array filled with an initial value. 
    From fillTime index onward, timestamps are set to current time. """
    arr = np.zeros((length, 2))
    arr[fill_time:, 0] = time.perf_counter()
    arr[:, 1] = value
    return arr


def addNewTimeValue(time_value_array, value):
    """ Add a new [current_time, value] pair to the timeArray. """
    return np.delete(np.vstack((time_value_array, [time.perf_counter(), value])), 0, axis=0)


def calculateAverageArray(time_value_array, time_range):
    """ Calculate the average of values within the last 'timeRange' seconds. """
    time_value_array = time_value_array[np.where(time_value_array[:, 0] > time.perf_counter() - time_range)]
    if time_value_array.size > 0:
        return np.mean(time_value_array[:, 1])
    else:
        return -1 # Returns -1 if no values found.


def getMaximumArray(time_value_array, time_range):
    """ Get the maximum value within the last 'timeRange' seconds. """
    time_value_array = time_value_array[np.where(time_value_array[:, 0] > time.perf_counter() - time_range)]
    return np.max(time_value_array[:, 1])