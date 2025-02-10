# -------- GamePad Interface -------- 

import pygame
import sys

import utils
import config
import robot

print("GamePad Interface: \t \t OK")

# Gamepad Vars
button0Pressed = False
button2Pressed = False

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
    global button0Pressed, button2Pressed
    # Global maxSpeedFactor config.defaultSpeed  config.reverseSpeedFactor speedFactor

    utils.printDebug(f"Button {button} pressed", config.DEBUG)

    if button == 8: # Select Quits Code
        utils.printDebug(f"Shutting Down: Button {button} Pressed!", config.softDEBUG)
        pygame.quit()
        sys.exit()
    elif button == 7:
        config.speedFactor = config.maxSpeedFactor
        utils.printDebug(f"Speed Factor: {config.speedFactor}", config.DEBUG)
    elif button == 6:
        config.speedFactor = config.reverseSpeedFactor
        utils.printDebug(f"Speed Factor: {config.speedFactor}", config.DEBUG)
    elif button == 5:
        # Increase default speed
        config.defaultSpeed = min(config.defaultSpeed + config.SPEED_STEP, config.MAX_DEFAULT_SPEED)
        utils.printDebug(f"Default Speed Increased: {config.defaultSpeed}", config.DEBUG)
    elif button == 4:
        # Decrease default speed
        config.defaultSpeed = max(config.defaultSpeed - config.SPEED_STEP, config.MIN_DEFAULT_SPEED)
        utils.printDebug(f"Default Speed Decreased: {config.defaultSpeed}", config.DEBUG)
    elif button == 1:
        if button0Pressed:
            robot.pickVictim("A")
            #time.sleep(2)
        elif button2Pressed:
            robot.ballRelease("A")
            #time.sleep(2)
        # Increase both forward and reverse speed factors
        if config.maxSpeedFactor < config.MAX_SPEED_FACTOR_LIMIT:
            config.maxSpeedFactor += config.FACTOR_STEP
            config.reverseSpeedFactor -= config.FACTOR_STEP
        utils.printDebug(f"Max/Reverse Speed Factor Increased: {config.maxSpeedFactor}/{config.reverseSpeedFactor}", config.DEBUG)
    elif button == 3:
        if button0Pressed:
            robot.pickVictim("D")
            #time.sleep(2)
        elif button2Pressed:
            robot.ballRelease("D")
            #time.sleep(2)
        # Decrease both forward and reverse speed factors
        elif config.maxSpeedFactor > config.MIN_SPEED_FACTOR_LIMIT:
            config.maxSpeedFactor -= config.FACTOR_STEP
            config.reverseSpeedFactor += config.FACTOR_STEP
        utils.printDebug(f"Max/Reverse Speed Factor Decreased: {config.maxSpeedFactor}/{config.reverseSpeedFactor}", config.DEBUG)
    elif button == 0: # /_\ button
        # Pick Motions
        button0Pressed = True
        if button2Pressed:
            robot.closeBallStorage()
            #time.sleep(2)
    elif button == 2: # X
        # Drop Ball Storage
        button2Pressed = True


# Handles button releases to reset speed factor
def handleButtonRelease(button):
    global speedFactor, button0Pressed, button2Pressed
    utils.printDebug(f"Button {button} released", config.DEBUG)
    if button == 7 or button == 6:
        config.speedFactor = 0
        utils.printDebug(f"Speed Factor: {speedFactor}", config.DEBUG)
    elif button == 0: # /_\ button
        # Pick Motions
        button0Pressed = False
    elif button == 2: # X
        # Drop Ball Storage
        button2Pressed = False