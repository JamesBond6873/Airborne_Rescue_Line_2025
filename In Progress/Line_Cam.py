# -------- Robot Actuators/Sensors -------- 

import time
import cv2
from picamera2 import Picamera2

import config
import utils
import robot

print("Line Camera: \t \t OK")


def LoPController():
    pass


def gapController():
    pass


def intersectionController():
    pass


def obstacleController():
    pass


def redLineCheck():
    pass


def silverLineCheck():
    pass


#############################################################################
#                            Line Camera Loop
#############################################################################

def lineCamLoop():
    camera = Picamera2()
    camera.start()
    time.sleep(0.1)

    t0 = time.time()
    while True:
        t1 = t0 + config.lineDelayMS * 0.001

        # Loop

        LoPController()
        
        if robot.objective == "Follow Line":
            raw_capture = camera.capture_array()
            cv2_img = cv2.cvtColor(raw_capture, cv2.COLOR_RGBA2BGR)

            hsv_image = cv2.cvtColor(cv2_img, cv2.COLOR_BGR2HSV)
            green_image = cv2.inRange(hsv_image, config.green_min, config.green_max)
            red_image = cv2.inRange(hsv_image, config.red_min_1, config.red_max_1) + cv2.inRange(hsv_image, config.red_min_2, config.red_max_2)

            # Show Images
            cv2.imshow("Camera View", cv2_img)
            cv2.imshow("HSV Image", hsv_image)

            gapController()
            intersectionController()
            obstacleController()
            redLineCheck()
            silverLineCheck()


        while (time.time() <= t1):
            time.sleep(0.001)
        t0 = t1
            