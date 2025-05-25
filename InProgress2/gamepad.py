# -------- GamePad Interface -------- 
import sys
import pygame
import time

import utils
from config import *
from mp_manager import *


print("GamePad Interface: \t \t OK")

# Loop var
loop = True

# Gamepad Vars
button0Pressed = False
button1Pressed = False
button2Pressed = False
button3Pressed = False

# Motor variables
M1, M2, M3, M4 = 0, 0, 0, 0


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


# Function to handle joystick events and speed factor changes
def handleEvents(joystick):
    global speedFactor, loop
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            loop = False
            pygame.quit()
            sys.exit()

        # Button Presses
        if event.type == pygame.JOYBUTTONDOWN:
            handleButtonPress(event.button)
        elif event.type == pygame.JOYBUTTONUP:
            handleButtonRelease(event.button)


# Handles button presses to adjust speed factor and default speed
def handleButtonPress(button):
    global button0Pressed, button1Pressed, button2Pressed, button3Pressed, speedFactor, maxSpeedFactor, reverseSpeedFactor, defaultSpeed

    utils.printDebug(f"Button {button} pressed", DEBUG)

    if button == 8: # Select Quits Code
        utils.printDebug(f"Shutting Down: Button {button} Pressed!", softDEBUG)
        terminate.value = True
        pygame.quit()
        sys.exit()
    elif button == 7:
        speedFactor = maxSpeedFactor
        utils.printDebug(f"Speed Factor: {speedFactor}", DEBUG)
    elif button == 6:
        speedFactor = reverseSpeedFactor
        utils.printDebug(f"Speed Factor: {speedFactor}", DEBUG)
    elif button == 5:
        # Increase default speed
        defaultSpeed = min(defaultSpeed + SPEED_STEP, MAX_DEFAULT_SPEED)
        utils.printDebug(f"Default Speed Increased: {defaultSpeed}", DEBUG)
    elif button == 4:
        # Decrease default speed
        defaultSpeed = max(defaultSpeed - SPEED_STEP, MIN_DEFAULT_SPEED)
        utils.printDebug(f"Default Speed Decreased: {defaultSpeed}", DEBUG)
    elif button == 1:
        button1Pressed = True
        saveFrame.value = not saveFrame.value
        #utils.printDebug(f"Save Frame is now set to: {saveFrame.value}", softDEBUG)
        pass
        if button0Pressed and button1Pressed and button2Pressed and button3Pressed:
            saveFrame.value = not saveFrame.value
            utils.printDebug(f"Save Frame is now set to: {saveFrame.value}", softDEBUG)

        elif button0Pressed:
            commandToExecute.value = "Pick Alive"
            #print(f"Pick Alive -- Gamepad")
        elif button2Pressed:
            commandToExecute.value = "Drop Alive"
        
        # Increase both forward and reverse speed factors
        if maxSpeedFactor < MAX_SPEED_FACTOR_LIMIT:
            maxSpeedFactor += FACTOR_STEP
            reverseSpeedFactor -= FACTOR_STEP
        utils.printDebug(f"Max/Reverse Speed Factor Increased: {maxSpeedFactor}/{reverseSpeedFactor}", DEBUG)
    
    elif button == 3:
        button3Pressed = True
        if button0Pressed and button1Pressed and button2Pressed and button3Pressed:
            saveFrame.value = not saveFrame.value
            utils.printDebug(f"Save Frame is now set to: {saveFrame.value}", softDEBUG)

        elif button0Pressed:
            commandToExecute.value = "Pick Dead"
            #print(f"Pick Dead -- Gamepad")
        elif button2Pressed:
            commandToExecute.value = "Drop Dead"

        # Decrease both forward and reverse speed factors
        elif maxSpeedFactor > MIN_SPEED_FACTOR_LIMIT:
            maxSpeedFactor -= FACTOR_STEP
            reverseSpeedFactor += FACTOR_STEP
        utils.printDebug(f"Max/Reverse Speed Factor Decreased: {maxSpeedFactor}/{reverseSpeedFactor}", DEBUG)
    
    elif button == 0: # /_\ button
        # Pick Motions
        button0Pressed = True
        if button0Pressed and button1Pressed and button2Pressed and button3Pressed:
            saveFrame.value = not saveFrame.value
            utils.printDebug(f"Save Frame is now set to: {saveFrame.value}", softDEBUG)
        elif button2Pressed:
            commandToExecute.value = "Close Ball Storage"
        elif button3Pressed:
            commandToExecute.value = "Camera Evacuation"
    
    elif button == 2: # X
        # Drop Ball Storage
        button2Pressed = True
        if button0Pressed and button1Pressed and button2Pressed and button3Pressed:
            saveFrame.value = not saveFrame.value
            utils.printDebug(f"Save Frame is now set to: {saveFrame.value}", softDEBUG)
        elif button3Pressed:
            commandToExecute.value = "Camera Line"


# Handles button releases to reset speed factor
def handleButtonRelease(button):
    global button0Pressed, button1Pressed, button2Pressed, button3Pressed, speedFactor
    utils.printDebug(f"Button {button} released", DEBUG)

    if button == 7 or button == 6:
        speedFactor = 0
        utils.printDebug(f"Speed Factor: {speedFactor}", DEBUG)
    
    elif button == 0: # /_\ button  --  Pick Motions
        button0Pressed = False
    
    elif button == 1:
        button1Pressed = False

    elif button == 2: # X  --  Drop Ball Storage
        button2Pressed = False
    
    elif button == 3: # X  --  Drop Ball Storage
        button3Pressed = False


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
def gamepadLoop():
    global button0Pressed, button1Pressed, button2Pressed, button3Pressed
    joystick = initJoystick()

    t0 = time.time()
    try:
        while not terminate.value and loop and gamepadLoopRun:
            t1 = t0 + delayTimeMS * 0.001

            handleEvents(joystick)

            # Read joystick axes values
            axes = [joystick.get_axis(i) for i in range(joystick.get_numaxes())]

            # Calculate motor speeds
            calculateMotorSpeeds(axes)

            gamepadM1.value = M1
            gamepadM2.value = M2

            while (time.time() <= t1):
                time.sleep(0.001)
            t0 = t1

        print(f"Shutting Down Gamepad Loop")  

    except KeyboardInterrupt:
        terminate.value = True
        print(f"Shutting Down")
        pygame.quit()
        #sys.exit()
