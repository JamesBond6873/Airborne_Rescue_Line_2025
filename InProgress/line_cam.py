# -------- Robot Actuators/Sensors -------- 

import datetime
import time
import os
import cv2
import numpy as np
from picamera2 import Picamera2
from libcamera import controls
from ultralytics import YOLO
from ultralytics.utils.plotting import colors

import config
from utils import printDebug
from utils import Timer
from utils import TimerManager
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

camera_x = 448
camera_y = 252

multiple_bottom_side = camera_x / 2
lastDirection = "Straight!"

timer = Timer()
timer_manager = TimerManager()

kernel = np.ones((3, 3), np.uint8)

lastSide = -1

photoCounter = 0


def savecv2_img(folder, cv2_img):
    global photoCounter
    if saveFrame.value:
        # Create the "fotos" directory if it doesn't exist

        #if not timer_manager.is_timer_expired("saveImageCoolDown"):
        #    return
        
        folder_name = folder
        os.makedirs(folder_name, exist_ok=True)
        
        # Generate filename based on timestamp
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S-%f")[:-3]  # Remove last 3 digits for milliseconds
        file_path = os.path.join(folder_name, f"cv2_img_{timestamp}.jpg")
        
        # Save the cv2_img using OpenCV
        cv2.imwrite(file_path, cv2_img)

        photoCounter += 1
        printDebug(f"Saved Image {photoCounter}: {file_path}", config.softDEBUG)

        #timer_manager.set_timer("saveImageCoolDown", 10)
        saveFrame.value = False
    

def computeMoments(contour):
    # Compute cv2_img moments for the largest contour

    theta = np.pi / 2

    finalContour = cv2.cvtColor(contour, cv2.COLOR_BGR2GRAY)

    M = cv2.moments(finalContour)
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

    return theta


def ignoreHighFOVCorners(blackImage, xPercentage=0.25, yPercentage=0.15):
    # Define the camera_x and height proportions of the triangular cut
    corner_width = int(camera_x * xPercentage)  # Extend more on x-axis
    corner_height = int(camera_y * yPercentage)  # Less extension on y-axis

    # Define triangle vertices for the top-left corner
    top_left_triangle = np.array([[0, 0], [corner_width, 0], [0, corner_height]], np.int32)
    top_left_triangle = top_left_triangle.reshape((-1, 1, 2))

    # Define triangle vertices for the top-right corner
    top_right_triangle = np.array([[camera_x, 0], [camera_x - corner_width, 0], [camera_x, corner_height]], np.int32)
    top_right_triangle = top_right_triangle.reshape((-1, 1, 2))

    # Fill triangles with white inverse of (255)
    cv2.fillPoly(blackImage, [top_left_triangle], 0)
    cv2.fillPoly(blackImage, [top_right_triangle], 0)

    return blackImage


def checkContourSize(contours, contour_color="red", size=20000):
    global cv2_img

    if contour_color == "red":
        color = (0, 255, 0) # Green
    elif contour_color == "green":
        color = (0, 0, 255) # Red
    else:
        color = (255, 0, 0)

    for contour in contours:
        contour_size = cv2.contourArea(contour)

        if contour_size > size:
            x, y, w, h = cv2.boundingRect(contour)
            cv2.rectangle(cv2_img, (x, y), (x + w, y + h), color, 2)
            return True

    return False


