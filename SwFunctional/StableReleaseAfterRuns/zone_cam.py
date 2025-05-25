import time
import cv2
from ultralytics import YOLO

# Measure the model loading time
start_model_load = time.time()

# Load the model (only once)
model = YOLO('/home/raspberrypi/Airborne_Rescue_Line_2025/Ai/models/ball_zone_s/ball_detect_s_edgetpu.tflite', task='detect')

end_model_load = time.time()
model_load_time = end_model_load - start_model_load
print(f"Model loading time: {model_load_time:.4f} seconds")

# Load an image
cv2_img = cv2.imread("/home/raspberrypi/Airborne_Rescue_Line_2025/Latest_Frames/latest_frame_original.jpg")

# Measure the inference time after model is loaded
start_inference = time.time()

# Run inference
#results = model.predict(cv2_img, imgsz=(512, 224), conf=0.3, iou=0.2, agnostic_nms=True, workers=4, verbose=True)

# Measure inference time in a loop
for i in range(10):
    start_inference = time.time()
    results = model.predict(cv2_img, imgsz=(512, 224), conf=0.3, iou=0.2, agnostic_nms=True, workers=4, verbose=True)
    end_inference = time.time()
    inference_time = end_inference - start_inference
    print(f"Iteration {i+1}: Inference time: {inference_time * 1000:.2f} ms")

end_inference = time.time()
inference_time = end_inference - start_inference

# Print the inference time
#print(f"Inference time: {inference_time * 1000:.2f} ms")

# Results
result = results[0].numpy()

# Print result details
#print(f"Results: {results}")
#print(f"Results 2: {result}")



"""import datetime
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


model = YOLO('/home/raspberrypi/Airborne_Rescue_Line_2025/Ai/models/ball_zone_s/ball_detect_s_edgetpu.tflite', task='detect')

cv2_img = cv2.imread("/home/raspberrypi/Airborne_Rescue_Line_2025/Latest_Frames/latest_frame_original.jpg")

print(f"Results 1:")
results = model.predict(cv2_img, imgsz=(512, 224), conf=0.3, iou=0.2, agnostic_nms=True, workers=4, verbose=False)  # verbose=True to enable debug info

print(f"Results 1:")
result = results[0].numpy()

print(f"Results: {results}")


print(f"results 2 {result}")"""