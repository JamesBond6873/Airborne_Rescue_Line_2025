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
from mp_manager import *

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
    global cv2_img, blackImage

    contoursblk, _ = cv2.findContours(blackImage, cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)
    
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


def getLineAndCrop(contours_blk):
    global cv2_img, x_last, y_last

    candidates = np.zeros((len(contours_blk), 5), dtype=np.int32)
    off_bottom = 0

    for i, contour in enumerate(contours_blk):
        box = cv2.boxPoints(cv2.minAreaRect(contour))
        box = box[box[:, 1].argsort()[::-1]]  # Sort them by their y values and reverse
        bottom_y = box[0][1]
        y_mean = (np.clip(box[0][1], 0, camera_y) + np.clip(box[3][1], 0, camera_y)) / 2

        if box[0][1] >= (camera_y * 0.75):
            off_bottom += 1

        box = box[box[:, 0].argsort()]
        x_mean = (np.clip(box[0][0], 0, camera_x) + np.clip(box[3][0], 0, camera_x)) / 2
        x_y_distance = abs(x_last - x_mean) + abs(y_last - y_mean)  # Distance between the last x/y and current x/y

        candidates[i] = i, bottom_y, x_y_distance, x_mean, y_mean

    if off_bottom < 2:
        candidates = candidates[candidates[:, 1].argsort()[::-1]]  # Sort candidates by their bottom_y
    else:
        off_bottom_candidates = candidates[np.where(candidates[:, 1] >= (camera_y * 0.75))]
        candidates = off_bottom_candidates[off_bottom_candidates[:, 2].argsort()]

    if turnDirection.value == "left":
        x_last = np.clip(candidates[0][3] - 150, 0, camera_x)
    elif turnDirection.value == "right":
        x_last = np.clip(candidates[0][3] + 150, 0, camera_x)
    else:
        x_last = candidates[0][3]

    y_last = candidates[0][4]
    blackline = contours_blk[candidates[0][0]]
    blackline_crop = blackline[np.where(blackline[:, 0, 1] > camera_y * lineCropPercentage.value)]

    cv2.drawContours(cv2_img, blackline, -1, (255, 0, 0), 2)
    cv2.drawContours(cv2_img, blackline_crop, -1, (255, 255, 0), 2)

    cv2.circle(cv2_img, (int(x_last), int(y_last)), 3, (0, 0, 255), -1)

    return blackline, blackline_crop


