# -------- Robot Actuators/Sensors -------- 

import time
import cv2
import numpy as np
from picamera2 import Picamera2
from libcamera import controls

import config
import utils
import robot

print("Line Camera: \t \t OK")


# Color Configs
green_min = np.array(config.green_min)
green_max = np.array(config.green_max)
red_min_1 = np.array(config.red_min_1)
red_max_1 = np.array(config.red_max_1)
red_min_2 = np.array(config.red_min_2)
red_max_2 = np.array(config.red_max_2)


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
    camera = Picamera2(0)

    mode = camera.sensor_modes[0]
    camera.configure(camera.create_video_configuration(sensor={'output_size': mode['size'], 'bit_depth': mode['bit_depth']}))

    # Enable Autofocus and Adjust Exposure
    #camera.set_controls({"AfMode": controls.AfModeEnum.Continuous, "LensPosition": 2.5, "FrameDurationLimits": (1000000 // 50, 1000000 // 50)})
    #camera.set_controls({"LensPosition": 2.5, "FrameDurationLimits": (1000000 // 50, 1000000 // 50)})

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
            green_image = cv2.inRange(hsv_image, green_min, green_max)
            red_image = cv2.inRange(hsv_image, red_min_1, red_max_1) + cv2.inRange(hsv_image, red_min_2, red_max_2)

            # Show Images
            cv2.imwrite("/home/raspberrypi/Airborne_Rescue_Line_2025/In Progress/latest_frame_cv2.jpg", cv2_img)
            cv2.imwrite("/home/raspberrypi/Airborne_Rescue_Line_2025/In Progress/latest_frame_hsv.jpg", hsv_image)

            gapController()
            intersectionController()
            obstacleController()
            redLineCheck()
            silverLineCheck()


        while (time.time() <= t1):
            time.sleep(0.001)
        t0 = t1
            