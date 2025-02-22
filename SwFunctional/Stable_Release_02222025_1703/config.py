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
lineDelayMS = 50 # Frame Rate = 20
controlDelayMS = 10 # 100 Hz

# Color Configs
black_min = [0, 0, 0] # 82 83 84
black_max = [133, 243, 105] # 133 133 135
green_min = [58, 95, 39]
green_max = [98, 255, 255]
red_min_1 = [0, 100, 90]
red_max_1 = [10, 255, 255]
red_min_2 = [170, 100, 100]
red_max_2 = [180, 255, 255]

# Constants for speed factors and motor default values
delayTimeMS = 10
MAX_DEFAULT_SPEED = 2000
MIN_DEFAULT_SPEED = 1600
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