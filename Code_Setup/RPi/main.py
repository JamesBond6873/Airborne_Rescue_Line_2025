import pygame
import sys
import serial
import time

# Is it DEBUG?
DEBUG = False

SERIAL_PORT = '/dev/ttyACM0'
BAUD_RATE = 115200

# Constants for speed factors and motor default values
delayTimeMS = 10
MAX_DEFAULT_SPEED = 2000
MIN_DEFAULT_SPEED = 1700
SPEED_STEP = 25
FACTOR_STEP = 25
MAX_SPEED_FACTOR_LIMIT = 500
MIN_SPEED_FACTOR_LIMIT = 50

# Variables that can be updated
maxSpeedFactor = 250
reverseSpeedFactor = -100
defaultSpeed = 1850

# Motor variables
M1, M2, M3, M4 = 0, 0, 0, 0
speedFactor = 0

# Makes printDebug dependent on DEBUG flag
def printDebug(text):
    if DEBUG:
        print(text)

# Initialize Pygame and joystick
def initJoystick():
    pygame.init()
    pygame.joystick.init()
    if pygame.joystick.get_count() == 0:
        print("No joystick found!")
        pygame.quit()
        sys.exit()
    joystick = pygame.joystick.Joystick(0)
    joystick.init()
    return joystick

def initSerial():
    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
        print(f"Connected to {SERIAL_PORT} at {BAUD_RATE} baud.")
        time.sleep(2)
        
        return ser
    except serial.SerialException as e:
        print(f"Eror opening serial port: {e}")
        sys.exit()

# Function to handle joystick events and speed factor changes
def handleEvents(joystick):
    global speedFactor
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

        # Button Presses
        if event.type == pygame.JOYBUTTONDOWN:
            handleButtonPress(event.button)
        elif event.type == pygame.JOYBUTTONUP:
            handleButtonRelease(event.button)

# Handles button presses to adjust speed factor and default speed
def handleButtonPress(button):
    global speedFactor, defaultSpeed, maxSpeedFactor, reverseSpeedFactor

    printDebug(f"Button {button} pressed")
    if button == 0:
        printDebug(f"Shutting Down: Button {button} Pressed!")
        pygame.quit()
        sys.exit()
    elif button == 7:
        speedFactor = maxSpeedFactor
        printDebug(f"Speed Factor: {speedFactor}")
    elif button == 6:
        speedFactor = reverseSpeedFactor
        printDebug(f"Speed Factor: {speedFactor}")
    elif button == 5:
        # Increase default speed
        defaultSpeed = min(defaultSpeed + SPEED_STEP, MAX_DEFAULT_SPEED)
        printDebug(f"Default Speed Increased: {defaultSpeed}")
    elif button == 4:
        # Decrease default speed
        defaultSpeed = max(defaultSpeed - SPEED_STEP, MIN_DEFAULT_SPEED)
        printDebug(f"Default Speed Decreased: {defaultSpeed}")
    elif button == 1:
        # Increase both forward and reverse speed factors
        if maxSpeedFactor < MAX_SPEED_FACTOR_LIMIT:
            maxSpeedFactor += FACTOR_STEP
            reverseSpeedFactor -= FACTOR_STEP
        printDebug(f"Max/Reverse Speed Factor Increased: {maxSpeedFactor}/{reverseSpeedFactor}")
    elif button == 3:
        # Decrease both forward and reverse speed factors
        if maxSpeedFactor > MIN_SPEED_FACTOR_LIMIT:
            maxSpeedFactor -= FACTOR_STEP
            reverseSpeedFactor += FACTOR_STEP
        printDebug(f"Max/Reverse Speed Factor Decreased: {maxSpeedFactor}/{reverseSpeedFactor}")

# Handles button releases to reset speed factor
def handleButtonRelease(button):
    global speedFactor
    printDebug(f"Button {button} released")
    if button == 7 or button == 6:
        speedFactor = 0
        printDebug(f"Speed Factor: {speedFactor}")

# Function to calculate motor speeds based on joystick input
def calculateMotorSpeeds(axes):
    global M1, M2, M3, M4
    axisValue = round(axes[0], 3)
    M1 = defaultSpeed + axisValue * speedFactor
    M2 = defaultSpeed - axisValue * speedFactor
    M3 = defaultSpeed + axisValue * speedFactor
    M4 = defaultSpeed - axisValue * speedFactor

    if M1 < 1520:
        M1 = 1250 - (1520 - M1)
        M3 = 1250 - (1520 - M3)
    
    if M2 < 1550:
        M2 = 1250 - (1550 - M2)
        M4 = 1250 - (1550 - M4)
    
    if M1 > 2000:
        M1 = 2000
        M3 = 2000

    if M2 > 2000:
        M2 = 2000
        M4 = 2000

    # Handle reverse speedFactor
    if speedFactor < 0:
        M1 = 1000 + (2000 - defaultSpeed) + axisValue * abs(speedFactor)
        M2 = 1000 + (2000 - defaultSpeed) - axisValue * abs(speedFactor)
        M3 = 1000 + (2000 - defaultSpeed) + axisValue * abs(speedFactor)
        M4 = 1000 + (2000 - defaultSpeed) - axisValue * abs(speedFactor)
    
    if M1 < 1000:
        M1 = 1000
        M3 = 1000

    if M2 < 1000:
        M2 = 1000
        M4 = 1000
        

    # If speedFactor is zero, stop motors
    if speedFactor == 0:
        M1 = M2 = M3 = M4 = 1520

# Main loop for handling joystick input and updating motor speeds
def mainLoop(joystick):
    try:
        while True:
            handleEvents(joystick)

            # Read joystick axes values
            axes = [joystick.get_axis(i) for i in range(joystick.get_numaxes())]

            # Calculate motor speeds
            calculateMotorSpeeds(axes)

            # Print motor speeds for debugging
            print(f"M({M2}, {M1})")
            message = f"M({M2}, {M1})"
            ser.write(message.encode('utf-8'))
            
            print(f"Sent to Serial: {message.strip()}")
            #print(f"M1: {M1}, M2: {M2}, M3: {M3}, M4: {M4}")

            pygame.time.delay(delayTimeMS)

    except KeyboardInterrupt:
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    joystick = initJoystick()
    ser = initSerial()
    mainLoop(joystick)