def getLineAndCrop(contours_blk):
    global x_last, y_last
    candidates = []
    off_bottom = 0
    min_area = 1500

    for i, contour in enumerate(contours_blk):
        box = cv2.boxPoints(cv2.minAreaRect(contour))
        box = box[box[:, 1].argsort()[::-1]]  # Sort them by their y values and reverse
        bottom_y = box[0][1]
        y_mean = (np.clip(box[0][1], 0, camera_y) + np.clip(box[3][1], 0, camera_y)) / 2
        contour_area = cv2.contourArea(contour)  # Get contour area

        if box[0][1] >= (camera_y * 0.75):
            off_bottom += 1

        if contour_area < min_area:
            continue  # Skip small contours

        box = box[box[:, 0].argsort()]
        x_mean = (np.clip(box[0][0], 0, camera_x) + np.clip(box[3][0], 0, camera_x)) / 2
        x_y_distance = abs(x_last - x_mean) + abs(y_last - y_mean)  # Distance between the last x/y and current x/y

        candidates.append([i, bottom_y, x_y_distance, x_mean, y_mean])


    candidates = np.array(candidates, dtype=np.int32).reshape(-1, 5)


    if off_bottom < 2:
        candidates = candidates[candidates[:, 1].argsort()[::-1]]  # Sort candidates by their bottom_y
    else:
        off_bottom_candidates = candidates[np.where(candidates[:, 1] >= (camera_y * 0.25))] # initially * 0.75
        candidates = off_bottom_candidates[off_bottom_candidates[:, 2].argsort()]
        

    if len(candidates) == 0: # No valid contours found
        lineDetected.value = False
        x_last, y_last = camera_x // 2, camera_y * 0.75
        return np.array([[[x_last, y_last]]]), np.array([[[x_last, y_last]]])  # Fake contour at center
    

    lineDetected.value = True


    if turnDirection.value == "left":
        x_last = np.clip(candidates[0][3] - 150, 0, camera_x)
    elif turnDirection.value == "right":
        x_last = np.clip(candidates[0][3] + 150, 0, camera_x)
    else:
        x_last = candidates[0][3]

    y_last = candidates[0][4]
    blackline = contours_blk[int( candidates[0][0] )]
    blackline_crop = blackline[np.where(blackline[:, 0, 1] > camera_y * lineCropPercentage.value)]

    cv2.drawContours(cv2_img, blackline, -1, (255, 0, 0), 2)
    cv2.drawContours(cv2_img, blackline_crop, -1, (255, 255, 0), 2)

    cv2.circle(cv2_img, (int(x_last), int(y_last)), 3, (0, 0, 255), -1)

    return blackline, blackline_crop


def calculatePointsOfInterest(blackline, blackline_crop, last_bottom_point, average_line_point):
    max_gap = 1
    max_line_width = camera_x * .3

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


