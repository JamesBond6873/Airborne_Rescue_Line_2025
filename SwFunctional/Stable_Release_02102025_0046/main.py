import pygame
import sys
import serial
import time

import config
import utils
import mySerial
import robot
import gamepad


# Motor variables
M1, M2, M3, M4 = 0, 0, 0, 0


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
def mainLoop(joystick):
    oldM1 = M1
    oldM2 = M2
    t0 = time.time()
    try:
        while True:
            t1 = t0 + config.delayTimeMS * 0.001

            utils.printDebug(robot.notWaiting, config.DEBUG)

            if robot.notWaiting:
                gamepad.handleEvents(joystick)

                # Read joystick axes values
                axes = [joystick.get_axis(i) for i in range(joystick.get_numaxes())]

                # Calculate motor speeds
                calculateMotorSpeeds(axes)

                if oldM1 != M1 or oldM2 != M2:
                    message = f"M({M1}, {M2})"
                    mySerial.sendSerial(message)

            receivedMessage = mySerial.readSerial(config.DEBUG)
            if "-Nothing-" not in receivedMessage:
                print(f"Received Message: {receivedMessage}")
            if "Ok" in receivedMessage:
                print(f"Command List: {robot.commandWaitingList}")
                if len(robot.commandWaitingList) == 0:
                    robot.notWaiting = True
                else:
                    mySerial.sendSerial(robot.commandWaitingList[0])
                    robot.commandWaitingList.pop(0)

            oldM1 = M1
            oldM2 = M2

            while (time.time() <= t1):
                time.sleep(0.001)
            t0 = t1
            

    except KeyboardInterrupt:
        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    joystick = gamepad.initJoystick()
    ser = mySerial.initSerial(config.SERIAL_PORT, config.BAUD_RATE, 10, config.DEBUG) # 10 second timeout
    mainLoop(joystick)