def calculatePointsOfInterest(blackline, blackline_crop, last_bottom_point, average_line_point):
    max_gap = 1
    max_line_width = camera_x * .19

    poi_no_crop = np.zeros((4, 2), dtype=np.int32)  # [t, l, r, b]

    # Top without crop
    blackline_y_min = np.amin(blackline[:, :, 1])
    blackline_top = blackline[np.where(blackline[:, 0, 1] == blackline_y_min)][:, :, 0]

    blackline_top = blackline_top[blackline_top[:, 0].argsort()]
    blackline_top_gap_fill = (blackline_top + max_gap + 1)[:-1]

    blackline_gap_mask = blackline_top_gap_fill < blackline_top[1:]

    top_mean = (int(np.mean(blackline_top)), blackline_y_min)

    if np.sum(blackline_gap_mask) == 1:
        gap_index = np.where(blackline_gap_mask)[0][0]

        if blackline_top[:gap_index].size > 0 and blackline_top[gap_index:].size > 0:
            top_mean_l = int(np.mean(blackline_top[:gap_index]))
            top_mean_r = int(np.mean(blackline_top[gap_index:]))

            top_mean = (top_mean_l, blackline_y_min) if np.abs(top_mean_l - average_line_point) < np.abs(top_mean_r - average_line_point) else (top_mean_r, blackline_y_min)

    poi_no_crop[0] = [top_mean[0], top_mean[1]]

    # Bottom without crop
    blackline_y_max = np.amax(blackline[:, :, 1])
    blackline_bottom = blackline[np.where(blackline[:, 0, 1] == blackline_y_max)][:, :, 0]
    blackline_bottom = blackline_bottom[blackline_bottom[:, 0].argsort()]
    blackline_bottom_gap_fill = (blackline_bottom + max_gap + 1)[:-1]

    blackline_gap_mask = blackline_bottom_gap_fill < blackline_bottom[1:]

    bottom_point_mean = (int(np.mean(blackline_bottom)), blackline_y_max)

    if np.sum(blackline_gap_mask) == 1:
        gap_index = np.where(blackline_gap_mask)[0][0]

        if blackline_bottom[:gap_index].size > 0 and blackline_bottom[gap_index:].size > 0:
            bottom_mean_l = int(np.mean(blackline_bottom[:gap_index]))
            bottom_mean_r = int(np.mean(blackline_bottom[gap_index:]))

            if np.abs(bottom_mean_l - bottom_mean_r) > 80:
                if np.abs(bottom_mean_l - last_bottom_point) < np.abs(bottom_mean_r - last_bottom_point):
                    bottom_point_mean = (bottom_mean_l, blackline_y_max)
                    bottom_mean = (bottom_mean_r, blackline_y_max)
                else:
                    bottom_point_mean = (bottom_mean_r, blackline_y_max)
                    bottom_mean = (bottom_mean_l, blackline_y_max)

                poi_no_crop[3] = [bottom_mean[0], bottom_mean[1]]

    bottom_point = [bottom_point_mean[0], bottom_point_mean[1]]

    # Left without crop
    blackline_x_min = np.amin(blackline[:, :, 0])
    blackline_left = blackline[np.where(blackline[:, 0, 0] == blackline_x_min)]
    left_mean = (blackline_x_min, int(np.mean(blackline_left[:, :, 1])))
    poi_no_crop[1] = [left_mean[0], left_mean[1]]

    # Right without crop
    blackline_x_max = np.amax(blackline[:, :, 0])
    blackline_right = blackline[np.where(blackline[:, 0, 0] == blackline_x_max)]
    right_mean = (blackline_x_max, int(np.mean(blackline_right[:, :, 1])))
    poi_no_crop[2] = [right_mean[0], right_mean[1]]

    poi = np.zeros((3, 2), dtype=np.int32)  # [t, l, r]
    is_crop = blackline_crop.size > 0

    max_black_top = False

    if is_crop:
        # Top
        blackline_y_min = np.amin(blackline_crop[:, :, 1])
        blackline_top = blackline_crop[np.where(blackline_crop[:, 0, 1] == blackline_y_min)][:, :, 0]
        top_mean = (int(np.mean(blackline_top)), blackline_y_min)
        poi[0] = [top_mean[0], top_mean[1]]

        blackline_top = blackline_top[blackline_top[:, 0].argsort()]
        max_black_top = bool(np.abs(blackline_top[0] - blackline_top[-1]) > max_line_width)

        # Left
        blackline_x_min = np.amin(blackline_crop[:, :, 0])
        blackline_left = blackline_crop[np.where(blackline_crop[:, 0, 0] == blackline_x_min)]
        left_mean = (blackline_x_min, int(np.mean(blackline_left[:, :, 1])))
        poi[1] = [left_mean[0], left_mean[1]]

        # Right
        blackline_x_max = np.amax(blackline_crop[:, :, 0])
        blackline_right = blackline_crop[np.where(blackline_crop[:, 0, 0] == blackline_x_max)]
        right_mean = (blackline_x_max, int(np.mean(blackline_right[:, :, 1])))
        poi[2] = [right_mean[0], right_mean[1]]

    return poi, poi_no_crop, is_crop, max_black_top, bottom_point

