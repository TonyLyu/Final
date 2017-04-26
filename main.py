
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
from province_detect.state_detector import SateDetector
img = cv2.imread('q.jpeg')
img_data = ImageData(img)
rows, cols = img.shape[:2]
grays, regions = detector.detect(img)
print type(grays[0])
for numberPlate in range(len(grays)):
    img_data.crop_gray = grays[numberPlate]
    img_data.regionOfInterest = regions[numberPlate]
    an_img = copy.copy(img_data.crop_gray)
    img_data.thresholds = bin.produceThresholds(an_img)
    # cv2.imshow("1", img_data.thresholds[0])
    # cv2.imshow("2", img_data.thresholds[1])
    # cv2.imshow("3", img_data.thresholds[2])

    # cv2.imwrite("plate.jpg", img_data.crop_gray)
    # cv2.imwrite("thresh.jpg", img_data.thresholds[0])

    img_data = characteran.characteranalysis(img_data)
    if img_data.disqualified == True:
        print "low score"
        continue
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
    result = ocr.performOCR(img_data)
    numberOfPlate = "".join(result)
    print numberOfPlate

    stateDetector = SateDetector()
    state_candidates, text = stateDetector.detect1(img_data.color_deskewed, img_data.color_deskewed.shape[2], img_data.color_deskewed.shape[1], img_data.color_deskewed.shape[0])
    if len(state_candidates) > 0:
        print state_candidates[0].state_code
    print text

cv2.destroyAllWindows()

