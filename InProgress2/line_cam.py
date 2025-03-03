# -------- Robot Actuators/Sensors -------- 

import datetime
import time
import os
import cv2
import numpy as np
from picamera2 import Picamera2
from libcamera import controls

import config
import utils
from utils import printDebug
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


def saveImage(folder, cv2_img):
    if saveFrame.value:
        # Create the "fotos" directory if it doesn't exist
        folder_name = folder
        os.makedirs(folder_name, exist_ok=True)
        
        # Generate filename based on timestamp
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S-%f")[:-3]  # Remove last 3 digits for milliseconds
        file_path = os.path.join(folder_name, f"image_{timestamp}.jpg")
        
        # Save the image using OpenCV
        cv2.imwrite(file_path, cv2_img)

        printDebug(f"File path: {file_path}", config.softDEBUG)


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
    

def getLine(Image, blackImage):
    contoursblk, _ = cv2.findContours(blackImage, cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)
    
    # No contours
    if not contoursblk:
        return lineCenterX.value, lineAngle.value, Image, blackImage
    
    largest_contour = max(contoursblk, key=cv2.contourArea)

    # Draw the largest contour
    cv2.drawContours(Image, [largest_contour], -1, (0, 255, 0), 2)

    # Compute image moments for the largest contour
    M = cv2.moments(largest_contour)
    if M["m00"] != 0:
        # Centroid (First Moment)
        cx = int(M["m10"] / M["m00"])
        cy = int(M["m01"] / M["m00"])

        # Calculate orientation using central moments
        mu20 = M["mu20"] / M["m00"]
        mu02 = M["mu02"] / M["m00"]
        mu11 = M["mu11"] / M["m00"]

        theta = 0.5 * np.arctan2(2 * mu11, mu20 - mu02)  # Principal axis angle

        if theta < 0:
            printDebug(f"theta og: {round(theta,2)} {round(np.rad2deg(theta),2)}, new {round(np.pi + theta,2)} {round(np.rad2deg(np.pi + theta),2)}", config.DEBUG)
            theta = np.pi + theta

        # Define line endpoints along the principal axis
        length = 100  # Adjust for visualization
        x1 = int(cx + length * np.cos(theta))
        y1 = int(cy + length * np.sin(theta))
        x2 = int(cx - length * np.cos(theta))
        y2 = int(cy - length * np.sin(theta))

        # Draw centroid
        cv2.circle(Image, (cx, cy), 5, (0, 255, 255), -1)

        # Draw principal axis line
        cv2.line(Image, (x1, y1), (x2, y2), (255, 0, 0), 2)

        #
        cv2.putText(Image, f"{round(np.rad2deg(theta), 0)}", (1125, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

        return cx, theta, Image, blackImage
    
    else:
        return lineCenterX.value, lineAngle.value, Image, blackImage

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

    #camera.set_controls({"AfMode": controls.AfModeEnum.Manual, "ExposureTime":10000})

    # Fix exposure to avoid automatic adjustments
    """camera.set_controls({
        "ExposureTime": 5000,  # Increase from 500 to 5000 (5ms) or more
        "AnalogueGain": 4.0    # Boost brightness (increase if still too dark)
    })"""

    """
    camera.configure(camera.create_video_configuration(sensor={'output_size': mode['size'], 'bit_depth': mode['bit_depth']}))
    #camera.set_controls({"AfMode": 2})  # 2 corresponds to "Auto" mode
    camera.set_controls({"AfMode": controls.AfModeEnum.Continuous})

    # Enable Autofocus and Adjust Exposure
    #camera.set_controls({"AfMode": controls.AfModeEnum.Continuous, "LensPosition": 2.5, "FrameDurationLimits": (1000000 // 50, 1000000 // 50)})
    #camera.set_controls({"LensPosition": 2.5, "FrameDurationLimits": (1000000 // 50, 1000000 // 50)})"""

    camera.start()
    time.sleep(0.1)

    t0 = time.perf_counter()
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
            
            # Find the line center and determine movement
            """line_position = get_line_center(black_image)
            if line_position:
                cx, _ = line_position
                lineCenterX.value = cx
                # Draw centroid
                cv2.circle(cv2_img, (cx, 300), 5, (0, 255, 255), -1)"""

            
            lineCenterX.value, lineAngle.value, cv2_img, black_image = getLine(cv2_img, black_image)

            # Show Images
            cv2.imwrite("/home/raspberrypi/Airborne_Rescue_Line_2025/In Progress/latest_frame_cv2.jpg", cv2_img)
            cv2.imwrite("/home/raspberrypi/Airborne_Rescue_Line_2025/In Progress/latest_frame_hsv.jpg", hsv_image)
            cv2.imwrite("/home/raspberrypi/Airborne_Rescue_Line_2025/In Progress/latest_frame_green.jpg", green_image)
            cv2.imwrite("/home/raspberrypi/Airborne_Rescue_Line_2025/In Progress/latest_frame_black.jpg", black_image)


            gapController()
            intersectionController()
            obstacleController()
            redLineCheck()
            silverLineCheck()

            saveImage("Frames", cv2_img)
            #saveImage("Frames", cv2_img)


        while (time.perf_counter() <= t1):
            time.sleep(0.0005)

        printDebug(f"\t\t\t\t\t\t\t\tLine Cam Loop Time: {t0} | {t1} | {time.perf_counter()}", config.DEBUG)
        t0 = t1
            