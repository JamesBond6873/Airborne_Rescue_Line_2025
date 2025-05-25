from gpiozero import Button
import numpy as np

import config
from utils import *
#from line_cam import camera_x, camera_y
#import mySerial
#from mp_manager import *


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
