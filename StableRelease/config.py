# -------- Robot Configurations -------- 

print("Robot Configurations: \t \t OK")

# Is it DEBUG?
DEBUG = False
softDEBUG = True

# Serial Port Vars
SERIAL_PORT = '/dev/ttyACM0'
BAUD_RATE = 115200

# Buzzer Delay
buzzerONMs = 100
buzzerOffMs = 5000
buzzerState = False

# Time Delays
lineDelayMS = 25 # Frame Rate = 40 FPS
controlDelayMS = 20 # 50 Hz

intersectionMaxTime = 1.000 #s

# Color Configs
black_min = [0, 0, 0] # 82 83 84
black_max = [255, 255, 130] # 133 133 135
#black_min = 0
#black_max = 80

#green_min = [50, 95, 40]    # 58, 95, 39 Night | 126, 94, 145 Day
#green_max = [100, 255, 255] # 98, 255, 255 Night | 155, 130, 180 Day
green_min = [40, 75, 35] # 50, 95, 40
green_max = [90, 255, 145] # 100, 255, 255
red_min_1 = [0, 100, 90]
red_max_1 = [10, 255, 255]
red_min_2 = [170, 100, 100]
red_max_2 = [180, 255, 255]

# Constants for speed factors and motor default values
delayTimeMS = 10
MAX_DEFAULT_SPEED = 2000
MIN_DEFAULT_SPEED = 1600 # Gamepad only?!
MIN_GENERAL_SPEED = 1000
DEFAULT_STOPPED_SPEED = 1520
DEFAULT_FORWARD_SPEED = 1750
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
KP = 2.50 #1.50
KD = 2.80 #2.05
KI = 0
KP_THETA = 250 # 407 = 1280/3.14159