def interpretPOI(poiCropped, poi, is_crop, maxBlackTop, bottomPoint, turn_direction, last_line_point):
    global multiple_bottom_side, lastDirection, lastSide

    average_line_point = last_line_point[0]
    average_line_point_y = last_line_point[1]

    black_top = poi[0][1] < camera_y * .05

    multiple_bottom = not (poi[3][0] == 0 and poi[3][1] == 0)

    black_l_high = poi[1][1] < camera_y * .5
    black_r_high = poi[2][1] < camera_y * .5

    if not timer.get_timer("multiple_bottom"):
        final_poi = [multiple_bottom_side, camera_y]
        turnReason.value = 0
        lastSide = 0  # Reset turning preference


    elif turn_direction == "left" or turn_direction == "right":
        final_poi = poi[1] if turn_direction == "left" else poi[2]
        lastDirection = turn_direction
        
        if timer_manager.is_timer_expired("test_timer"): # So only start counting time from the last time it was seen
            timer_manager.set_timer("test_timer", 1.5) # Give 1.0 s for turn
        
        turnReason.value = 1
        lastSide = 0  # Reset turning preference

    elif turn_direction == "uTurn":
        # BackUp to Control loop. Meaning it will go forward until control decides otherwise
        final_poi = (camera_x / 2, camera_y / 2)
        turnReason.value = 102
        lastSide = 0  # Reset turning preference

    elif not timer_manager.is_timer_expired("test_timer"): # Not Expired
        final_poi = poi[1] if lastDirection == "left" else poi[2]
        turnReason.value = 100
        lastSide = 0  # Reset turning preference

    #elif not timer_manager.is_timer_expired("rightLeft"): # Sharp left
     #   final_poi = poi[1]
      #  turnReason.value = 160

    #elif not timer_manager.is_timer_expired("rightRight"): # Sharp Right
     #   final_poi = poi[2]
      #  turnReason.value = 170


    else:
        if black_top:
            final_poi = poiCropped[0] if is_crop and not maxBlackTop else poi[0]
            turnReason.value = 2
            lastSide = 0  # Reset turning preference

            if (poi[1][0] < camera_x * 0.05 and poi[1][1] > camera_y * (lineCropPercentage.value * .75)) or (poi[2][0] > camera_x * 0.95 and poi[2][1] > camera_y * (lineCropPercentage.value * .75)):
                final_poi = poi[0]
                turnReason.value = 3

                if black_l_high or black_r_high:
                    near_high_index = 0
                    turnReason.value = 4

                    if black_l_high and not black_r_high:
                        near_high_index = 1
                        turnReason.value = 5

                    elif not black_l_high and black_r_high:
                        near_high_index = 2
                        turnReason.value = 6

                    elif black_l_high and black_r_high:
                        if np.abs(poi[1][0] - average_line_point) < np.abs(poi[2][0] - average_line_point):
                            near_high_index = 1
                            turnReason.value = 7
                        else:
                            near_high_index = 2
                            turnReason.value = 8

                    if np.abs(poi[near_high_index][0] - average_line_point) < np.abs(poi[0][0] - average_line_point):
                        final_poi = poi[near_high_index]
                        turnReason.value = 9

        else:
            final_poi = poiCropped[0] if is_crop else poi[0]
            turnReason.value = 10

            if poi[1][0] < camera_x * 0.10 and poi[2][0] > camera_x * 0.90 and timer_manager.is_timer_expired("rightLeft") and timer_manager.is_timer_expired("rightRight"):
                if lastSide == 2:
                    index = 2
                    timer_manager.set_timer("rightRight", 0.6)
                    turnReason.value = 17.5
                    final_poi = poi[index]
                elif lastSide == 1:
                    index = 1
                    timer_manager.set_timer("rightLeft", 0.6)
                    turnReason.value = 16.5
                    final_poi = poi[index]
                

            #elif poi[1][0] < camera_x * 0.05:
            elif poi[1][0] < camera_x * 0.05 and timer_manager.is_timer_expired("rightRight"): # Do not go for left if we were going right
                # final_poi = poiCropped[1] if is_crop else poi[1] # Removed because constant lineCropPercentage
                if timer_manager.is_timer_expired("rightLeft"):
                    timer_manager.set_timer("rightLeft", 0.3)
                final_poi = poi[1]
                lastSide = 1
                turnReason.value = 16

            elif poi[2][0] > camera_x * 0.95 and timer_manager.is_timer_expired("rightLeft"): # Do not go for right if we were going left
                # final_poi = poiCropped[2] if is_crop else poi[2] # Removed because constant lineCropPercentage
                if timer_manager.is_timer_expired("rightRight"):
                    timer_manager.set_timer("rightRight", 0.3)
                final_poi = poi[2]
                lastSide = 2
                turnReason.value = 17

            elif multiple_bottom and timer.get_timer("multiple_bottom"):
                if poi[3][0] < bottomPoint[0]:
                    final_poi = [0, camera_y]
                    multiple_bottom_side = 0
                    turnReason.value = 18
                else:
                    final_poi = [camera_x, camera_y]
                    multiple_bottom_side = camera_x
                    turnReason.value = 19
                timer.set_timer("multiple_bottom", .6)
            
            """if poi[1][0] < camera_x * 0.05 and poi[2][0] > camera_x * 0.95 and timer.get_timer("multiple_side_r") and timer.get_timer("multiple_side_l"):
                #print(f"Here {average_line_angle}")
                if average_line_angle >= 0:
                    #print(f"Here 1")
                    turnReason.value = 11
                    index = 2
                    timer.set_timer("multiple_side_r", .6)
                else:
                    #print(f"Here 2")
                    turnReason.value = 12
                    index = 1
                    timer.set_timer("multiple_side_l", .6)

                final_poi = poiCropped[index] if is_crop else poi[index]
                turnReason.value = 13

            elif not timer.get_timer("multiple_side_l"):
                #print(f"Here 3")
                final_poi = poiCropped[1] if is_crop else poi[1]
                turnReason.value = 14

            elif not timer.get_timer("multiple_side_r"):
                #print(f"Here 4")
                final_poi = poiCropped[2] if is_crop else poi[2]
                turnReason.value = 15"""

    if (final_poi == poiCropped[0]).all():
        #angle = computeMoments(blackLineCrop)
        angle = np.pi / 2
    else: 
        angle = np.pi / 2 # don't know how to calculate angle in other cases

    angle = int((final_poi[0] - camera_x / 2) / (camera_x / 2) * 180)

    return angle, final_poi, bottomPoint


