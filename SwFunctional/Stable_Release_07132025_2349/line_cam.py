# -------- Robot Sensors -------- 

import datetime
import time
import os
import cv2
import numpy as np
from picamera2 import Picamera2
from libcamera import controls
from glob import glob
from ultralytics import YOLO
from ultralytics.utils.plotting import colors
from skimage.metrics import structural_similarity

from config import *
from utils import printDebug
from utils import TimerManager
from mp_manager import *

print("Line Camera: \t \t \t OK")

# Debug Features
cameraDebugMode = computerOnlyDebug
#debugImageFolder = "DataSet/FullRunTest"
debugImageFolder = "DataSet/SilverLineTest2"
debugImagePaths = sorted(glob(os.path.join(debugImageFolder, "*.jpg")))
currentFakeImageIndex = 0
raw_capture = None
cv2_img = None

# Color Configs
black_min = np.array(black_min)
black_max_normal_top = np.array(black_max_normal_top)
black_max_normal_bottom = np.array(black_max_normal_bottom)
green_min = np.array(green_min)
green_max = np.array(green_max)
red_min_1 = np.array(red_min_1)
red_max_1 = np.array(red_max_1)
red_min_2 = np.array(red_min_2)
red_max_2 = np.array(red_max_2)

evacZoneGreenMin = np.array(evacZoneGreenMin)
evacZoneGreenMax = np.array(evacZoneGreenMax)
evacZoneRedMin_1 = np.array(evacZoneRedMin_1)
evacZoneRedMax_1 = np.array(evacZoneRedMax_1)
evacZoneRedMin_2 = np.array(evacZoneRedMin_2)
evacZoneRedMax_2 = np.array(evacZoneRedMax_2)

# Camera Images Configs
camera_x = 448
camera_y = 256

multiple_bottom_side = camera_x / 2
lastDirection = "Straight!"

# Timers
timer_manager = TimerManager()

kernel = np.ones((3, 3), np.uint8)

lastSide = -1

photoCounter = 0

doInferenceLimit = 2
doInferenceCounter = 0
checkSimilarityCounter = 0
checkSimilarityLimit = 30
lastImage = np.zeros((camera_y, camera_x), dtype=np.uint8)


# Initialize sensors data arrays
ballCenterXArray = createEmptyTimeArray()
ballBottomYArray = createEmptyTimeArray()
ballWidthArray = createEmptyTimeArray()
ballTypeArray = createEmptyTimeArray()
ballExistsArray = createEmptyTimeArray()
cornerCenterArrayGreen = createEmptyTimeArray()
cornerHeightArrayGreen = createEmptyTimeArray()

# Time-value arrays
TurnDirectionArray = createEmptyTimeArray()
LineAngleNormalizedArray = createEmptyTimeArray()
LineAngleArray = createEmptyTimeArray()
BottomPointXArray = createEmptyTimeArray()
LinePointXArray = createEmptyTimeArray()

imageSimilarityArray = createFilledArray(0, 1200)

silverValueArray = createEmptyTimeArray() # Silver Line Array
redValueArray = createEmptyTimeArray() # Red Line Array



