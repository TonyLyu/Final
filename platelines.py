import cv2
import numpy as np
import math
import linefinder
import copy

class PlateLines:
    def __init__(self, img_data = None):
        self.img_data = img_data
        self.horizontalLines=[]
        self.verticalLines = []
        self.line = None

    def preocessImage(self, inputImage, textLines, sensitivity):
        avgPixelIntensity = cv2.mean(inputImage)

        if avgPixelIntensity[0] >= 252:
            return
        elif avgPixelIntensity[0] <= 3:
            return

        smoothed = cv2.bilateralFilter(inputImage, 3, 45, 45)
        edges = cv2.Canny(smoothed, 66, 133)

        mask = np.zeros((inputImage.shape[0], inputImage.shape[1]), dtype="uint8")
        for i in range(0, len(textLines)):
            polygons = []
            polygons.append(textLines[i].textArea)
            polygons = np.array(polygons, np.int32)
            mask = cv2.fillPoly(mask, polygons, (255, 255, 255))
        mask = cv2.dilate(mask, cv2.getStructuringElement(1, (2, 3), (1, 1)))
        mask = cv2.bitwise_not(mask)
        edges = cv2.bitwise_and(edges, mask)
        hlines = self.getLines(edges, sensitivity, False)
        vlines = self.getLines(edges, sensitivity, True)

        for i in range(0, len(hlines)):
            self.horizontalLines.append(hlines[i])
        for i in range(0, len(vlines)):
            self.verticalLines.append(vlines[i])
        debug = True
        if debug:
            debugImgHoriz = copy.deepcopy(edges)
            debugImgVert = copy.deepcopy(edges)
            debugImgHoriz = cv2.cvtColor(debugImgHoriz, cv2.COLOR_GRAY2RGB)
            debugImgVert = cv2.cvtColor(debugImgVert, cv2.COLOR_GRAY2RGB)
            for i in range(0, len(self.horizontalLines)):
                cv2.line(debugImgHoriz, self.horizontalLines[i].line.p1,
                         self.horizontalLines[i].line.p2, (0, 0, 255),
                         1, cv2.LINE_AA)
            for i in range(0, len(self.verticalLines)):
                cv2.line(debugImgVert, self.verticalLines[i].line.p1,
                        self.verticalLines[i].line.p2, (0, 0, 255),
                         1, cv2.LINE_AA)

            images = []
            images.append(debugImgHoriz)
            images.append(debugImgVert)
            for i in range(0, len(images)):
                cv2.imshow("Hough Lines %d" % i, images[i])

    def getLines(self, edges, sensitivityMultiplier, vertical):
        horizontal_sensitivity = 45
        vertical_sensitivity = 25
        filteredLines =[]
        if vertical:
            sensitivity = int(vertical_sensitivity * (1.0 / sensitivityMultiplier))
        else:
            sensitivity = int(horizontal_sensitivity * (1.0 / sensitivityMultiplier))
        allLines = cv2.HoughLines(edges, 1, math.pi/180.0, sensitivity, srn=0, stn=0)




        for i in range(0, len(allLines)):

            rho = allLines[i][0][0]
            theta = allLines[i][0][1]

            pt1 = pt2 = (0, 0)
            a = math.cos(theta)
            b = math.sin(theta)
            x0 = a * rho
            y0 = b * rho
            angle = theta * (180.0 / math.pi)
            x1 = round(x0 + 1000 * (-b))
            y1 = round(y0 + 1000 * (a))
            pt1 = (x1, y1)
            x2 = round(x0 - 1000 * (-b))
            y2 = round(y0 - 1000 * (a))
            pt2 = (x2, y2)

            if vertical:
                if angle < 20 or angle > 340 or (angle > 160 and angle < 210):
                    if pt1[1] <= pt2[1]:
                        line = linefinder.LineSegment(pt2[0], pt2[1], pt1[0], pt1[1])
                    else:
                        line = linefinder.LineSegment(pt1[0], pt1[1], pt2[0], pt2[1])
                    top = linefinder.LineSegment(0, 0, edges.shape[1], 0)
                    bottom = linefinder.LineSegment(0, edges.shape[0], edges.shape[1], edges.shape[0])
                    p1 = line.intersection(bottom)
                    p2 = line.intersection(top)

                    plateLine = PlateLines()
                    plateLine.line = linefinder.LineSegment(p1[0], p1[1], p2[0], p2[1])
                    plateLine.confidence = (1.0 - 0.3) * (float(len(allLines) - i)) / float(len(allLines)) + 0.3
                    filteredLines.append(plateLine)
            else:
                if (angle > 70 and angle < 110) or (angle > 250 and angle < 290):
                    if pt1[0] <= pt2[0]:
                        line = linefinder.LineSegment(pt1[0], pt1[1], pt2[0], pt2[1])
                    else:
                        line = linefinder.LineSegment(pt2[0], pt2[1], pt1[0], pt1[1])
                    newY1 = line.getPointAt(0)
                    newY2 = line.getPointAt(edges.shape[1])
                    plateLine = PlateLines()
                    plateLine.line = linefinder.LineSegment(0, newY1, edges.shape[1], newY2)
                    plateLine.confidence = (1.0 - 0.3) * (float(len(allLines) - i)) / float(len(allLines)) + 0.3
                    filteredLines.append(plateLine)


        return filteredLines