"""
def calculate_angle(blackline, blackline_crop, average_line_angle, turn_direction, last_bottom_point, average_line_point, entry):
    global multiple_bottom_side

    poi, poi_no_crop, is_crop, max_black_top, bottom_point = calculate_angle_numba(blackline, blackline_crop, last_bottom_point, average_line_point)

    black_top = poi_no_crop[0][1] < camera_y * .1

    multiple_bottom = not (poi_no_crop[3][0] == 0 and poi_no_crop[3][1] == 0)

    black_l_high = poi_no_crop[1][1] < camera_y * .5
    black_r_high = poi_no_crop[2][1] < camera_y * .5

    if entry:
        final_poi = poi_no_crop[0]

    elif not timer.get_timer("multiple_bottom"):
        final_poi = [multiple_bottom_side, camera_y]

    elif turn_direction in ["left", "right"]:
        index = 1 if turn_direction == "left" else 2
        final_poi = poi[index] if is_crop else poi_no_crop[index]

    else:
        if black_top:
            final_poi = poi[0] if is_crop and not max_black_top else poi_no_crop[0]

            if (poi_no_crop[1][0] < camera_x * 0.02 and poi_no_crop[1][1] > camera_y * (lineCropPercentage.value * .75)) or (poi_no_crop[2][0] > camera_x * 0.98 and poi_no_crop[2][1] > camera_y * (lineCropPercentage.value * .75)):
                final_poi = poi_no_crop[0]

                if black_l_high or black_r_high:
                    near_high_index = 0

                    if black_l_high and not black_r_high:
                        near_high_index = 1

                    elif not black_l_high and black_r_high:
                        near_high_index = 2

                    elif black_l_high and black_r_high:
                        if np.abs(poi_no_crop[1][0] - average_line_point) < np.abs(poi_no_crop[2][0] - average_line_point):
                            near_high_index = 1
                        else:
                            near_high_index = 2

                    if np.abs(poi_no_crop[near_high_index][0] - average_line_point) < np.abs(poi_no_crop[0][0] - average_line_point):
                        final_poi = poi_no_crop[near_high_index]

        else:
            final_poi = poi[0] if is_crop else poi_no_crop[0]

            if poi_no_crop[1][0] < camera_x * 0.02 and poi_no_crop[2][0] > camera_x * 0.98 and timer.get_timer("multiple_side_r") and timer.get_timer("multiple_side_l"):
                if average_line_angle >= 0:
                    index = 2
                    timer.set_timer("multiple_side_r", .6)
                else:
                    index = 1
                    timer.set_timer("multiple_side_l", .6)

                final_poi = poi[index] if is_crop else poi_no_crop[index]

            elif not timer.get_timer("multiple_side_l"):
                final_poi = poi[1] if is_crop else poi_no_crop[1]

            elif not timer.get_timer("multiple_side_r"):
                final_poi = poi[2] if is_crop else poi_no_crop[2]

            elif poi_no_crop[1][0] < camera_x * 0.02:
                final_poi = poi[1] if is_crop else poi_no_crop[1]

            elif poi_no_crop[2][0] > camera_x * 0.98:
                final_poi = poi[2] if is_crop else poi_no_crop[2]

            elif multiple_bottom and timer.get_timer("multiple_bottom"):
                if poi_no_crop[3][0] < bottom_point[0]:
                    final_poi = [0, camera_y]
                    multiple_bottom_side = 0
                else:
                    final_poi = [camera_x, camera_y]
                    multiple_bottom_side = camera_x
                timer.set_timer("multiple_bottom", .6)

    return int((final_poi[0] - camera_x / 2) / (camera_x / 2) * 180), final_poi, bottom_point
"""

def LoPController():
    pass


def gapController():
    pass