def checkBlack(black_around_sign, i, green_box):
    global cv2_img, blackImage

    green_box = green_box[green_box[:, 1].argsort()]

    marker_height = green_box[-1][1] - green_box[0][1]

    black_around_sign[i, 4] = int(green_box[2][1])

    roi_mean_comparison = 125
    marker_height_search_factor = 0.3

    # Bottom
    roi_b_top_left = (np.minimum(int(green_box[2][0]), int(green_box[3][0])), int(green_box[2][1]))
    roi_b_bottom_right = (np.maximum(int(green_box[2][0]), int(green_box[3][0])), np.minimum(int(green_box[2][1] + (marker_height * marker_height_search_factor)), camera_y))

    # Draw the bounding box for the bottom region
    cv2.rectangle(cv2_img, roi_b_top_left, roi_b_bottom_right, (0, 255, 0), 2)  # Green color box
    
    
    # Bottom
    roi_b = blackImage[int(green_box[2][1]):np.minimum(int(green_box[2][1] + (marker_height * marker_height_search_factor)), camera_y), np.minimum(int(green_box[2][0]), int(green_box[3][0])):np.maximum(int(green_box[2][0]), int(green_box[3][0]))]
    if roi_b.size > 0:
        if np.mean(roi_b[:]) > roi_mean_comparison:
            black_around_sign[i, 0] = 1

    # Top
    roi_t_top_left = (np.minimum(np.maximum(int(green_box[0][0]), 0), np.maximum(int(green_box[1][0]), 0)), np.maximum(int(green_box[1][1] - (marker_height * marker_height_search_factor)), 0))
    roi_t_bottom_right = (np.maximum(np.maximum(int(green_box[0][0]), 0), np.maximum(int(green_box[1][0]), 0)), int(green_box[1][1]))

    # Draw the bounding box for the top region
    cv2.rectangle(cv2_img, roi_t_top_left, roi_t_bottom_right, (0, 255, 0), 2)  # Green color box
    

    roi_t = blackImage[np.maximum(int(green_box[1][1] - (marker_height * marker_height_search_factor)), 0):int(green_box[1][1]), np.minimum(np.maximum(int(green_box[0][0]), 0), np.maximum(int(green_box[1][0]), 0)):np.maximum(np.maximum(int(green_box[0][0]), 0), np.maximum(int(green_box[1][0]), 0))]
    if roi_t.size > 0:
        if np.mean(roi_t[:]) > roi_mean_comparison:
            black_around_sign[i, 1] = 1

    green_box = green_box[green_box[:, 0].argsort()]

    # Left
    roi_l_top_left = (np.maximum(int(green_box[1][0] - (marker_height * marker_height_search_factor)), 0), np.minimum(int(green_box[0][1]), int(green_box[1][1])))
    roi_l_bottom_right = (int(green_box[1][0]), np.maximum(int(green_box[0][1]), int(green_box[1][1])))

    # Draw the bounding box for the left region
    cv2.rectangle(cv2_img, roi_l_top_left, roi_l_bottom_right, (0, 255, 0), 2)  # Green color box
    

    roi_l = blackImage[np.minimum(int(green_box[0][1]), int(green_box[1][1])):np.maximum(int(green_box[0][1]), int(green_box[1][1])), np.maximum(int(green_box[1][0] - (marker_height * marker_height_search_factor)), 0):int(green_box[1][0])]
    if roi_l.size > 0:
        if np.mean(roi_l[:]) > roi_mean_comparison:
            black_around_sign[i, 2] = 1

    # Right
    roi_r_top_left = (int(green_box[2][0]), np.minimum(int(green_box[2][1]), int(green_box[3][1])))
    roi_r_bottom_right = (np.minimum(int(green_box[2][0] + (marker_height * marker_height_search_factor)), camera_x), np.maximum(int(green_box[2][1]), int(green_box[3][1])))

    # Draw the bounding box for the right region
    cv2.rectangle(cv2_img, roi_r_top_left, roi_r_bottom_right, (0, 255, 0), 2)  # Green color box
    

    roi_r = blackImage[np.minimum(int(green_box[2][1]), int(green_box[3][1])):np.maximum(int(green_box[2][1]), int(green_box[3][1])), int(green_box[2][0]):np.minimum(int(green_box[2][0] + (marker_height * marker_height_search_factor)), camera_x)]
    if roi_r.size > 0:
        if np.mean(roi_r[:]) > roi_mean_comparison:
            black_around_sign[i, 3] = 1

    return black_around_sign


