# -------- GamePad Interface -------- 
import sys
import pygame
import time
from gpiozero import Button, Buzzer

import utils
import config
import mySerial
import robot


print("GamePad Interface: \t \t OK")

# Gamepad Vars
button0Pressed = False
button3Pressed = False
button2Pressed = False

# Pin Definitions
SWITCH_PIN = 14
BUZZER_PIN = 15

# Initialize components
switch = Button(SWITCH_PIN, pull_up=True)  # Uses internal pull-up
buzzer = Buzzer(BUZZER_PIN)

# Motor variables
M1, M2, M3, M4 = 0, 0, 0, 0


def is_switch_on():
    """Returns True if the switch is ON, False otherwise."""
    return switch.is_pressed


def buzzer_on():
    """Turns the buzzer on."""
    buzzer.on()


def buzzer_off():
    """Turns the buzzer off."""
    buzzer.off()


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
    global button0Pressed, button2Pressed, button3Pressed
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
        button3Pressed = True
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
        elif button3Pressed:
            robot.cameraDefault("Evacuation")
    elif button == 2: # X
        # Drop Ball Storage
        button2Pressed = True
        if button3Pressed:
            robot.cameraDefault("Line")


# Handles button releases to reset speed factor
def handleButtonRelease(button):
    global button0Pressed, button2Pressed, button3Pressed
    utils.printDebug(f"Button {button} released", config.DEBUG)

    if button == 7 or button == 6:
        config.speedFactor = 0
        utils.printDebug(f"Speed Factor: {config.speedFactor}", config.DEBUG)
    
    elif button == 0: # /_\ button  --  Pick Motions
        button0Pressed = False
    
    elif button == 2: # X  --  Drop Ball Storage
        button2Pressed = False
    
    elif button == 3: # X  --  Drop Ball Storage
        button3Pressed = False


# Function to calculate motor speeds based on joystick input
def calculateMotorSpeeds(axes):
    global M1, M2, M3, M4
    axisValue = round(axes[0], 3)
    M1 = config.defaultSpeed + axisValue * config.speedFactor
    M2 = config.defaultSpeed - axisValue * config.speedFactor
    M3 = config.defaultSpeed + axisValue * config.speedFactor
    M4 = config.defaultSpeed - axisValue * config.speedFactor

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
    if config.speedFactor < 0:
        M1 = 1000 + (2000 - config.defaultSpeed) + axisValue * abs(config.speedFactor)
        M2 = 1000 + (2000 - config.defaultSpeed) - axisValue * abs(config.speedFactor)
        M3 = 1000 + (2000 - config.defaultSpeed) + axisValue * abs(config.speedFactor)
        M4 = 1000 + (2000 - config.defaultSpeed) - axisValue * abs(config.speedFactor)
    
    if M1 < 1000:
        M1 = 1000
        M3 = 1000

    if M2 < 1000:
        M2 = 1000
        M4 = 1000
        

    # If speedFactor is zero, stop motors
    if config.speedFactor == 0:
        M1 = M2 = M3 = M4 = 1520


# Main loop for handling joystick input and updating motor speeds
def gamepadLoop():
    oldM1 = M1
    oldM2 = M2

    joystick = initJoystick()
    robot.sendCommandList(["GR","BC", "SF,5,F", "CL", "SF,4,F"])

    t0 = time.time()
    try:
        while True:
            t1 = t0 + config.delayTimeMS * 0.001

            utils.printDebug(robot.notWaiting, config.DEBUG)

            if is_switch_on():
                print("Switch is ON")

            if robot.notWaiting:
                handleEvents(joystick)

                # Read joystick axes values
                axes = [joystick.get_axis(i) for i in range(joystick.get_numaxes())]

                # Calculate motor speeds
                calculateMotorSpeeds(axes)

                if oldM1 != M1 or oldM2 != M2:
                    message = f"M({M1}, {M2})"
                    mySerial.sendSerial(message)

            receivedMessage = mySerial.readSerial(config.DEBUG)
            robot.interpretMessage(receivedMessage)

            oldM1 = M1
            oldM2 = M2

            while (time.time() <= t1):
                time.sleep(0.001)
            t0 = t1
            

    except KeyboardInterrupt:
        pygame.quit()
        sys.exit()
