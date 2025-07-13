import cv2
import numpy as np

image_hsv = None   # global ;(
pixel = (20,60,80) # some stupid default

def pick_color(event, x, y, flags, param):
    global image_hsv
    if event == cv2.EVENT_LBUTTONDOWN:
        pixel = image_hsv[y, x]
        print(f"Clicked pixel at ({x},{y}): HSV={pixel}")

        lower = np.array([0, 0, 0], dtype=np.uint8)
        upper = np.array([
            min(pixel[0] + 15, 179),
            min(pixel[1] + 15, 255),
            min(pixel[2] + 40, 255)
        ], dtype=np.uint8)

        print("lower:", lower, "upper:", upper)

        image_mask = cv2.inRange(image_hsv, lower, upper)
        cv2.imshow("mask", image_mask)


def main():
    import sys
    global image_hsv

    image_src = cv2.imread("C:/Users/Francisco/Projects/RoboCup Junior Rescue Line/2025/SoftwareRepo/SwTest/Image (122).jpg")
    if image_src is None:
        print("the image read is None............")
        return

    # Convert to HSV for internal use
    image_hsv = cv2.cvtColor(image_src, cv2.COLOR_BGR2HSV)

    cv2.namedWindow('image')
    cv2.setMouseCallback('image', pick_color)

    # Show BGR image so it looks correct to you
    cv2.imshow("image", image_src)

    cv2.waitKey(0)
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()