def determineTurnDirection(black_around_sign):
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

    height, width = cv2_img.shape[:2]  # Get the height and width of the image
    bottom_percent_threshold = int(0.15 * height)  # This is the pixel line separating the top 20% from the bottom 80%

    black_around_sign = np.zeros((len(contours_grn), 5), dtype=np.int16)  # [[b,t,l,r,lp], [b,t,l,r,lp]]

    for i, contour in enumerate(contours_grn):
        area = cv2.contourArea(contour)

        # Get the y-coordinate of the center of the bounding box
        center, _, _ = cv2.minAreaRect(contour)  # center is a tuple (x, y)
        y_center = center[1]  # Extract the y-coordinate

        if area <= 1500:  # Changed to 1500 # Later Changed to 1000 # Changed to 750
                continue
        
        # Only process contours in the bottom 80% of the image
        if y_center < bottom_percent_threshold:
            #print(f"Here {y_center} {bottom_percent_threshold}")
            continue
            

        green_box = cv2.boxPoints(cv2.minAreaRect(contour))
        draw_box = np.intp(green_box)
        cv2.drawContours(cv2_img, [draw_box], -1, (0, 0, 255), 2)

        black_around_sign = checkBlack(black_around_sign, i, green_box)

    turn_left, turn_right, left_bottom, right_bottom = determineTurnDirection(black_around_sign)

    if turn_left and not turn_right and not left_bottom:
        return "left"
    elif turn_right and not turn_left and not right_bottom:
        return "right"
    elif turn_left and turn_right and not (left_bottom and right_bottom):
        return "uTurn"
    else:
        return "straight"


def intersectionDetector():
    global greenImage, blackImage
    contoursGreen, _ = cv2.findContours(greenImage, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)

    if len(contoursGreen) > 0:
        turnDirection.value = checkGreen(contoursGreen)
                    
    else:
        turnDirection.value = "straight"


def obstacleController():
    pass


#############################################################################
#                            Line Camera Loop
#############################################################################

