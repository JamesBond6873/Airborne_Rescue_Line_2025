# -------- Robot Configurations -------- 

print("Robot Configurations: \t \t OK")

# Is it DEBUG?
silverDatasetCollectionMode = False
victimDatasetCollectionMode = False
computerOnlyDebug = False # True for computer only, False for robot
gamepadLoopRun = True # False for score runs
DEBUG = False
softDEBUG = True
serialSoftDEBUG = True #True
pickVictimSoftDEBUG = True
LOPOverride = False # If True, LOP state will be updated virtually
LOPVirtualState = True
MotorOverride = False # If True, the robot will not move

# Camera Angle variables
CAMERA_LINE_ANGLE = 30
CAMERA_EVAC_ZONE_ANGLE = 70

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
dataRequestDelayMS = 50 # 20 Hz
intersectionMaxTime = 1.000 #s

# Line Vars
redLineStopTime = 9.0 # s
default_crop=0.45
turn_crop=0.75
SILVER_ANGLE_THRESHOLD = 90
SILVER_CENTER_THRESHOLD = 0.20
SILVER_CLOSE_THRESHOLD = 0.40
GAP_CORRECTION_TIMEOUT = 5 # s
ANGLE_THRESHOLD = 10.0  # degrees
SEESAW_RATE_THRESHOLD = 85 # degrees per second - Requires calibration
ROBOT_CLOSE_TO_WALL_DISTANCE = 150 # mm
PARALLEL_TOF_THRESHOLD = 65 # mm
OPENING_THRESHOLD_SIDE = 300  # mm
OPENING_THRESHOLD_FRONT = 1000  # mm
# Constants for gap correction state
GAP_IDLE = 0
GAP_CORRECTING = 1
GAP_ALIGNED = 2
GAP_TIMEOUT = 3

# Color Configs
blackThreshold = 55
black_top_threshold_percentage = 0.4
black_min = [0, 0, 0]
black_max_normal_top = [82, 83, 30]
black_max_normal_bottom = [180, 90, 50]
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
DEFAULT_BACKWARD_SPEED = 1200
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
KP = 1.5 #1.50
KD = 2.0 #2.05
KI = 0.0
KP_THETA = 140 # 407 = 1280/3.1415
Kp_distance = 2.3 # Kp for exiting the evac zone
Kp_angle = 1.2 # Kp for exiting the evac zone angle to the wall