def resetBallArrayVars():
    global ballCenterXArray, ballBottomYArray, ballWidthArray, ballTypeArray, ballExistsArray
    if resetBallArrays.value:
        ballCenterXArray = createFilledArray(camera_x // 2)
        ballBottomYArray = createFilledArray(camera_y // 2)
        ballWidthArray = createEmptyTimeArray()
        ballTypeArray = createFilledArray(0.5)
        ballExistsArray = createEmptyTimeArray()

        ballCenterX.value = calculateAverageArray(ballCenterXArray, 0.15)
        ballBottomY.value = calculateAverageArray(ballBottomYArray, 0.25)
        ballWidth.value = calculateAverageArray(ballWidthArray, 0.25)
        ballType.value = "black ball" if calculateAverageArray(ballTypeArray, 0.45) < 0.5 else "silver ball" # Maybe needs rechecking... (bias towards silver ball)
        ballExists.value = calculateAverageArray(ballExistsArray, 0.25) >= 0.5 # [0.5, 1.0] = Ball Exist True [0.0, 0.5[ = False

        print(f"Successfully reset ball arrays")
        printDebug(f"Reset Ball Arrays data: {ballExists.value} {ballCenterX.value} {ballBottomY.value} {ballWidth.value} {ballType.value}", DEBUG)
        resetBallArrays.value = False


def resetEvacZoneArrayVars():
    global cornerCenterArrayGreen, cornerHeightArrayGreen
    if resetEvacZoneArrays.value:
        cornerCenterArrayGreen = createFilledArray(camera_x // 2)
        cornerHeightArrayGreen = createEmptyTimeArray()

        cornerCenter.value = camera_x // 2
        cornerHeight.value = 0

        print(f"Successfully reset evacuation zone corner arrays")
        resetEvacZoneArrays.value = False


def resetImageSimilarityArrayVars():
    global imageSimilarityArray
    if resetImageSimilarityArrays.value:
        imageSimilarityArray = createFilledArray(0, 1200)
        
        stuckDetected.value = False

        print(f"Successfully reset image similarity arrays")
        resetImageSimilarityArrays.value = False


def savecv2_img(folder, cv2_img):
    global photoCounter
    if saveFrame.value:
        # Create the "fotos" directory if it doesn't exist

        if not timer_manager.is_timer_expired("saveImageCoolDown"):
            return
        
        folder_name = folder
        os.makedirs(folder_name, exist_ok=True)
        
        # Generate filename based on timestamp
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S-%f")[:-3]  # Remove last 3 digits for milliseconds
        file_path = os.path.join(folder_name, f"cv2_img_{timestamp}.jpg")
        
        # Save the cv2_img using OpenCV
        if not computerOnlyDebug:
            cv2.imwrite(file_path, cv2_img)

            photoCounter += 1
            printDebug(f"Saved Image {photoCounter}: {file_path}", softDEBUG)

        timer_manager.set_timer("saveImageCoolDown", 0.1)
        
        if not silverDatasetCollectionMode:
            saveFrame.value = False
    

def getCameraImage(camera):
    global currentFakeImageIndex, raw_capture, cv2_img

    if not cameraDebugMode:
        raw_capture = camera.capture_array()
        raw_capture = cv2.resize(raw_capture, (camera_x, camera_y))
        cv2_img = cv2.cvtColor(raw_capture, cv2.COLOR_RGBA2BGR)
        cv2.imwrite("/home/raspberrypi/Airborne_Rescue_Line_2025/Latest_Frames/latest_frame_original.jpg", cv2_img)
        return cv2_img
    else:
        if updateFakeCamImage.value:
            if currentFakeImageIndex >= len(debugImagePaths):
                print(f"----- End of debug images ----- ")
                return None

            imagePath = debugImagePaths[currentFakeImageIndex]
            raw_capture = cv2.imread(imagePath)
            if raw_capture is None:
                print(f"Couldn't read image: {imagePath}")
                currentFakeImageIndex += 1
                return None

            cv2_img = cv2.resize(raw_capture, (camera_x, camera_y))
            cv2.imwrite("/home/raspberrypi/Airborne_Rescue_Line_2025/Latest_Frames/latest_frame_original.jpg", cv2_img)
            print(f"Processing debug image {currentFakeImageIndex + 1}/{len(debugImagePaths)} at  {time.perf_counter()}: {imagePath}")
            updateFakeCamImage.value = False

            currentFakeImageIndex += 1
            return cv2_img

        else:
            cv2_img = raw_capture.copy()
            return cv2_img


def drawAngleLine(img, angle_rad, length=100, color=(0, 255, 0), thickness=2):
    """
    Draw a line on img representing angle_rad (in radians).
    
    The line starts from the bottom-center of the image and extends `length` pixels
    in the direction of angle_rad (where 0 rad points to the right).
    
    Args:
        img (np.ndarray): The image to draw on.
        angle_rad (float): Angle in radians (0 is to the right, positive CCW).
        length (int): Length of the line in pixels.
        color (tuple): BGR color of the line.
        thickness (int): Thickness of the line.
    """
    height, width = img.shape[:2]
    
    # Start point: bottom center
    start_point = (width // 2, height)
    
    # Calculate end point using angle (invert y-axis because image origin is top-left)
    end_x = int(start_point[0] + length * np.cos(angle_rad))
    end_y = int(start_point[1] - length * np.sin(angle_rad))
    
    # Draw the line
    cv2.line(img, start_point, (end_x, end_y), color, thickness)


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
        color = (20, 20, 20)

    for contour in contours:
        contour_size = cv2.contourArea(contour)

        if contour_size > size:
            printDebug(f"Found Big Contour Size {contour_color}; {contour_size}", True)
            x, y, w, h = cv2.boundingRect(contour)
            cv2.rectangle(cv2_img, (x, y), (x + w, y + h), color, 2)
            return True

    return False


def getLineAndCrop(contours_blk):
    global x_last, y_last
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
    blackLineCrop = blackline[np.where(blackline[:, 0, 1] > camera_y * lineCropPercentage.value)]

    cv2.drawContours(cv2_img, blackline, -1, (255, 0, 0), 2)
    cv2.drawContours(cv2_img, blackLineCrop, -1, (255, 255, 0), 2)

    cv2.circle(cv2_img, (int(x_last), int(y_last)), 3, (0, 0, 255), -1)

    return blackline, blackLineCrop


def getLineAndCropOnGap(contours_blk):
    global x_last, y_last

    # Store candidates as (index, top_y, x_mean, y_mean)
    candidates = np.zeros((len(contours_blk), 4), dtype=np.float32)

    for i, contour in enumerate(contours_blk):
        box = cv2.boxPoints(cv2.minAreaRect(contour))
        box = box[box[:, 1].argsort()]  # sort ascending y (top to bottom)

        top_y = np.clip(box[0][1], 0, camera_y)
        bottom_y = np.clip(box[3][1], 0, camera_y)

        box = box[box[:, 0].argsort()]
        x_mean = (np.clip(box[0][0], 0, camera_x) + np.clip(box[3][0], 0, camera_x)) / 2
        y_mean = (top_y + bottom_y) / 2

        candidates[i] = i, top_y, x_mean, y_mean

    # Prefer the contour with the smallest top_y (highest in the image)
    candidates = candidates[candidates[:, 1].argsort()]  # sort by top_y ascending

    chosen = candidates[0]
    idx, _, x_mean, y_mean = chosen

    # Update x_last and y_last so the robot keeps heading forward
    x_last = x_mean
    y_last = y_mean

    blackline = contours_blk[int(idx)]
    blackLineCrop = blackline[np.where(blackline[:, 0, 1] > camera_y * lineCropPercentage.value)]

    # Debug drawing
    cv2.drawContours(cv2_img, blackline, -1, (0, 255, 255), 2)           # cyan contour
    cv2.drawContours(cv2_img, blackLineCrop, -1, (0, 128, 255), 2)       # orange-ish cropped
    cv2.circle(cv2_img, (int(x_last), int(y_last)), 3, (0, 0, 255), -1)  # red dot

    return blackline, blackLineCrop


def calculatePointsOfInterest(blackLine, blackLineCrop, last_bottom_point, averageLinePointX):
    max_gap = 1
    max_line_width = camera_x * .3

    poi_no_crop = np.zeros((4, 2), dtype=np.int32)  # [t, l, r, b]

    # Top without crop
    blackLineYMin = np.amin(blackLine[:, :, 1])
    blackLineTop = blackLine[np.where(blackLine[:, 0, 1] == blackLineYMin)][:, :, 0]

    blackLineTop = blackLineTop[blackLineTop[:, 0].argsort()]
    blacklineTopGapFill = (blackLineTop + max_gap + 1)[:-1]

    blackline_gap_mask = blacklineTopGapFill < blackLineTop[1:]

    top_mean = (int(np.mean(blackLineTop)), blackLineYMin)

    if np.sum(blackline_gap_mask) == 1:
        gap_index = np.where(blackline_gap_mask)[0][0]

        if blackLineTop[:gap_index].size > 0 and blackLineTop[gap_index:].size > 0:
            top_mean_l = int(np.mean(blackLineTop[:gap_index]))
            top_mean_r = int(np.mean(blackLineTop[gap_index:]))

            top_mean = (top_mean_l, blackLineYMin) if np.abs(top_mean_l - averageLinePointX) < np.abs(top_mean_r - averageLinePointX) else (top_mean_r, blackLineYMin)

    poi_no_crop[0] = [top_mean[0], top_mean[1]]

    # Bottom without crop
    blackLineYMax = np.amax(blackLine[:, :, 1])
    blackLineBottom = blackLine[np.where(blackLine[:, 0, 1] == blackLineYMax)][:, :, 0]
    blackLineBottom = blackLineBottom[blackLineBottom[:, 0].argsort()]
    blacklineBottomGapFill = (blackLineBottom + max_gap + 1)[:-1]

    blackline_gap_mask = blacklineBottomGapFill < blackLineBottom[1:]

    bottom_point_mean = (int(np.mean(blackLineBottom)), blackLineYMax)

    if np.sum(blackline_gap_mask) == 1:
        gap_index = np.where(blackline_gap_mask)[0][0]

        if blackLineBottom[:gap_index].size > 0 and blackLineBottom[gap_index:].size > 0:
            bottom_mean_l = int(np.mean(blackLineBottom[:gap_index]))
            bottom_mean_r = int(np.mean(blackLineBottom[gap_index:]))

            if np.abs(bottom_mean_l - bottom_mean_r) > 80:
                if np.abs(bottom_mean_l - last_bottom_point) < np.abs(bottom_mean_r - last_bottom_point):
                    bottom_point_mean = (bottom_mean_l, blackLineYMax)
                    bottom_mean = (bottom_mean_r, blackLineYMax)
                else:
                    bottom_point_mean = (bottom_mean_r, blackLineYMax)
                    bottom_mean = (bottom_mean_l, blackLineYMax)

                poi_no_crop[3] = [bottom_mean[0], bottom_mean[1]]

    bottom_point = [bottom_point_mean[0], bottom_point_mean[1]]

    # Left without crop
    blackline_x_min = np.amin(blackLine[:, :, 0])
    blackline_left = blackLine[np.where(blackLine[:, 0, 0] == blackline_x_min)]
    left_mean = (blackline_x_min, int(np.mean(blackline_left[:, :, 1])))
    poi_no_crop[1] = [left_mean[0], left_mean[1]]

    # Right without crop
    blackline_x_max = np.amax(blackLine[:, :, 0])
    blackline_right = blackLine[np.where(blackLine[:, 0, 0] == blackline_x_max)]
    right_mean = (blackline_x_max, int(np.mean(blackline_right[:, :, 1])))
    poi_no_crop[2] = [right_mean[0], right_mean[1]]

    poi = np.zeros((3, 2), dtype=np.int32)  # [t, l, r]
    is_crop = blackLineCrop.size > 0

    max_black_top = False

    if is_crop:
        # Top
        blackLineYMin = np.amin(blackLineCrop[:, :, 1])
        blackLineTop = blackLineCrop[np.where(blackLineCrop[:, 0, 1] == blackLineYMin)][:, :, 0]
        top_mean = (int(np.mean(blackLineTop)), blackLineYMin)
        poi[0] = [top_mean[0], top_mean[1]]

        blackLineTop = blackLineTop[blackLineTop[:, 0].argsort()]
        max_black_top = bool(np.abs(blackLineTop[0] - blackLineTop[-1]) > max_line_width)

        # Left
        blackline_x_min = np.amin(blackLineCrop[:, :, 0])
        blackline_left = blackLineCrop[np.where(blackLineCrop[:, 0, 0] == blackline_x_min)]
        left_mean = (blackline_x_min, int(np.mean(blackline_left[:, :, 1])))
        poi[1] = [left_mean[0], left_mean[1]]

        # Right
        blackline_x_max = np.amax(blackLineCrop[:, :, 0])
        blackline_right = blackLineCrop[np.where(blackLineCrop[:, 0, 0] == blackline_x_max)]
        right_mean = (blackline_x_max, int(np.mean(blackline_right[:, :, 1])))
        poi[2] = [right_mean[0], right_mean[1]]

    # Poi = [Top, Left, Right, Bottom]
    # Poi Cropped = [Top, Left, Right]
    return poi, poi_no_crop, is_crop, max_black_top, bottom_point


def interpretPOI(poi, poi_no_crop, is_crop, max_black_top, bottom_point, averageLineAngleNormalized, turn_direction, last_bottom_point, averageLinePointX, entry):
    global multiple_bottom_side

    black_top = poi_no_crop[0][1] < camera_y * .1
    multiple_bottom = not (poi_no_crop[3][0] == 0 and poi_no_crop[3][1] == 0)

    black_l_high = poi_no_crop[1][1] < camera_y * .5
    black_r_high = poi_no_crop[2][1] < camera_y * .5

    # === ENTRY MODE ===
    if entry:
        final_poi = poi_no_crop[0]
        turnReason.value = "entry"

    # === ACTIVE MULTIPLE BOTTOM (cooldown) ===
    elif not timer_manager.is_timer_expired("multiple_bottom"):
        final_poi = [multiple_bottom_side, camera_y]
        turnReason.value = "multiple_bottom_active"

    # === FORCED TURNS ===
    elif turn_direction in ["left", "right"]:
        index = 1 if turn_direction == "left" else 2
        #final_poi = poi[index] if is_crop else poi_no_crop[index]
        final_poi = ( (poi[index][0] + poi_no_crop[index][0]) / 2, (poi[index][1] + poi_no_crop[index][1]) / 2  ) if is_crop else poi_no_crop[index]
        turnReason.value = f"forced_turn_{turn_direction}"

    # === DEFAULT TRACKING LOGIC ===
    else:
        if black_top:
            final_poi = poi[0] if is_crop and not max_black_top else poi_no_crop[0]
            turnReason.value = "black_top_default"

            # Check for two lines at bottom
            if (
                (poi_no_crop[1][0] < camera_x * 0.05 and poi_no_crop[1][1] > camera_y * (lineCropPercentage.value * .65)) or
                (poi_no_crop[2][0] > camera_x * 0.95 and poi_no_crop[2][1] > camera_y * (lineCropPercentage.value * .65))
            ):
                final_poi = poi_no_crop[0]
                turnReason.value = "black_top_with_sides"

                if black_l_high or black_r_high:
                    near_high_index = 0

                    if black_l_high and not black_r_high:
                        near_high_index = 1
                    elif not black_l_high and black_r_high:
                        near_high_index = 2
                    elif black_l_high and black_r_high:
                        if abs(poi_no_crop[1][0] - averageLinePointX) < abs(poi_no_crop[2][0] - averageLinePointX):
                            near_high_index = 1
                        else:
                            near_high_index = 2

                    if abs(poi_no_crop[near_high_index][0] - averageLinePointX) < abs(poi_no_crop[0][0] - averageLinePointX):
                        final_poi = poi_no_crop[near_high_index]
                        turnReason.value = f"black_top_closer_{near_high_index}"

        else:
            final_poi = poi[0] if is_crop else poi_no_crop[0]
            turnReason.value = "bottom_default"

            if (
                poi_no_crop[1][0] < camera_x * 0.05 and
                poi_no_crop[2][0] > camera_x * 0.95 and
                timer_manager.is_timer_expired("multiple_side_r") and
                timer_manager.is_timer_expired("multiple_side_l")
            ):
                if averageLineAngleNormalized >= 0:
                    index = 2
                    timer_manager.set_timer("multiple_side_r", 0.6)
                    turnReason.value = "detected_double_side_right"
                else:
                    index = 1
                    timer_manager.set_timer("multiple_side_l", 0.6)
                    turnReason.value = "detected_double_side_left"

                #final_poi = poi[index] if is_crop else poi_no_crop[index]
                final_poi = ( (poi[index][0] + poi_no_crop[index][0]) / 2, (poi[index][1] + poi_no_crop[index][1]) / 2  ) if is_crop else poi_no_crop[index]

            elif not timer_manager.is_timer_expired("multiple_side_l"):
                #final_poi = poi[1] if is_crop else poi_no_crop[1]
                final_poi = ( (poi[1][0] + poi_no_crop[1][0]) / 2, (poi[1][1] + poi_no_crop[1][1]) / 2 ) if is_crop else poi_no_crop[1]
                turnReason.value = "left_side_still_active"

            elif not timer_manager.is_timer_expired("multiple_side_r"):
                #final_poi = poi[2] if is_crop else poi_no_crop[2]
                final_poi = ( (poi[2][0] + poi_no_crop[2][0]) / 2, (poi[2][1] + poi_no_crop[2][1]) / 2 ) if is_crop else poi_no_crop[2]
                turnReason.value = "right_side_still_active"

            elif poi_no_crop[1][0] < camera_x * 0.05:
                #final_poi = poi[1] if is_crop else poi_no_crop[1]
                final_poi = ( (poi[1][0] + poi_no_crop[1][0]) / 2, (poi[1][1] + poi_no_crop[1][1]) / 2 ) if is_crop else poi_no_crop[1]
                turnReason.value = "left_line_edge"

            elif poi_no_crop[2][0] > camera_x * 0.95:
                #final_poi = poi[2] if is_crop else poi_no_crop[2]
                final_poi = ( (poi[2][0] + poi_no_crop[2][0]) / 2, (poi[2][1] + poi_no_crop[2][1]) / 2 ) if is_crop else poi_no_crop[2]
                turnReason.value = "right_line_edge"

            elif multiple_bottom and timer_manager.is_timer_expired("multiple_bottom"):
                if poi_no_crop[3][0] < bottom_point[0]:
                    final_poi = [0, camera_y]
                    multiple_bottom_side = 0
                    turnReason.value = "multi_bottom_chosen_left"
                else:
                    final_poi = [camera_x, camera_y]
                    multiple_bottom_side = camera_x
                    turnReason.value = "multi_bottom_chosen_right"
                timer_manager.set_timer("multiple_bottom", 0.6)

    #return np.deg2rad(int((final_poi[0] - camera_x / 2) / (camera_x / 2) * 180)), final_poi, bottom_point
    dy = final_poi[1] - bottom_point[1]
    dx = final_poi[0] - bottom_point[0]
    lineAngleNormalized = int((final_poi[0] - camera_x / 2) / (camera_x / 2) * 180)
    lineAngle = - np.arctan2(dy, dx)
    lineAngle = np.pi / 2 if lineAngle == 0 else lineAngle
    return lineAngleNormalized, lineAngle, final_poi, bottom_point
    

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
    
    if np.any(green_box[:,1] > camera_y * 0.98): # If marker to close to the bottom black detection is unstable
        skip_bottom_check = True
    else:
        skip_bottom_check = False

    # Bottom
    roi_b = blackImage[int(green_box[2][1]):np.minimum(int(green_box[2][1] + (marker_height * marker_height_search_factor)), camera_y), np.minimum(int(green_box[2][0]), int(green_box[3][0])):np.maximum(int(green_box[2][0]), int(green_box[3][0]))]
    if roi_b.size > 0:
        if np.mean(roi_b[:]) > roi_mean_comparison and not skip_bottom_check:
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
        markerToHighDebug.value = y_center < bottom_percent_threshold
        if y_center < bottom_percent_threshold:
            #print(f"Here {y_center} {bottom_percent_threshold}")
            continue
            

        green_box = cv2.boxPoints(cv2.minAreaRect(contour))
        draw_box = np.intp(green_box)
        cv2.drawContours(cv2_img, [draw_box], -1, (0, 0, 255), 2)

        black_around_sign = checkBlack(black_around_sign, i, green_box)
        b, t, l, r, lp = black_around_sign[i]
        #print(f"[Contour {i}] black: top={t}, bottom={b}, left={l}, right={r}, low_pos={lp}")   

    turn_left, turn_right, left_bottom, right_bottom = determineTurnDirection(black_around_sign)
    #print("Decision:", turn_left, turn_right, left_bottom, right_bottom)

    #if turn_left and not turn_right and not left_bottom: Francisco Check
    if turn_left and not turn_right:
        return "left"
    #elif turn_right and not turn_left and not right_bottom: Francisco Check
    elif turn_right and not turn_left:
        return "right"
    #elif turn_left and turn_right and not (left_bottom and right_bottom): Francisco Check
    elif turn_left and turn_right:
        return "uTurn"
    else:
        return "straight"


def intersectionDetector():
    global greenImage, blackImage
    contoursGreen, _ = cv2.findContours(greenImage, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)

    if len(contoursGreen) > 0:
        #turnDirection.value = checkGreen(contoursGreen)
        return checkGreen(contoursGreen)

    else:
        #turnDirection.value = "straight"
        return "straight"


def average_direction(turn_direction):
    turn_dir_num = 0

    if turn_direction == "left":
        turn_dir_num = -1
    elif turn_direction == "right":
        turn_dir_num = 1

    return turn_dir_num


def updateTurnDirectionAndCrop(time_turn_direction, turn_direction, ramp_up):
    """
    Update turn direction history, trigger forced turn timers, and return new line crop value.

    Parameters:
    - time_turn_direction: np.ndarray, time-value array of recent turn directions
    - turn_direction: float, current detected turn direction
    - ramp_up: bool, whether the robot is on a ramp up

    Returns:
    - updated time_turn_direction (np.ndarray)
    - turnDirectionToSet (float)
    - lineCropPercentageToSet (float)
    """

    # Step 1: Add new value to array
    time_turn_direction = addNewTimeValue(time_turn_direction, average_direction(turn_direction))

    # Step 2: Calculate average turn direction over last 0.2 seconds
    avg_turn_dir = calculateAverageArray(time_turn_direction, 0.2)

    # Step 3: Trigger appropriate forced turn timers
    if avg_turn_dir > 0.1:
        if ramp_up:
            timer_manager.set_timer("right_marker_up", 0.8)
        else:
            timer_manager.set_timer("right_marker", 0.5)
    elif avg_turn_dir < -0.1:
        if ramp_up:
            timer_manager.set_timer("left_marker_up", 0.8)
        else:
            timer_manager.set_timer("left_marker", 0.5)

    # Step 4: Decide line crop based on active timers
    turning_right = not timer_manager.is_timer_expired("right_marker")
    turning_right_up = not timer_manager.is_timer_expired("right_marker_up")
    turning_left = not timer_manager.is_timer_expired("left_marker")
    turning_left_up = not timer_manager.is_timer_expired("left_marker_up")

    if (turning_right or turning_right_up) and not turn_direction == "uTurn" and avg_turn_dir >= 0 and not ramp_up:
        turnDirectionToSet = "right"
        lineCropToSet = default_crop
    elif (turning_right or turning_right_up) and not turn_direction == "uTurn" and avg_turn_dir >= 0 and ramp_up:
        turnDirectionToSet = "right"
        lineCropToSet = turn_crop
    elif (turning_left or turning_left_up) and not turn_direction == "uTurn" and avg_turn_dir <= 0 and not ramp_up:
        turnDirectionToSet = "left"
        lineCropToSet = default_crop
    elif (turning_left or turning_left_up) and not turn_direction == "uTurn" and avg_turn_dir <= 0 and ramp_up:
        turnDirectionToSet = "left"
        lineCropToSet = turn_crop
    else:
        turnDirectionToSet = turn_direction
        lineCropToSet = turn_crop if ramp_up or wasOnRamp.value else default_crop 

    return time_turn_direction, turnDirectionToSet, lineCropToSet


def checkContours(contours, image, color, size=5000):
    if len(contours) > 0:
        largest_contour = max(contours, key=cv2.contourArea)

        if cv2.contourArea(largest_contour) > size:
            x, y, w, h = cv2.boundingRect(largest_contour)
            cv2.rectangle(image, (x, y), (x + w, y + h), color, 2)

            box_width_center = x + w // 2

            #return (box_width_center - (camera_x // 2)) / (camera_x // 2) * 180, abs(h)
            printDebug(f"Found {'Alive' if color == (0, 0, 255) else 'Red' if color == (0, 255, 0) else 'unknown'} Evacuation Corner", False)
            return box_width_center, abs(h)


    return 0, 0 # (meaning it turns left as a safety for control)


def updateCornerDetection(contours, color):
    global cornerCenterArrayGreen, cornerHeightArrayGreen
    rawCenter, rawHeight = checkContours(contours, cv2_img, color)

    # Save values over time
    cornerCenterArrayGreen = addNewTimeValue(cornerCenterArrayGreen, rawCenter)
    cornerHeightArrayGreen = addNewTimeValue(cornerHeightArrayGreen, rawHeight)

    # Set averaged values
    cornerCenter.value = calculateAverageArray(cornerCenterArrayGreen, 0.25)
    cornerHeight.value = calculateAverageArray(cornerHeightArrayGreen, 0.25)


def getGreenContours(green_image):
    green_image = cv2.erode(green_image, kernel, iterations=5)
    green_image = cv2.dilate(green_image, kernel, iterations=8)

    contoursGreen, _ = cv2.findContours(green_image, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)

    return contoursGreen


def getRedContours(red_image):
    red_image = cv2.erode(red_image, kernel, iterations=5)
    red_image = cv2.dilate(red_image, kernel, iterations=8)

    contoursRed, _ = cv2.findContours(red_image, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)

    return contoursRed


def obstacleController():
    pass


def silverDetector(modelSilverLine, original_cv2_img):
    global cv2_img, doInferenceCounter, silverValueArray
    if doInferenceCounter >= doInferenceLimit and LOPstate.value == 0:
        results = modelSilverLine.predict(raw_capture, imgsz=128, conf=0.4, workers=4, verbose=False)
        result = results[0].numpy()

        confidences = result.probs.top5conf
        rawSilverValue = round(confidences[0] if result.probs.top1 == 1 else confidences[1], 3)  # 0 = Line, 1 = Silver

        silverValueArray = addNewTimeValue(silverValueArray, rawSilverValue)# Add value to Array
        silverValueAverage = calculateAverageArray(silverValueArray, 0.75) # Average Array

        doInferenceCounter = 0

        # Debug
        if silverValue.value > 0.5:
            cv2.circle(cv2_img, (10, camera_y - 10), 5, (255, 255, 255), -1, cv2.LINE_AA)
            if not computerOnlyDebug and not silverDatasetCollectionMode:
                saveFrame.value = True
                savecv2_img("Silver", original_cv2_img)
        silverValueDebug.value = rawSilverValue
        silverValueArrayDebug.value = calculateAverageArray(silverValueArray, 0.75) # Average Array

        if rawSilverValue > 0.5 and not silverDatasetCollectionMode:
            saveFrame.value = True
            savecv2_img("Silver", original_cv2_img)
            printDebug(f"Simple Silver Line Detected at {time.perf_counter()}: {rawSilverValue}, AVG: {silverValueAverage}", False)

        return silverValueAverage

    doInferenceCounter += 1
    return silverValue.value


def checkImageSimilarity():
    global imageSimilarityArray, checkSimilarityCounter, lastImage
    if checkSimilarityCounter >= checkSimilarityLimit:
        greyImage = cv2.cvtColor(cv2_img, cv2.COLOR_BGR2GRAY)
        imageSimilarity = structural_similarity(greyImage, lastImage)
        lastImage = greyImage.copy()
        checkSimilarityCounter = 0

        imageSimilarityArray = addNewTimeValue(imageSimilarityArray, imageSimilarity)
        imageSimilarityAverage.value = calculateAverageArray(imageSimilarityArray, 10)

    checkSimilarityCounter += 1


def getGapAngle(box):
    box = box[box[:, 1].argsort()]  # Sort by Y (top-bottom)

    vector = box[0] - box[1]
    angle = np.arccos(np.dot(vector, [1, 0]) / (np.linalg.norm(vector))) * 180 / np.pi

    angle = angle if box[0][0] < box[1][0] else -angle
    if angle == 180:
        angle = 0

    angle = 90 - angle  # Rotate to make 0º = vertical

    return box[0], box[1], angle


def getSilverAngle(box):
    box = box[box[:, 0].argsort()]  # Sort by X (left-right)

    left_points = box[:2]
    right_points = box[2:]

    left_points = left_points[left_points[:, 1].argsort()]
    right_points = right_points[right_points[:, 1].argsort()]

    vector = left_points[0] - right_points[0]
    angle = np.arccos(np.dot(vector, [1, 0]) / (np.linalg.norm(vector))) * 180 / np.pi

    angle = -angle if left_points[0][1] < right_points[0][1] else angle
    if angle == 180:
        angle = 0

    # Normalize angle to [-90, 90]
    if angle > 90:
        angle -= 180
    elif angle < -90:
        angle += 180

    return left_points[0], right_points[0], angle


#############################################################################
#                            Line Camera Loop
#############################################################################

def lineCamLoop():
    global cv2_img, blackImage, greenImage, redImage, x_last, y_last, ballCenterXArray, ballBottomYArray, ballWidthArray, ballTypeArray, ballExistsArray, silverValueArray, redValueArray
    global TurnDirectionArray, LineAngleNormalizedArray, LineAngleArray, BottomPointXArray, LinePointXArray, imageSimilarityArray

    #modelVictim = YOLO('/home/raspberrypi/Airborne_Rescue_Line_2025/Ai/models/ball_zone_s/ball_detect_s_edgetpu.tflite', task='detect')
    #modelVictim = YOLO('/home/raspberrypi/Airborne_Rescue_Line_2025/Ai/models/victim_ball_detection_v3/victim_ball_detection_int8_edgetpu.tflite', task='detect')
    #modelVictim = YOLO('/home/raspberrypi/Airborne_Rescue_Line_2025/Ai/models/victim_ball_detection_v3/victim_ball_detection_full_integer_quant_edgetpu.tflite', task='detect')
    #modelVictim = YOLO('/home/raspberrypi/Airborne_Rescue_Line_2025/Ai/models/victim_ball_detection_v7/victim_ball_detection_full_integer_quant_edgetpu.tflite', task='detect')
    #modelVictim = YOLO('/home/raspberrypi/Airborne_Rescue_Line_2025/Ai/models/victim_ball_detection_v7.1/victim_ball_detection_full_integer_quant_edgetpu.tflite', task='detect')
    #modelVictim = YOLO('/home/raspberrypi/Airborne_Rescue_Line_2025/Ai/models/victim_ball_detection_v7.1/victim_ball_detection_full_integer_quant_with_metadata_edgetpu.tflite', task='detect')
    #modelVictim = YOLO('/home/raspberrypi/Airborne_Rescue_Line_2025/Ai/models/victim_ball_detection_v7.1/victim_ball_detection.pt', task='detect')
    #modelVictim = YOLO('/home/raspberrypi/Airborne_Rescue_Line_2025/Ai/models/victim_ball_detection_v7.2/victim_ball_detection_full_integer_quant_edgetpu.tflite', task='detect') # Used ultralytics 8.3.66 (nms not an argument)
    #modelVictim = YOLO('/home/raspberrypi/Airborne_Rescue_Line_2025/Ai/models/victim_ball_detection_v7.3/victim_ball_detection_full_integer_quant_edgetpu.tflite', task='detect') # Used format = edgetpu
    #modelVictim = YOLO('/home/raspberrypi/Airborne_Rescue_Line_2025/Ai/models/victim_ball_detection_v7.4/victim_ball_detection_full_integer_quant_edgetpu.tflite', task='detect') # Used format = edgetpu
    #modelVictim = YOLO('Ai/models/victim_ball_detection_v8/victim_ball_detection_v8_yolov8s_edgetpu.tflite', task='detect') # Used format = edgetpu
    modelVictim = YOLO('Ai/models/victim_ball_detection_v9/victim_ball_detection_v9_edgetpu.tflite', task='detect') # Used format = edgetpu

    #modelSilverLine = YOLO('/home/raspberrypi/Airborne_Rescue_Line_2025/Ai/models/silver_zone_entry/silver_classify_s.onnx', task='classify')
    #modelSilverLine = YOLO('/home/raspberrypi/Airborne_Rescue_Line_2025/Ai/models/silver_strip/SilverStripDetection.onnx', task='classify')
    #modelSilverLine = YOLO('Ai/models/silver_zone_entry_v2/silver_classify_s.onnx', task='classify')
    modelSilverLine = YOLO('Ai/models/silver_strip_v4/SilverStripDetection.onnx', task='classify')
    
    camera = None # PlaceHolder for Debugging
    if not cameraDebugMode:
        camera = Picamera2(0)

        mode = camera.sensor_modes[0]
        camera.configure(camera.create_video_configuration(sensor={'output_size': mode['size'], 'bit_depth': mode['bit_depth']}))

        #camera.set_controls({"AfMode": controls.AfModeEnum.Manual, "ExposureTime":10000})
        camera.set_controls({
            #"AfMode": controls.AfModeEnum.Manual,
            #"LensPosition": 6.5,
            "FrameDurationLimits": (1000000 // 50, 1000000 // 50),
            #"AnalogueGain": 3.0,  # Fix gain (default 1.0)
            #"ExposureTime": 10000  # Set exposure in microseconds (adjust as needed)
        })

        camera.start()
        time.sleep(0.1)

    x_last = int( camera_x / 2 )
    y_last = int( camera_y / 2 )
    lastBottomPoint_x = camera_x / 2
    lastLinePoint = [x_last, y_last] # center points 

    last_best_box = None

    timer_manager.add_timer("image_similarity", .5)
    timer_manager.add_timer("multiple_bottom", .05)
    timer_manager.add_timer("multiple_side_l", .05)
    timer_manager.add_timer("multiple_side_r", .05)
    timer_manager.add_timer("right_marker", .05)
    timer_manager.add_timer("left_marker", .05)
    timer_manager.add_timer("right_marker_up", .05)
    timer_manager.add_timer("left_marker_up", .05)
    timer_manager.add_timer("turn_persistence_timer", .05)  # Initialize if not present

    timer_manager.add_timer("continueTurnIntersection", 0.05)
    timer_manager.add_timer("uTurn", 0.05)
    timer_manager.add_timer("rightLeft", 0.05)
    timer_manager.add_timer("rightRight", 0.05)
    timer_manager.add_timer("goToBall", 0.05)
    timer_manager.add_timer("saveImageCoolDown", 0.05)


    t0 = time.perf_counter()
    while not terminate.value:
        t1 = t0 + lineDelayMS * 0.001
        t0Real = time.perf_counter()

        # Loop
        cv2_img = getCameraImage(camera)
        original_cv2_img = cv2_img.copy()

        savecv2_img("Silver", cv2_img)

        resetBallArrayVars() # Reset ball arrays if needed
        resetEvacZoneArrayVars() # Reset evacuation zone corner arrays if needed
        resetImageSimilarityArrayVars() # Reset image similarity array if needed


        # Image Similarity (Stuck Detection)
        checkImageSimilarity()

        if objective.value == "follow_line":
            # Color Processing
            hsvImage = cv2.cvtColor(cv2_img, cv2.COLOR_BGR2HSV)
            greenImage = cv2.inRange(hsvImage, green_min, green_max)
            redImage = cv2.inRange(hsvImage, red_min_1, red_max_1) + cv2.inRange(hsvImage, red_min_2, red_max_2)
            
            # Black Processing
            grayImage = cv2.cvtColor(cv2_img, cv2.COLOR_BGR2GRAY)
            _, blackImage = cv2.threshold(grayImage, blackThreshold, 255, cv2.THRESH_BINARY_INV)
            #blackImage = cv2.inRange(cv2_img, black_min, black_max_normal_bottom)
            blackImage[0:int(camera_y * black_top_threshold_percentage), 0:camera_x] = cv2.inRange(cv2_img, black_min, black_max_normal_top)[0:int(camera_y * black_top_threshold_percentage), 0:camera_x]
            

            blackImage -= greenImage
            blackImage = ignoreHighFOVCorners(blackImage)

            # Noise Reduction
            blackImage = cv2.erode(blackImage, kernel, iterations=5)
            blackImage = cv2.dilate(blackImage, kernel, iterations=17) # Previous values: 12 | 16
            blackImage = cv2.erode(blackImage, kernel, iterations=9)  # Previous values: 4 | 8

            greenImage = cv2.erode(greenImage, kernel, iterations=1)
            greenImage = cv2.dilate(greenImage, kernel, iterations=11)
            greenImage = cv2.erode(greenImage, kernel, iterations=9)
                                    
            redImage = cv2.erode(redImage, kernel, iterations=1)
            redImage = cv2.dilate(redImage, kernel, iterations=11)
            redImage = cv2.erode(redImage, kernel, iterations=9)


            # -- SILVER Line --
            silverValue.value = silverDetector(modelSilverLine, original_cv2_img)
           
            
            # -- INTERSECTIONS -- Deal with intersections
            #intersectionDetector()
            turn_direction = intersectionDetector()
            TurnDirectionArray, turnDirection.value, lineCropPercentage.value = updateTurnDirectionAndCrop(TurnDirectionArray, turn_direction, rampUp.value)


            # -- RED STRIP -- Check for Red Line - Stop
            contoursRed, _ = cv2.findContours(redImage, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
            redCurrentValue = 1 if checkContourSize(contoursRed) else 0 

            redValueArray = addNewTimeValue(redValueArray, redCurrentValue)
            redValue.value = calculateAverageArray(redValueArray, 0.35)


            # -- Black Line --
            # Get Black Contours
            contoursBlack, _ = cv2.findContours(blackImage, cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)
            
            if len(contoursBlack) > 0:
                # Calculate Black Line (cropped and not) + Points of Interest
                if gapCorrectionActive.value and False: # Temporary fix
                    blackLine, blackLineCrop = getLineAndCropOnGap(contoursBlack)
                else:
                    blackLine, blackLineCrop = getLineAndCrop(contoursBlack)

                lineDetected.value = True
                poiCropped, poi, isCrop, maxBlackTop, bottomPoint = calculatePointsOfInterest(blackLine, blackLineCrop, lastBottomPoint_x, lastLinePoint[0])

                # Get smoothed/averaged values
                averageLineAngleNormalized = calculateAverageArray(LineAngleNormalizedArray, 0.3)
                averageLineAngle = calculateAverageArray(LineAngleArray, 0.3)
                averageBottomPoint = calculateAverageArray(BottomPointXArray, 0.15)
                averageLinePointX = calculateAverageArray(LinePointXArray, 0.15)
                
                # Use the averaged values
                lineAngleNormalized, lineAngle2, finalPoi, bottomPoint = interpretPOI(
                    poiCropped, poi, isCrop, maxBlackTop, bottomPoint,
                    averageLineAngleNormalized, turnDirection.value,
                    averageBottomPoint, averageLinePointX, entry=False
                )
                lineAngleNormalizedDebug.value = averageLineAngleNormalized
                lineAngle.value = lineAngle2  # Or raw angle if you prefer
                lineCenterX.value = finalPoi[0]
                lineBottomY.value = bottomPoint[1]
                isCropped.value = isCrop

                # Update time arrays
                LineAngleNormalizedArray = addNewTimeValue(LineAngleNormalizedArray, lineAngleNormalized)
                LineAngleArray = addNewTimeValue(LineAngleArray, lineAngle2)
                BottomPointXArray = addNewTimeValue(BottomPointXArray, bottomPoint[0])
                LinePointXArray = addNewTimeValue(LinePointXArray, finalPoi[0])

                """
                p1, p2, angle = getGapAngle(cv2.boxPoints(cv2.minAreaRect(blackLine)))
                if p1[1] < camera_y * 0.95 and p2[1] < camera_y * 0.95:
                    gapAngle.value = angle

                    centerGapPoint = (p1 - p2) / 2 + p2

                    gapCenterX.value = centerGapPoint[0]
                    gapCenterY.value = centerGapPoint[1]

                    cv2.line(cv2_img, (int(p1[0]), int(p1[1])), (int(p2[0]), int(p2[1])), (0, 255, 0), 2)
                    cv2.circle(cv2_img, (int(centerGapPoint[0]), int(centerGapPoint[1])), 5, (0, 255, 0), 1, cv2.LINE_AA)"""

                if silverLineDetected.value:
                    p1, p2, angle = getSilverAngle(cv2.boxPoints(cv2.minAreaRect(blackLine)))

                    # The silver line is perpendicular to the black line
                    silverAngle.value = angle

                    centerSilverPoint = (p1 - p2) / 2 + p2

                    silverCenterX.value = centerSilverPoint[0]
                    silverCenterY.value = centerSilverPoint[1]

                    cv2.line(cv2_img, (int(p1[0]), int(p1[1])), (int(p2[0]), int(p2[1])), (255, 0, 255), 2)  # Magenta line for silver
                    cv2.circle(cv2_img, (int(centerSilverPoint[0]), int(centerSilverPoint[1])), 5, (255, 0, 255), 1, cv2.LINE_AA)


                # Update Image
                cv2.circle(cv2_img, (int(poiCropped[0][0]), int(poiCropped[0][1])), 5, (0, 0, 255), -1)
                cv2.circle(cv2_img, (int(poiCropped[1][0]), int(poiCropped[1][1])), 5, (0, 255, 0), -1)
                cv2.circle(cv2_img, (int(poiCropped[2][0]), int(poiCropped[2][1])), 5, (255, 0, 0), -1)

                cv2.circle(cv2_img, (int(poi[0][0]), int(poi[0][1])), 2, (0, 0, 255), -1)
                cv2.circle(cv2_img, (int(poi[1][0]), int(poi[1][1])), 2, (255, 0, 0), -1)
                cv2.circle(cv2_img, (int(poi[2][0]), int(poi[2][1])), 2, (0, 255, 0), -1)

                cv2.circle(cv2_img, (int(bottomPoint[0]), int(bottomPoint[1])), 5, (0, 255, 255), -1)

                cv2.circle(cv2_img, (int(finalPoi[0]), int(finalPoi[1])), 10, (0, 0, 255), -1)

            else: # No Black Contours / Line
                lineDetected.value = False

            obstacleController()

            #savecv2_img("VictimsDataSet", cv2_img)
            

        elif objective.value == "zone":
            # Color Processing
            hsvImage = cv2.cvtColor(cv2_img, cv2.COLOR_BGR2HSV)
            greenImage = cv2.inRange(hsvImage, evacZoneGreenMin, evacZoneGreenMax)
            redImage = cv2.inRange(hsvImage, evacZoneRedMin_1, evacZoneRedMax_1) + cv2.inRange(hsvImage, evacZoneRedMin_2, evacZoneRedMax_2)
            
            # Black Processing
            grayImage = cv2.cvtColor(cv2_img, cv2.COLOR_BGR2GRAY)
            _, blackImage = cv2.threshold(grayImage, blackThreshold, 255, cv2.THRESH_BINARY_INV)
            
            blackImage = ignoreHighFOVCorners(blackImage)

            #if zoneStatus.value in ["begin", "entry", "findVictims", "goToBall", "exit"] and not pickingVictim.value and not cameraServoAngle.value == CAMERA_LINE_ANGLE:
            if zoneStatus.value in ["begin", "entry", "findVictims", "goToBall"] and not pickingVictim.value and not cameraServoAngle.value == CAMERA_LINE_ANGLE:
                img_rgb = cv2.cvtColor(cv2_img, cv2.COLOR_BGR2RGB)
                try:
                    results = modelVictim.predict(img_rgb, imgsz=448, conf=0.3, iou=0.2, agnostic_nms=True, workers=4, verbose=False)
                except ValueError as e:
                    print(f"[lineCamLoop] EdgeTPU error: {e}")
                    modelVictim = YOLO('Ai/models/victim_ball_detection_v9/victim_ball_detection_v9_edgetpu.tflite', task='detect')
                    results = None
                    continue
                #results = modelVictim.predict(img_rgb, imgsz=448, conf=0.3, iou=0.2, agnostic_nms=True, workers=4, verbose=False)  # verbose=True to enable debug info
                #results = modelVictim.predict(img_rgb, save=True, save_txt=True, imgsz=448, conf=0.3, iou=0.2, agnostic_nms=True, workers=4, verbose=False)
                
                result = results[0].numpy()

                boxes = []
                for box in result.boxes:
                    x1, y1, x2, y2 = box.xyxy[0].astype(int)
                    class_id = box.cls[0].astype(int)
                    name = "black ball" if class_id == 0 else "silver ball" if class_id == 1 else "unknown"
                    #name = result.names[class_id]
                    confidence = box.conf[0].astype(float)

                    ballConfidence.value = confidence

                    width = x2 - x1
                    height = y2 - y1
                    area = width * height
                    distance = (x1 + x2) // 2

                    boxes.append([area, distance, name, width, y2, class_id])

                    color = colors(class_id, True)
                    cv2.rectangle(cv2_img, (x1, y1), (x2, y2), color, 2)
                    cv2.putText(cv2_img, f"{name}: {confidence:.2f}", (x1, y1 - 5), cv2.FONT_HERSHEY_DUPLEX, 0.5, color, 1, cv2.LINE_AA)

                #print(f"boxes {len(boxes)} {boxes}")
                if len(boxes) > 0:
                    best_box = max(boxes, key=lambda x: x[0])
                    if last_best_box is not None:
                        best_box = min(boxes, key=lambda x: abs(x[1] - last_best_box[1]))

                    last_best_box = best_box

                    # Update arrays with the current values and store the timestamped data
                    ballCenterXArray = addNewTimeValue(ballCenterXArray, best_box[1])
                    ballBottomYArray = addNewTimeValue(ballBottomYArray, best_box[4])
                    ballWidthArray = addNewTimeValue(ballWidthArray, best_box[3])
                    ballTypeArray = addNewTimeValue(ballTypeArray, best_box[5])
                    ballExistsArray = addNewTimeValue(ballExistsArray, 1)

    
                else:
                    ballCenterXArray = addNewTimeValue(ballCenterXArray, camera_x // 2)
                    ballBottomYArray = addNewTimeValue(ballBottomYArray, camera_y // 2)
                    ballWidthArray = addNewTimeValue(ballWidthArray, 0)
                    ballTypeArray = addNewTimeValue(ballTypeArray, 0.5)
                    ballExistsArray = addNewTimeValue(ballExistsArray, 0)


                ballCenterX.value = calculateAverageArray(ballCenterXArray, 0.15)
                ballBottomY.value = calculateAverageArray(ballBottomYArray, 0.25)
                ballWidth.value = calculateAverageArray(ballWidthArray, 0.25)
                ballType.value = "black ball" if calculateAverageArray(ballTypeArray, 0.45) < 0.5 else "silver ball" # Maybe needs rechecking...
                ballExists.value = calculateAverageArray(ballExistsArray, 0.25) >= 0.5 # [0.5, 1.0] = Ball Exist True [0.0, 0.5[ = False


            elif zoneStatus.value == "depositGreen":
                contoursGreen = getGreenContours(greenImage)
                updateCornerDetection(contoursGreen, (0, 0, 255))

            elif zoneStatus.value == "depositRed":
                contoursRed = getRedContours(redImage)
                updateCornerDetection(contoursRed, (0, 255, 0))

            if zoneStatus.value == "exit":
                contoursBlack, _ = cv2.findContours(blackImage, cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)
                contoursGreen = getGreenContours(greenImage)
                contoursRed = getRedContours(redImage)

                zoneFoundBlack.value = checkContourSize(contoursBlack, contour_color="black", size=16500)
                zoneFoundGreen.value = checkContourSize(contoursGreen, contour_color="green", size=30000)
                zoneFoundRed.value = checkContourSize(contoursRed, contour_color="red", size=30000)

                # -- SILVER Line --
                silverValue.value = silverDetector(modelSilverLine, original_cv2_img)



        cv2.imwrite("/home/raspberrypi/Airborne_Rescue_Line_2025/Latest_Frames/latest_frame_cv2.jpg", cv2_img)
        cv2.imwrite("/home/raspberrypi/Airborne_Rescue_Line_2025/Latest_Frames/latest_frame_hsv.jpg", hsvImage)
        cv2.imwrite("/home/raspberrypi/Airborne_Rescue_Line_2025/Latest_Frames/latest_frame_green.jpg", greenImage)
        cv2.imwrite("/home/raspberrypi/Airborne_Rescue_Line_2025/Latest_Frames/latest_frame_black.jpg", blackImage)
        cv2.imwrite("/home/raspberrypi/Airborne_Rescue_Line_2025/Latest_Frames/latest_frame_red.jpg", redImage)


        while (time.perf_counter() <= t1):
            time.sleep(0.0005)

        elapsed_time = time.perf_counter() - t0Real
        if lineDelayMS * 0.001 - elapsed_time > 0:
            time.sleep(lineDelayMS * 0.001 - elapsed_time)

        # === Frequency Measurement ===
        loop_duration = time.perf_counter() - t0Real
        if loop_duration > 0:
            lineCamLoopFrequency.value = 1.0 / loop_duration
        else:
            lineCamLoopFrequency.value = 0  # Avoid division by zero

        printDebug(f"Line Frequency: {lineCamLoopFrequency.value} Hz", DEBUG)
        printDebug(f"\t\t\t\t\t\t\t\tLine Cam Loop Time: {t0} | {t1} | {time.perf_counter()}", False)

        t0 = t1


    print(f"Shutting Down Line Cam Loop")
    if not cameraDebugMode: 
        camera.stop()
