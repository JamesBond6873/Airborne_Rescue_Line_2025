# -------- Robot Configurations -------- 

print("Robot Configurations: \t \t OK")

# Is it DEBUG?
computerOnlyDebug = True # True for computer only, False for robot
gamepadLoopRun = True # False for score runs
DEBUG = False
softDEBUG = True
serialSoftDEBUG = False
LOPOverride = False # If True, LOP state will be updated virtually
LOPVirtualState = True
MotorOverride = False # If True, the robot will not move

# Serial Port Vars
SERIAL_PORT = '/dev/ttyACM0'
BAUD_RATE = 115200

# Buzzer Delay
buzzerONMs = 100
buzzerOffMs = 5000
buzzerState = False

# Time Delays
lineDelayMS = 25 # Frame Rate = 40 FPS
controlDelayMS = 25 # 40 Hz
serialDelayMS = 10 # 100 Hz
dataRequestDelayMS = 25 # 25 ms
intersectionMaxTime = 1.000 #s

# Color Configs
blackThreshold = 55
#green_min = [50, 95, 40]    # 58, 95, 39 Night | 126, 94, 145 Day
#green_max = [100, 255, 255] # 98, 255, 255 Night | 155, 130, 180 Day
green_min = [50, 120, 70] # 50, 95, 40 # 40, 75, 35
green_max = [100,255,200] # 100, 255, 255 # 90, 255, 145
red_min_1 = [0, 100, 90]
red_max_1 = [10, 255, 255]
red_min_2 = [170, 100, 100]
red_max_2 = [180, 255, 255]

evacZoneGreenMin = [15, 100, 15]
evacZoneGreenMax = [90, 200, 105]
evacZoneRedMin_1 = [0, 100, 90]
evacZoneRedMax_1 = [10, 255, 255]
evacZoneRedMin_2 = [170, 100, 100]
evacZoneRedMax_2 = [180, 255, 255]

# Constants for speed factors and motor default values
delayTimeMS = 10
MAX_DEFAULT_SPEED = 2000
MIN_DEFAULT_SPEED = 1600 # Gamepad only?!
MIN_GENERAL_SPEED = 1000
DEFAULT_STOPPED_SPEED = 1520
DEFAULT_FORWARD_SPEED = 1700
ESC_DEADZONE = 50
SPEED_STEP = 25
FACTOR_STEP = 25
MAX_SPEED_FACTOR_LIMIT = 500
MIN_SPEED_FACTOR_LIMIT = 50

# Variables that can be updated
maxSpeedFactor = 250
reverseSpeedFactor = -100
defaultSpeed = 1850

# Motor Vars
speedFactor = 0
KP = 1.70 #1.50
KD = 2.05 #2.05
KI = 0
KP_THETA = 250 # 407 = 1280/3.14159