def check_black(black_around_sign, i, green_box):
    global blackImage

    green_box = green_box[green_box[:, 1].argsort()]

    marker_height = green_box[-1][1] - green_box[0][1]

    black_around_sign[i, 4] = int(green_box[2][1])

    # Bottom
    roi_b = blackImage[int(green_box[2][1]):np.minimum(int(green_box[2][1] + (marker_height * 0.8)), camera_y), np.minimum(int(green_box[2][0]), int(green_box[3][0])):np.maximum(int(green_box[2][0]), int(green_box[3][0]))]
    if roi_b.size > 0:
        if np.mean(roi_b[:]) > 125:
            black_around_sign[i, 0] = 1

    # Top
    roi_t = blackImage[np.maximum(int(green_box[1][1] - (marker_height * 0.8)), 0):int(green_box[1][1]), np.minimum(np.maximum(int(green_box[0][0]), 0), np.maximum(int(green_box[1][0]), 0)):np.maximum(np.maximum(int(green_box[0][0]), 0), np.maximum(int(green_box[1][0]), 0))]
    if roi_t.size > 0:
        if np.mean(roi_t[:]) > 125:
            black_around_sign[i, 1] = 1

    green_box = green_box[green_box[:, 0].argsort()]

    # Left
    roi_l = blackImage[np.minimum(int(green_box[0][1]), int(green_box[1][1])):np.maximum(int(green_box[0][1]), int(green_box[1][1])), np.maximum(int(green_box[1][0] - (marker_height * 0.8)), 0):int(green_box[1][0])]
    if roi_l.size > 0:
        if np.mean(roi_l[:]) > 125:
            black_around_sign[i, 2] = 1

    # Right
    roi_r = blackImage[np.minimum(int(green_box[2][1]), int(green_box[3][1])):np.maximum(int(green_box[2][1]), int(green_box[3][1])), int(green_box[2][0]):np.minimum(int(green_box[2][0] + (marker_height * 0.8)), camera_x)]
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
    global cv2_img, blackImage

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
    global greenImage, blackImage
    contoursGreen, _ = cv2.findContours(greenImage, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)

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
    global cv2_img, blackImage, greenImage, redImage, x_last, y_last

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


    x_last = camera_x / 2
    y_last = camera_y / 2
    lastBottomPoint_x = camera_x / 2
    lastLineAngle = 90


    t0 = time.perf_counter()
    while not terminate.value:
        t1 = t0 + config.lineDelayMS * 0.001

        # Loop

        LoPController()
        
        if robot.objective == "Follow Line":
            raw_capture = camera.capture_array()
            cv2_img = cv2.cvtColor(raw_capture, cv2.COLOR_RGBA2BGR)

            hsvImage = cv2.cvtColor(cv2_img, cv2.COLOR_BGR2HSV)
            greenImage = cv2.inRange(hsvImage, green_min, green_max)
            redImage = cv2.inRange(hsvImage, red_min_1, red_max_1) + cv2.inRange(hsvImage, red_min_2, red_max_2)
            blackImage = cv2.inRange(hsvImage, black_min, black_max)

            """# Follow Line - Get Centroid and Line Angle            
            lineCenterX.value, lineAngle.value = getLine()"""

            # Get blackline and blackline contours
            contoursBlack, _ = cv2.findContours(blackImage, cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)
            blackLine, blackLineCrop = getLineAndCrop(contoursBlack)
            poiCropped, poi, isCrop, maxBlackTop, bottomPoint = calculatePointsOfInterest(blackLine, blackLineCrop, lastBottomPoint_x, lastLineAngle)
            
            cv2.circle(cv2_img, (int(poiCropped[0][0]), int(poiCropped[0][1])), 10, (0, 0, 255), -1)
            cv2.circle(cv2_img, (int(poiCropped[1][0]), int(poiCropped[1][1])), 10, (0, 255, 0), -1)
            cv2.circle(cv2_img, (int(poiCropped[2][0]), int(poiCropped[2][1])), 10, (255, 0, 0), -1)

            cv2.circle(cv2_img, (int(poi[0][0]), int(poi[0][1])), 5, (0, 0, 255), -1)
            cv2.circle(cv2_img, (int(poi[1][0]), int(poi[1][1])), 5, (255, 0, 0), -1)
            cv2.circle(cv2_img, (int(poi[2][0]), int(poi[2][1])), 5, (0, 255, 0), -1)

            cv2.circle(cv2_img, (int(bottomPoint[0]), int(bottomPoint[1])), 10, (0, 255, 255), -1)

            lastBottomPoint_x = bottomPoint[0]
            lastLineAngle = lineAngle.value

            # Deal with intersections
            intersectionDetector()

            # Show cv2_imgs
            cv2.imwrite("./InProgress2/latest_frame_cv2.jpg", cv2_img)
            cv2.imwrite("./InProgress2/latest_frame_hsv.jpg", hsvImage)
            cv2.imwrite("./InProgress2/latest_frame_green.jpg", greenImage)
            cv2.imwrite("./InProgress2/latest_frame_black.jpg", blackImage)

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
            