def lineCamLoop():
    global cv2_img, blackImage, greenImage, redImage, x_last, y_last

    #modelVictim = YOLO('/home/raspberrypi/Airborne_Rescue_Line_2025/Ai/models/ball_zone_s/ball_detect_s_edgetpu.tflite', task='detect')
    modelVictim = YOLO('/home/raspberrypi/Airborne_Rescue_Line_2025/Ai/models/victim_ball_detection_v3/victim_ball_detection_int8_edgetpu.tflite', task='detect')
    modelSilverLine = YOLO('/home/raspberrypi/Airborne_Rescue_Line_2025/Ai/models/silver_zone_entry/silver_classify_s.onnx', task='classify')
    
    camera = Picamera2(0)

    mode = camera.sensor_modes[0]
    camera.configure(camera.create_video_configuration(sensor={'output_size': mode['size'], 'bit_depth': mode['bit_depth']}))

    #camera.set_controls({"AfMode": controls.AfModeEnum.Manual, "ExposureTime":10000})
    camera.set_controls({
        #"AfMode": controls.AfModeEnum.Manual,
        #"LensPosition": 6.5,
        #"FrameDurationLimits": (1000000 // 50, 1000000 // 50),
        #"AnalogueGain": 3.0,  # Fix gain (default 1.0)
        #"ExposureTime": 10000  # Set exposure in microseconds (adjust as needed)
    })

    camera.start()
    time.sleep(0.1)

    # Image for brightness normalization
    #white_img = cv2.imread("./InProgress3/White_Image_2.jpg")
    #white_gray = cv2.cvtColor(white_img, cv2.COLOR_RGB2GRAY)
    #white_gray += (white_gray == 0)

    x_last = int( camera_x / 2 )
    y_last = int( camera_y / 2 )
    lastBottomPoint_x = camera_x / 2
    lastLineAngle = 90
    lastLinePoint = [x_last, y_last] # center points 

    do_inference_limit = 7
    do_inference_counter = 0
    last_best_box = None

    timer.set_timer("image_similarity", .5)
    timer.set_timer("multiple_bottom", .05)
    timer.set_timer("multiple_side_l", .05)
    timer.set_timer("multiple_side_r", .05)
    timer.set_timer("right_marker", .05)
    timer.set_timer("left_marker", .05)
    timer.set_timer("right_marker_up", .05)
    timer.set_timer("left_marker_up", .05)
    timer.set_timer("turn_persistence_timer", .05)  # Initialize if not present

    timer_manager.add_timer("test_timer", 0.05)
    timer_manager.add_timer("uTurn", 0.05)
    timer_manager.add_timer("rightLeft", 0.05)
    timer_manager.add_timer("rightRight", 0.05)
    timer_manager.add_timer("goToBall", 0.05)
    timer_manager.add_timer("saveImageCoolDown", 0.05)


    t0 = time.perf_counter()
    while not terminate.value:
        t1 = t0 + config.lineDelayMS * 0.001

        # Loop
        raw_capture = camera.capture_array()
        raw_capture = cv2.resize(raw_capture, (camera_x, camera_y))
        cv2_img = cv2.cvtColor(raw_capture, cv2.COLOR_RGBA2BGR)

        savecv2_img("VictimsDataSet", cv2_img)
        cv2.imwrite("/home/raspberrypi/Airborne_Rescue_Line_2025/Latest_Frames/latest_frame_original.jpg", cv2_img)

        if objective.value == "follow_line":
            # Color Processing
            hsvImage = cv2.cvtColor(cv2_img, cv2.COLOR_BGR2HSV)
            greenImage = cv2.inRange(hsvImage, green_min, green_max)
            redImage = cv2.inRange(hsvImage, red_min_1, red_max_1) + cv2.inRange(hsvImage, red_min_2, red_max_2)
            
            # Black Processing
            grayImage = cv2.cvtColor(cv2_img, cv2.COLOR_BGR2GRAY)
            _, blackImage = cv2.threshold(grayImage, 55, 255, cv2.THRESH_BINARY_INV)
            
            blackImage = ignoreHighFOVCorners(blackImage)
            

            # Noise Reduction
            blackImage = cv2.erode(blackImage, kernel, iterations=5)
            blackImage = cv2.dilate(blackImage, kernel, iterations=17) # Previous values: 12 | 16
            blackImage = cv2.erode(blackImage, kernel, iterations=9)  # Previous values: 4 | 8"""

            greenImage = cv2.erode(greenImage, kernel, iterations=1)
            greenImage = cv2.dilate(greenImage, kernel, iterations=11)
            greenImage = cv2.erode(greenImage, kernel, iterations=9)
                                    
            redImage = cv2.erode(redImage, kernel, iterations=1)
            redImage = cv2.dilate(redImage, kernel, iterations=11)
            redImage = cv2.erode(redImage, kernel, iterations=9)


            # -- SILVER Line --
            """if do_inference_counter >= do_inference_limit:
                results = modelSilverLine.predict(raw_capture, imgsz=128, conf=0.4, workers=4, verbose=False)
                result = results[0].numpy()

                confidences = result.probs.top5conf
                silverValue.value = round(confidences[0] if result.probs.top1 == 1 else confidences[1], 3)  # 0 = Line, 1 = Silver
                do_inference_counter = 0

            do_inference_counter += 1
            if silverValue.value > .6 and LOPstate.value == 0:
                cv2.circle(cv2_img, (10, camera_y - 10), 5, (255, 255, 255), -1, cv2.LINE_AA)
                objective.value = "zone"
                zoneStatus.value = "begin"
            """
            
            # -- INTERSECTIONS -- Deal with intersections
            intersectionDetector()


            # -- RED STRIP -- Check for Red Line - Stop
            contoursRed, _ = cv2.findContours(redImage, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
            redDetected.value = checkContourSize(contoursRed)


            # -- Black Line --
            # Get Black Contours
            contoursBlack, _ = cv2.findContours(blackImage, cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)
            # Calculate Black Line (cropped and not) + Points of Interest
            blackLine, blackLineCrop = getLineAndCrop(contoursBlack)
            poiCropped, poi, isCrop, maxBlackTop, bottomPoint = calculatePointsOfInterest(blackLine, blackLineCrop, lastBottomPoint_x, lastLinePoint[0])
            lineAngle2, finalPoi, bottomPoint = interpretPOI(poiCropped, poi, isCrop, maxBlackTop, bottomPoint, turnDirection.value, lastLinePoint)
            lineCenterX.value = finalPoi[0]
            isCropped.value = isCrop

            lineAngle.value = np.pi / 2 # Means ignore line angle when in this situation

            # Update Image
            cv2.circle(cv2_img, (int(poiCropped[0][0]), int(poiCropped[0][1])), 5, (0, 0, 255), -1)
            cv2.circle(cv2_img, (int(poiCropped[1][0]), int(poiCropped[1][1])), 5, (0, 255, 0), -1)
            cv2.circle(cv2_img, (int(poiCropped[2][0]), int(poiCropped[2][1])), 5, (255, 0, 0), -1)

            cv2.circle(cv2_img, (int(poi[0][0]), int(poi[0][1])), 2, (0, 0, 255), -1)
            cv2.circle(cv2_img, (int(poi[1][0]), int(poi[1][1])), 2, (255, 0, 0), -1)
            cv2.circle(cv2_img, (int(poi[2][0]), int(poi[2][1])), 2, (0, 255, 0), -1)

            cv2.circle(cv2_img, (int(bottomPoint[0]), int(bottomPoint[1])), 5, (0, 255, 255), -1)

            cv2.circle(cv2_img, (int(finalPoi[0]), int(finalPoi[1])), 10, (0, 0, 255), -1)


            lastBottomPoint_x = bottomPoint[0]
            lastLineAngle = lineAngle2
            lastLinePoint = finalPoi


            # Show cv2_imgs
            cv2.imwrite("/home/raspberrypi/Airborne_Rescue_Line_2025/Latest_Frames/latest_frame_hsv.jpg", hsvImage)
            cv2.imwrite("/home/raspberrypi/Airborne_Rescue_Line_2025/Latest_Frames/latest_frame_green.jpg", greenImage)
            cv2.imwrite("/home/raspberrypi/Airborne_Rescue_Line_2025/Latest_Frames/latest_frame_black.jpg", blackImage)
            cv2.imwrite("/home/raspberrypi/Airborne_Rescue_Line_2025/Latest_Frames/latest_frame_red.jpg", redImage)

            obstacleController()

            #savecv2_img("VictimsDataSet", cv2_img)
            

        elif objective.value == "zone":
            results = modelVictim.predict(cv2_img, imgsz=(512, 224), conf=0.3, iou=0.2, agnostic_nms=True, workers=4, verbose=False)  # verbose=True to enable debug info

            result = results[0].numpy()

            #print(f"Results: {results} {result}")

            boxes = []
            for box in result.boxes:
                x1, y1, x2, y2 = box.xyxy[0].astype(int)
                class_id = box.cls[0].astype(int)
                name = result.names[class_id]
                confidence = box.conf[0].astype(float)

                ballConfidence.value = confidence

                width = x2 - x1
                height = y2 - y1
                area = width * height
                distance = (x1 + x2) // 2

                if width >= 400: # Precarius attempt at ignoring random silver balls
                    continue

                boxes.append([area, distance, name, width, y2])

                color = colors(class_id, True)
                cv2.rectangle(cv2_img, (x1, y1), (x2, y2), color, 2)
                cv2.putText(cv2_img, f"{name}: {confidence:.2f}", (x1, y1 - 5), cv2.FONT_HERSHEY_DUPLEX, 0.5, color, 1, cv2.LINE_AA)

            #print(f"boxes {len(boxes)} {boxes}")
            if len(boxes) > 0:
                best_box = max(boxes, key=lambda x: x[0])
                if last_best_box is not None:
                    best_box = min(boxes, key=lambda x: abs(x[1] - last_best_box[1]))

                last_best_box = best_box
                ballCenterX.value = best_box[1]
                ballType.value = str.lower(str(best_box[2]))
                ballWidth.value = best_box[3]
                ballBottomY.value = best_box[4]
                print(f"BALLL FOUND: {ballCenterX.value} {ballBottomY.value} {ballType.value} {ballWidth.value} {ballConfidence.value}")
                zoneStatus.value = "goToBall"
                timer_manager.set_timer("goToBall", 0.750)
            else:
                if timer_manager.is_timer_expired("goToBall"):
                    last_best_box = None
                    ballCenterX.value = 0
                    ballType.value = "none"
                    ballWidth.value = -1
                    zoneStatus.value = "findVictims"
                else: # Not expired
                    pass


        cv2.imwrite("/home/raspberrypi/Airborne_Rescue_Line_2025/Latest_Frames/latest_frame_cv2.jpg", cv2_img)


        while (time.perf_counter() <= t1):
            time.sleep(0.0005)

        printDebug(f"\t\t\t\t\t\t\t\tLine Cam Loop Time: {t0} | {t1} | {time.perf_counter()}", config.DEBUG)
        t0 = t1
            