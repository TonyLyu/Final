import cv2
import detector
import bin
import copy
from image_data import ImageData
import characteran

img = cv2.imread('1.jpg')
img_data = ImageData(img)

img_data.crop_gray = detector.detect(img)[0]
an_img = copy.copy(img_data.crop_gray)
img_data.thresholds = bin.produceThresholds(an_img)

cv2.imwrite("plate.jpg", img_data.crop_gray)
cv2.imwrite("thresh.jpg", img_data.thresholds[0])

characteran.characteranalysis(img_data.crop_gray, img_data.thresholds)

for i in range(0, len(img_data.thresholds)):
    cv2.imshow("%d"%i, img_data.thresholds[i])
    print i
cv2.imshow("12345", img_data.crop_gray)
cv2.waitKey(0)
cv2.destroyAllWindows()

# if len(imgplates) != 0:
#     for imgplate in imgplates:
#         k = 0
#         cv2.imshow('just', imgplate)
#         bin_img = bin.Wolf(imgplate, 3, 18, 18, 0.05 + (k * 0.35), 128)
#         bin_img = cv2.bitwise_not(bin_img)
#         contours = textcontours.getTextContours(bin_img)
#         # cv2.drawContours(bin_img, contours, -1, (0,255,0), 1)
#         textcontours.drawContours(bin_img, contours)
#         cv2.imshow('plate', bin_img)
#         print textcontours.height
#     cv2.waitKey(0)
#     cv2.destroyAllWindows()
#
#
# else:
#     print("no plate")