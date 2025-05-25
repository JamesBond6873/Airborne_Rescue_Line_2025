import cv2
import numpy as np

# Load image
cv2_img = cv2.imread("C:\\Users\\Francisco\\Projects\\RoboCup Junior Rescue Line\\2025\\Frames\\Frames_7Points_Test\\latest_frame_original.jpg")
white_image = cv2.imread("C:\\Users\\Francisco\\Projects\\RoboCup Junior Rescue Line\\2025\\Frames\\Frames_7Points_Test\\White_Image.jpg")

# Convert to grayscale to estimate brightness
gray = cv2.cvtColor(cv2_img, cv2.COLOR_BGR2GRAY)

# Apply Gaussian Blur to get a smooth light distribution
intensity_map = cv2.GaussianBlur(gray, (35, 35), 0)

# Normalize intensity map to avoid division by zero
intensity_map = intensity_map.astype(np.float32) + 1  # Avoid zero division
intensity_map /= np.max(intensity_map)  # Scale to [0,1]

# Convert original image to float32
cv2_img = cv2_img.astype(np.float32)

# Apply pixel-wise division to normalize brightness
corrected_img = cv2_img / intensity_map[..., np.newaxis]

# Normalize back to uint8 (0-255)
corrected_img = cv2.normalize(corrected_img, None, 0, 255, cv2.NORM_MINMAX)
corrected_img = np.clip(corrected_img, 0, 255).astype(np.uint8)

# Save the corrected image
#cv2.imwrite("./InProgress3/latest_frame_corrected.jpg", corrected_img)
# Show the image instead of saving
cv2.imshow("Original", cv2_img)
cv2.imshow("Corrected Image", white_image)
cv2.imshow("Corrected Image", corrected_img)
cv2.waitKey(0)  # Wait indefinitely until a key is pressed
cv2.destroyAllWindows()  # Close the window when a key is pressed
