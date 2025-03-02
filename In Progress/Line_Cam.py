# -------- Robot Actuators/Sensors -------- 

import time
import cv2
import numpy as np
from picamera2 import Picamera2
from libcamera import controls

import config
import utils
import robot
from MP_Manager import *

print("Line Camera: \t \t \t OK")


# Color Configs
black_min = np.array(config.black_min)
black_max = np.array(config.black_max)
green_min = np.array(config.green_min)
green_max = np.array(config.green_max)
red_min_1 = np.array(config.red_min_1)
red_max_1 = np.array(config.red_max_1)
red_min_2 = np.array(config.red_min_2)
red_max_2 = np.array(config.red_max_2)


def get_line_center(binary_image):
    height, width = binary_image.shape
    roi = binary_image[int(height * 0.7):, :]  # Focus on the lower part of the image
    contours, _ = cv2.findContours(roi, cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)

    if contours:
        largest_contour = max(contours, key=cv2.contourArea)
        M = cv2.moments(largest_contour)
        if M["m00"] != 0:
            cx = int(M["m10"] / M["m00"])
            return cx, height - 1  # Return x position of the detected line
    return None  # No line detected


def follow_line(cx, frame_width):
    center_x = frame_width // 2
    if cx < center_x - 20:
        print("Turn Left")
    elif cx > center_x + 20:
        print("Turn Right")
    else:
        print("Move Forward")


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
    # Fix exposure to avoid automatic adjustments
    camera.set_controls({
        "ExposureTime": 500,  # Microseconds (Lower values reduce blur, try 500-2000)
        "AnalogueGain": 2.0,  # Increase brightness if necessary (1.0 to 8.0)
        "AfMode": controls.AfModeEnum.Continuous
    })
    """
    camera.configure(camera.create_video_configuration(sensor={'output_size': mode['size'], 'bit_depth': mode['bit_depth']}))
    #camera.set_controls({"AfMode": 2})  # 2 corresponds to "Auto" mode
    camera.set_controls({"AfMode": controls.AfModeEnum.Continuous})"""

    # Enable Autofocus and Adjust Exposure
    #camera.set_controls({"AfMode": controls.AfModeEnum.Continuous, "LensPosition": 2.5, "FrameDurationLimits": (1000000 // 50, 1000000 // 50)})
    #camera.set_controls({"LensPosition": 2.5, "FrameDurationLimits": (1000000 // 50, 1000000 // 50)})

    camera.start()
    time.sleep(0.1)

    t0 = time.time()
    while not terminate.value:
        t1 = t0 + config.lineDelayMS * 0.001

        # Loop

        LoPController()
        
        if robot.objective == "Follow Line":
            raw_capture = camera.capture_array()
            cv2_img = cv2.cvtColor(raw_capture, cv2.COLOR_RGBA2BGR)

            hsv_image = cv2.cvtColor(cv2_img, cv2.COLOR_BGR2HSV)
            green_image = cv2.inRange(hsv_image, green_min, green_max)
            red_image = cv2.inRange(hsv_image, red_min_1, red_max_1) + cv2.inRange(hsv_image, red_min_2, red_max_2)
            black_image = cv2.inRange(hsv_image, black_min, black_max)

            # Show Images
            cv2.imwrite("/home/raspberrypi/Airborne_Rescue_Line_2025/In Progress/latest_frame_cv2.jpg", cv2_img)
            cv2.imwrite("/home/raspberrypi/Airborne_Rescue_Line_2025/In Progress/latest_frame_hsv.jpg", hsv_image)
            cv2.imwrite("/home/raspberrypi/Airborne_Rescue_Line_2025/In Progress/latest_frame_green.jpg", green_image)
            cv2.imwrite("/home/raspberrypi/Airborne_Rescue_Line_2025/In Progress/latest_frame_black.jpg", black_image)

            # Find the line center and determine movement
            line_position = get_line_center(black_image)
            if line_position:
                cx, _ = line_position
                lineCenter.value = cx
                #follow_line(cx, cv2_img.shape[1])

            gapController()
            intersectionController()
            obstacleController()
            redLineCheck()
            silverLineCheck()


        while (time.time() <= t1):
            time.sleep(0.001)
        t0 = t1
            