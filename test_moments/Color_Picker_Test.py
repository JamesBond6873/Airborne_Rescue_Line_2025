import cv2
import numpy as np

image_hsv = None   # global ;(
pixel = (20,60,80) # some stupid default

# mouse callback function
def pick_color(event,x,y,flags,param):
    if event == cv2.EVENT_LBUTTONDOWN:
        pixel = image_hsv[y, x].astype(int)

        #you might want to adjust the ranges(+-10, etc):
        upper =  np.array([pixel[0] + 20, pixel[1] + 20, pixel[2] + 30])
        lower =  np.array([pixel[0] - 30, pixel[1] - 30, pixel[2] - 30])
        lower = np.array([15, 100, 15])
        upper = np.array([90, 200, 105])
        #lower = np.array([0,0,0]) # Black only
        print(pixel, lower, upper)

        image_mask = cv2.inRange(image_hsv,lower,upper)
        cv2.imshow("mask",image_mask)

def main():
    import sys
    global image_hsv, pixel # so we can use it in mouse callback

    image_src = cv2.imread("C:\\Users\\Francisco\\Projects\\RoboCup Junior Rescue Line\\2025\\SoftwareRepo\\test_moments\\latest_frame_cv2_corner2.jpg")  # pick.py my.png
    #image_src = cv2.imread("test_moments\Silver_Line_2.jpg")
    if image_src is None:
        print ("the image read is None............")
        return
    cv2.imshow("bgr",image_src)

    ## NEW ##
    cv2.namedWindow('hsv')
    cv2.setMouseCallback('hsv', pick_color)

    # now click into the hsv img , and look at values:
    image_hsv = cv2.cvtColor(image_src,cv2.COLOR_BGR2HSV)
    cv2.imshow("hsv",image_hsv)

    cv2.waitKey(0)
    cv2.destroyAllWindows()

if __name__=='__main__':
    main()