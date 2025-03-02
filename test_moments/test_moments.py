import cv2
import numpy as np

# Load image
cv2_img = cv2.imread("C:\\Users\\Francisco\\Projects\\RoboCup Junior Rescue Line\\2025\\Software_Repo\\test_moments\\Frames01\\image_2025-03-01_18-15-39-198.jpg")
#gray = cv2.cvtColor(cv2_img, cv2.COLOR_BGR2GRAY)
hsv_image = cv2.cvtColor(cv2_img, cv2.COLOR_BGR2HSV)
black_image = cv2.inRange(hsv_image, np.array([0, 0, 0]), np.array([255, 255, 150])) # 180,255,30
"""gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

# Invert colors: Make black lines white and background black
inverted = cv2.bitwise_not(gray)

# Threshold to get binary image (now the black line is detected as white)
_, binary = cv2.threshold(inverted, 127, 255, cv2.THRESH_BINARY)

# Find contours
contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)"""

contours, _ = cv2.findContours(black_image, cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)

# If no contours found, exit
if not contours:
    print("No contours found!")
    exit()

# Select the largest contour based on area (m00)
largest_contour = max(contours, key=cv2.contourArea)

# Create debugging images
contour_debug = cv2_img.copy()  # Contours only
axis_debug = cv2_img.copy()     # Principal axis overlay

# Draw the largest contour
cv2.drawContours(contour_debug, [largest_contour], -1, (0, 255, 0), 2)

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

    # Define line endpoints along the principal axis
    length = 100  # Adjust for visualization
    x1 = int(cx + length * np.cos(theta))
    y1 = int(cy + length * np.sin(theta))
    x2 = int(cx - length * np.cos(theta))
    y2 = int(cy - length * np.sin(theta))

    # Draw centroid
    cv2.circle(axis_debug, (cx, cy), 5, (0, 0, 255), -1)

    # Draw principal axis line
    cv2.line(axis_debug, (x1, y1), (x2, y2), (255, 0, 0), 2)

# Show debugging images
#cv2.imshow("Inverted Image", inverted)
#cv2.imshow("Binary Image", binary)
#cv2.imshow("Gray", gray)
cv2.imshow("HSV", hsv_image)
cv2.imshow("Black", black_image)
cv2.imshow("Largest Contour", contour_debug)
cv2.imshow("Principal Axis", axis_debug)
cv2.waitKey(0)
cv2.destroyAllWindows()
