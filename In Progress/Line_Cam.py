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

camera_x = 1280
camera_y = 720


def savecv2_img(folder, cv2_img):
    if saveFrame.value:
        # Create the "fotos" directory if it doesn't exist
        folder_name = folder
        os.makedirs(folder_name, exist_ok=True)
        
        # Generate filename based on timestamp
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S-%f")[:-3]  # Remove last 3 digits for milliseconds
        file_path = os.path.join(folder_name, f"cv2_img_{timestamp}.jpg")
        
        # Save the cv2_img using OpenCV
        cv2.imwrite(file_path, cv2_img)

        printDebug(f"File path: {file_path}", config.softDEBUG)
    

def getLine():
    global cv2_img, blackcv2_img

    contoursblk, _ = cv2.findContours(blackcv2_img, cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)
    
    # No contours
    if not contoursblk:
        return lineCenterX.value, lineAngle.value
    
    largest_contour = max(contoursblk, key=cv2.contourArea)

    # Draw the largest contour
    cv2.drawContours(cv2_img, [largest_contour], -1, (0, 255, 0), 2)

    # Compute cv2_img moments for the largest contour
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
        cv2.circle(cv2_img, (cx, cy), 5, (0, 255, 255), -1)

        # Draw principal axis line
        cv2.line(cv2_img, (x1, y1), (x2, y2), (255, 0, 0), 2)

        #
        cv2.putText(cv2_img, f"{round(np.rad2deg(theta), 0)}", (1125, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

        return cx, theta
    
    else:
        return lineCenterX.value, lineAngle.value


def LoPController():
    pass


def gapController():
    pass

def check_black(black_around_sign, i, green_box):
    global blackcv2_img

    green_box = green_box[green_box[:, 1].argsort()]

    marker_height = green_box[-1][1] - green_box[0][1]

    black_around_sign[i, 4] = int(green_box[2][1])

    # Bottom
    roi_b = blackcv2_img[int(green_box[2][1]):np.minimum(int(green_box[2][1] + (marker_height * 0.8)), camera_y), np.minimum(int(green_box[2][0]), int(green_box[3][0])):np.maximum(int(green_box[2][0]), int(green_box[3][0]))]
    if roi_b.size > 0:
        if np.mean(roi_b[:]) > 125:
            black_around_sign[i, 0] = 1

    # Top
    roi_t = blackcv2_img[np.maximum(int(green_box[1][1] - (marker_height * 0.8)), 0):int(green_box[1][1]), np.minimum(np.maximum(int(green_box[0][0]), 0), np.maximum(int(green_box[1][0]), 0)):np.maximum(np.maximum(int(green_box[0][0]), 0), np.maximum(int(green_box[1][0]), 0))]
    if roi_t.size > 0:
        if np.mean(roi_t[:]) > 125:
            black_around_sign[i, 1] = 1

    green_box = green_box[green_box[:, 0].argsort()]

    # Left
    roi_l = blackcv2_img[np.minimum(int(green_box[0][1]), int(green_box[1][1])):np.maximum(int(green_box[0][1]), int(green_box[1][1])), np.maximum(int(green_box[1][0] - (marker_height * 0.8)), 0):int(green_box[1][0])]
    if roi_l.size > 0:
        if np.mean(roi_l[:]) > 125:
            black_around_sign[i, 2] = 1

    # Right
    roi_r = blackcv2_img[np.minimum(int(green_box[2][1]), int(green_box[3][1])):np.maximum(int(green_box[2][1]), int(green_box[3][1])), int(green_box[2][0]):np.minimum(int(green_box[2][0] + (marker_height * 0.8)), camera_x)]
    if roi_r.size > 0:
        if np.mean(roi_r[:]) > 125:
            black_around_sign[i, 3] = 1

    return black_around_sign


def determine_turn_direction(black_around_sign):
    turn_left = False
    turn_right = False
    left_bottom = False
    right_bottom = False

    for i in black_around_sign:
        if np.sum(i[:4]) == 2:
            if i[1] == 1 and i[2] == 1:
                turn_right = True
                if i[4] > camera_y * 0.95:
                    right_bottom = True
            elif i[1] == 1 and i[3] == 1:
                turn_left = True
                if i[4] > camera_y * 0.95:
                    left_bottom = True

    return turn_left, turn_right, left_bottom, right_bottom


def checkGreen(contours_grn):
    global cv2_img, blackcv2_img

    black_around_sign = np.zeros((len(contours_grn), 5), dtype=np.int16)  # [[b,t,l,r,lp], [b,t,l,r,lp]]

    for i, contour in enumerate(contours_grn):
        area = cv2.contourArea(contour)
        if area <= 2500:
            continue

        green_box = cv2.boxPoints(cv2.minAreaRect(contour))
        draw_box = np.intp(green_box)
        cv2.drawContours(cv2_img, [draw_box], -1, (0, 0, 255), 2)

        black_around_sign = check_black(black_around_sign, i, green_box)

    turn_left, turn_right, left_bottom, right_bottom = determine_turn_direction(black_around_sign)

    if turn_left and not turn_right and not left_bottom:
        return "left"
    elif turn_right and not turn_left and not right_bottom:
        return "right"
    elif turn_left and turn_right and not (left_bottom and right_bottom):
        return "uTurn"
    else:
        return "straight"


def onTopIntersection(contours_grn):
    global cv2_img

    closeToIntersection = onIntersection.value

    for i, contour in enumerate(contours_grn):
        area = cv2.contourArea(contour)
        if area <= 2500:
            continue

        # Compute Green Contours moments
        M = cv2.moments(contour)
        if M["m00"] != 0:
            # Centroid (First Moment)
            cx = int(M["m10"] / M["m00"])
            cy = int(M["m01"] / M["m00"])

            cv2.circle(cv2_img, (cx, cy), 5, (255, 0, 0), -1)

            if cy > 0.5 * camera_y:
                closeToIntersection = True 

    return closeToIntersection


def intersectionDetector():
    global greencv2_img, blackcv2_img
    contoursGreen, _ = cv2.findContours(greencv2_img, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)

    onIntersection.value = onTopIntersection(contoursGreen)

    if len(contoursGreen) > 0:
        turnDirection.value = checkGreen(contoursGreen)
    else:
        turnDirection.value = "straight"


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
    global cv2_img, blackcv2_img, greencv2_img, redcv2_img

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

            hsv_cv2_img = cv2.cvtColor(cv2_img, cv2.COLOR_BGR2HSV)
            greencv2_img = cv2.inRange(hsv_cv2_img, green_min, green_max)
            redcv2_img = cv2.inRange(hsv_cv2_img, red_min_1, red_max_1) + cv2.inRange(hsv_cv2_img, red_min_2, red_max_2)
            blackcv2_img = cv2.inRange(hsv_cv2_img, black_min, black_max)

            # Follow Line - Get Centroid and Line Angle            
            lineCenterX.value, lineAngle.value = getLine()

            # Deal with intersections
            intersectionDetector()

            # Show cv2_imgs
            cv2.imwrite("/home/raspberrypi/Airborne_Rescue_Line_2025/In Progress/latest_frame_cv2.jpg", cv2_img)
            cv2.imwrite("/home/raspberrypi/Airborne_Rescue_Line_2025/In Progress/latest_frame_hsv.jpg", hsv_cv2_img)
            cv2.imwrite("/home/raspberrypi/Airborne_Rescue_Line_2025/In Progress/latest_frame_green.jpg", greencv2_img)
            cv2.imwrite("/home/raspberrypi/Airborne_Rescue_Line_2025/In Progress/latest_frame_black.jpg", blackcv2_img)


            gapController()
            obstacleController()
            redLineCheck()
            silverLineCheck()

            savecv2_img("Frames", cv2_img)
            #savecv2_img("Frames", cv2_img)


        while (time.perf_counter() <= t1):
            time.sleep(0.0005)

        printDebug(f"\t\t\t\t\t\t\t\tLine Cam Loop Time: {t0} | {t1} | {time.perf_counter()}", config.DEBUG)
        t0 = t1
            