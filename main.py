
import cv2
import detector
import bin
import copy
from image_data import ImageData
import characteran
from edgefinder import EdgeFinder
from transformation import Transformation
from textline import TextLine
from segment.ocr import OCR
import numpy as np
img = cv2.imread('2.png')
img_data = ImageData(img)
rows, cols = img.shape[:2]
grays, regions = detector.detect(img)
img_data.crop_gray = grays[0]
img_data.regionOfInterest = regions[0]
an_img = copy.copy(img_data.crop_gray)
img_data.thresholds = bin.produceThresholds(an_img)
cv2.imshow("1", img_data.thresholds[0])
cv2.imshow("2", img_data.thresholds[1])
cv2.imshow("3", img_data.thresholds[2])

# cv2.imwrite("plate.jpg", img_data.crop_gray)
# cv2.imwrite("thresh.jpg", img_data.thresholds[0])

img_data = characteran.characteranalysis(img_data)

edgeFinder = EdgeFinder(img_data)
img_data.plate_corners = edgeFinder.findEdgeCorners()
img_data = edgeFinder.img_data
img_data.plate_corners = img_data.plate_corners[0]
expandRegion = img_data.regionOfInterest


imgTransform = Transformation(img_data.grayImg, img_data.crop_gray, expandRegion.x, expandRegion.y, expandRegion.width, expandRegion.height)
orcImageWidthPx = round(120.0 * 1.3333333)
orcImageHeightPx = round(60 * 1.3333333)

cropSize = imgTransform.getCropSize(img_data.plate_corners, (orcImageWidthPx, orcImageHeightPx))
transmtx = imgTransform.getTransformationMatrix1(img_data.plate_corners, cropSize[0], cropSize[1])

projectPoints = copy.deepcopy(img_data.plate_corners)
projectPoints = np.array(projectPoints, np.float32)

img_data.color_deskewed = np.zeros((cropSize[0], cropSize[1]), dtype=img_data.colorImg.dtype)
cols1, rows1 = img_data.color_deskewed.shape
deskewed_points = []
deskewed_points.append((0, 0))
deskewed_points.append((cols1, 0))
deskewed_points.append((cols1, rows1))
deskewed_points.append((0, rows1))
deskewed_points = np.array(deskewed_points, np.float32)
color_transmtx = cv2.getPerspectiveTransform(projectPoints, deskewed_points)

img_data.color_deskewed = cv2.warpPerspective(img_data.colorImg, color_transmtx, (img_data.color_deskewed.shape[0],
                                                                         img_data.color_deskewed.shape[1]))
cv2.imshow("3gray", img_data.crop_gray)

if len(img_data.color_deskewed.shape) > 2:
    img_data.crop_gray = cv2.cvtColor(img_data.color_deskewed, cv2.COLOR_BGR2GRAY)
else:
    img_data.crop_gray = copy.deepcopy(img_data.color_deskewed)
cv2.imshow("4gray", img_data.crop_gray)


newLines = []
for i in range(0, len(img_data.textLines)):
    textArea = imgTransform.transformSmallPointsTOBigImage(img_data.textLines[i].textArea)

    linePolygon = imgTransform.transformSmallPointsTOBigImage(img_data.textLines[i].linePolygon)
    textAreaRemapped = imgTransform.remapSmallPointstoCrop(textArea, transmtx)

    linePolygonRemapped = imgTransform.remapSmallPointstoCrop(linePolygon, transmtx)

    newLines.append(TextLine(textAreaRemapped[0], linePolygonRemapped[0], img_data.crop_gray.shape[1],
                                                                     img_data.crop_gray.shape[0]))

img_data.textLines = []
for i in range (0, len(newLines)):
    img_data.textLines.append(newLines[i])
# print "textLines: "
# print img_data.textLines
cv2.waitKey(0)
ocr = OCR()
ocr.performOCR(img_data)

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