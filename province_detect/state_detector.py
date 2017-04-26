from featurematcher import FeatureMatcher, RecognitionResult
import os
import cv2
import numpy as np
import copy
from bin import produceThresholds
from image_data import ImageData
from pro_characteran import characteranalysis
from edgefinder import EdgeFinder
from segment.rect import Rect
import pytesseract
from PIL import Image
class StateCandidate:
    def __init__(self):
        self.state_code = ""
        self.confidence = 0.0

class SateDetector:
    def __init__(self):
        self.featureMather = FeatureMatcher()
        if self.featureMather.isLoaded() == False:
            print "can not detect state"
            return
        runDir = os.path.dirname(__file__)

        self.featureMather.loadRecognitionSet(runDir, "ca")
    def detect(self, imageBytes):
        img = cv2.imdecode(imageBytes, 1)
        return self._detect(img)
    def detect1(self, pixelData, bytesPerPixel, imgWidth, imgHeight):
        # arraySize = imgHeight * imgWidth * bytesPerPixel
        # print imgHeight
        # print imgWidth
        # print bytesPerPixel
        # cv2.imshow("state img", pixelData)
        # cv2.waitKey(0)
        # # imgData = np.array(pixelData, np.uint8)
        # # img = imgData.reshape(bytesPerPixel, imgHeight)
        cv2.imshow("pixel", pixelData)
        cv2.imwrite("ca002.png", pixelData)
        cv2.waitKey(0)
        cv2.destroyAllWindows()
        img = copy.deepcopy(pixelData)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        row2, col2  = img.shape
        row2 = int(row2)
        col2 = int(col2)
        text_points = []
        text_points.append((int(0.25 * col2), int(row2 * 0.05)))
        text_points.append((int(col2 * 0.75), int(row2 * 0.05)))
        text_points.append((int(col2 * 0.75), int(row2 * 0.25)))
        text_points.append((int(col2 * 0.25), int(row2 * 0.25)))
        x = int(0.25 * col2)
        y = int(0.05 * row2)
        w = int(0.5 * col2)
        h = int(0.2 * row2)
        testimg = copy.deepcopy(img)[y:y + h, x:x + w]
        testimg = cv2.resize(testimg, dsize=(120, 40))
        cv2.imshow("te123", testimg)
        textimg = produceThresholds(testimg)
        # img_data1 = ImageData(pixelData)
        # img_data1.crop_gray = testimg
        # img_data1.thresholds = textimg
        # img_data1.regionOfInterest = Rect(0, 0, 120, 40)
        # img_data1 = characteranalysis(img_data1)
        # edgeFinder1 = EdgeFinder(img_data1)
        # img_data1.plate_corners = edgeFinder1.findEdgeCorners()
        #
        # img_data1 = edgeFinder1.img_data
        textimg = produceThresholds(testimg)
        testimg = textimg[0]
        testimg = cv2.bitwise_not(testimg)
        kernel = np.ones((1,1), np.uint8)
        testimg = cv2.dilate(testimg, kernel, iterations=1)
        testimg = cv2.erode(testimg, kernel, iterations=1)
        textimg = cv2.adaptiveThreshold(testimg, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)


        cv2.imwrite("thresh.png", textimg)
        result = pytesseract.image_to_string(Image.open("thresh.png"))
        print result
        if "ON" in result or "TA" in result or "IO" in result or "0N" in result:
            result = "on"
        elif "Qu" in result or "u" in result:
            result = "quebec"




        # cv2.imshow('tst', testimg)
        # cv2.imshow('tst', textimg[0])

        imgtoout = cv2.bitwise_not(textimg[0])
        cv2.imshow("th", imgtoout)

        # test_img = copy.deepcopy(img_data1.crop_gray)
        # print img_data1.textLines[0].linePolygon
        # for i in range(0, 2):
        #     pair = img_data1.textLines[0].linePolygon[i]
        #     w = pair[0]
        #     h = pair[1]
        #     h = h - 8
        #     pair = (w, h)
        #     img_data1.textLines[0].linePolygon[i] = pair
        #     pair2 = img_data1.textLines[0].textArea[i]
        #     w2 = pair2[0]
        #     h2 = pair2[1]
        #     h2 = h2 - 8
        #     pair2 = (w2, h2)
        #     img_data1.textLines[0].textArea[i] = pair2
        #
        # polygon = np.array(img_data1.textLines[0].textArea)
        # print polygon
        # pair1 = img_data1.textLines[0].topLine.p1
        # pair2 = img_data1.textLines[0].topLine.p2
        # img_data1.textLines[0].topLine.p1 = (pair1[0], pair1[1] - 10)
        # img_data1.textLines[0].topLine.p2 = (pair2[0], pair2[1] - 10)
        #
        # pair1 = img_data1.textLines[0].bottomLine.p1
        # pair2 = img_data1.textLines[0].bottomLine.p2
        # img_data1.textLines[0].bottomLine.p1 = (pair1[0], pair1[1] + 8)
        # img_data1.textLines[0].bottomLine.p2 = (pair2[0], pair2[1] + 8)
        #
        # test_img = cv2.polylines(test_img, [polygon], True, (0, 0, 255))
        # cv2.imshow("text", test_img)
        #
        # cv2.waitKey(0)
        return self._detect(pixelData), result
    def _detect(self, image):
        results = []
        debugImg = copy.deepcopy(image)
        matchesArray = []
        result = self.featureMather.recognize(image, True, debugImg, True, matchesArray)
        if result.haswinner == False:
            return results
        top_candidate = StateCandidate
        top_candidate.confidence = result.confidence
        top_candidate.state_code = result.winner
        results.append(top_candidate)
        return  results

