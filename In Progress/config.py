# -------- Robot Configurations -------- 

print("Robot Configurations: \t \t OK")

# Is it DEBUG?
DEBUG = True
softDEBUG = True

# Serial Port Vars
SERIAL_PORT = '/dev/ttyACM0'
BAUD_RATE = 115200

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