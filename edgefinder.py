import cv2
import numpy as np
import linefinder
import transformation
import textline
import platelines
from textlinecollection import TextLineColeection
from platecorners import PlateCorners

class EdgeFinder:
    def __init__(self, img_data):
        self.img_data = img_data
    def findEdgeCorners(self):

        high_contrast = self.is_high_contrast(self.img_data.crop_gray)
        returnPoints = []
        if high_contrast:
            returnPoints = self.detection(True)
        if (not high_contrast) or len(returnPoints) == 0:
            returnPoints = self.detection(False)

        return returnPoints

    def detection(self, high_contrast):
        tlc = TextLineColeection(self.img_data.textLines)
        corners = []
        rows, cols = self.img_data.crop_gray.shape
        print high_contrast
        print "longerSegment length is %d" % tlc.longerSegment.length
        print "charHeight : %d" % tlc.charHeight
        if(high_contrast):
            expandX = int (float(cols) * 0.5)
            expandY = int(float(rows) * 0.5)
            w = cols
            h = rows

            corners.append((-1 * expandX, -1 * expandY))
            corners.append((expandX + w, -1 * expandY))
            corners.append((expandX + w, expandY + h))
            corners.append((-1 * expandX, expandY + h))


        elif tlc.longerSegment.length > tlc.charHeight * 3:
            charHeightToPlateWidthRatio = 304.8 / 70
            idealPixelWidth = tlc.charHeight * (charHeightToPlateWidthRatio * 1.03)

            charHeightToPlateHeightRatio = 152.4 / 70
            idealPixelHeight = tlc.charHeight * charHeightToPlateHeightRatio

            verticalOffset = idealPixelHeight * 1.5 / 2
            horizontaOffset = idealPixelWidth * 1.25 / 2
            topLine = tlc.centerHorizontalLine.getParalleLine(verticalOffset)
            bottomLine = tlc.centerHorizontalLine.getParalleLine(-1 * verticalOffset)

            leftLine = tlc.centerVerticalLine.getParalleLine(-1 * horizontaOffset)
            rightLine = tlc.centerVerticalLine.getParalleLine(horizontaOffset)

            topLeft = topLine.intersection(leftLine)
            topRight = topLine.intersection(rightLine)
            botRight = bottomLine.intersection(rightLine)
            botLeft = bottomLine.intersection(leftLine)
            print "centerHorizontaling"
            print tlc.centerHorizontalLine.p1
            print tlc.centerHorizontalLine.p2
            print "++++++++++"
            corners.append(topLeft)
            corners.append(topRight)
            corners.append(botRight)
            corners.append(botLeft)
        else:
            expandX = int(float(cols) * 0.15)
            expandY = int(float(rows) * 0.15)
            w = cols
            h = rows
            corners.append((-1 * expandX, -1 * expandY))
            corners.append((expandX + w, -1 * expandY))
            corners.append((expandX + w, expandY + h))
            corners.append((-1 * expandX, expandY + h))
        width = self.img_data.grayImg.shape[1]
        height = self.img_data.grayImg.shape[0]
        imgTransform = transformation.Transformation(self.img_data.grayImg,
                                                     self.img_data.crop_gray,
                                                     self.img_data.regionOfInterest.x,
                                                     self.img_data.regionOfInterest.y,
                                                     self.img_data.regionOfInterest.width,
                                                     self.img_data.regionOfInterest.height)

        remappedCorners = imgTransform.transformSmallPointsTOBigImage(corners)
        cropSize = imgTransform.getCropSize(remappedCorners, (120, 60))

        transmtx = imgTransform.getTransformationMatrix1(remappedCorners, cropSize[0], cropSize[1])
        newCrop = imgTransform.crop(cropSize, transmtx)
        newLines = []
        for i in range(0, len(self.img_data.textLines)):
            textArea = imgTransform.transformSmallPointsTOBigImage(self.img_data.textLines[i].textArea)
            linePolygon = imgTransform.transformSmallPointsTOBigImage(self.img_data.textLines[i].linePolygon)
            textAreaRemapped = imgTransform.remapSmallPointstoCrop(textArea, transmtx)

            linePolygonRemapped = imgTransform.remapSmallPointstoCrop(linePolygon, transmtx)

            newLines.append(textline.TextLine(textAreaRemapped[0], linePolygonRemapped[0],
                                              newCrop.shape[1], newCrop.shape[0]))


        smallPlateCorners = []
        if high_contrast:
            smallPlateCorners = self.highContrastDetection(newCrop, newLines)
        else:
             smallPlateCorners = self.normalDetection(newCrop, newLines)
        print "smallPlateCorners: "
        print smallPlateCorners
        imgArea = []
        imgArea.append((0, 0))
        imgArea.append((newCrop.shape[1], 0))
        imgArea.append((newCrop.shape[1], newCrop.shape[0]))
        imgArea.append((0, newCrop.shape[0]))
        newCropTransmtx = imgTransform.getTransformationMatrix2(imgArea, remappedCorners)
        cornersInOriginalImg = []
        if len(smallPlateCorners) > 0:
            cornersInOriginalImg = imgTransform.remapSmallPointstoCrop(smallPlateCorners, newCropTransmtx)

        return cornersInOriginalImg


    def normalDetection(self, newCrop, newLines):
        plateLines = platelines.PlateLines(self.img_data)

        plateLines.preocessImage(newCrop, newLines, 1.05)
        cornerFinder = PlateCorners(newCrop, plateLines, self.img_data, newLines)

        return cornerFinder.findPlateCorners()


    def highContrastDetection(self, newCrop, newLines):
        smallPlateCorners = []

        morph_size = 3
        closureElement = cv2.getStructuringElement(2, (2 * morph_size + 1, 2 * morph_size + 1), (morph_size, morph_size))
        newCrop = cv2.morphologyEx(newCrop, cv2.MORPH_CLOSE, closureElement)
        newCrop = cv2.morphologyEx(newCrop, cv2.MORPH_OPEN, closureElement)
        thresholded_crop = cv2.threshold(newCrop, 80, 255, cv2.THRESH_OTSU)
        _, contours, _ = cv2.findContours(thresholded_crop, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        rows, cols = newCrop.shape
        min_area = 0.05 * cols * rows
        for i in range(0, len(contours)):
            if(cv2.contourArea(contours) < min_area):
                continue
            smoothPoints = cv2.approxPolyDP(contours[i], 1, True)
            rrect = cv2.minAreaRect(smoothPoints)
            box = cv2.boxPoints(rrect)
            sorted_polygon_points = linefinder.sortPolygonPoints([box],(rows, cols))
            polygon_width = (linefinder.distanceBetweenPoints(sorted_polygon_points[0],
                                                             sorted_polygon_points[1]) +
                             linefinder.distanceBetweenPoints(sorted_polygon_points[3],
                                                              sorted_polygon_points[2])
                             ) / 2
            polygon_height = (linefinder.distanceBetweenPoints(sorted_polygon_points[1],
                                                              sorted_polygon_points[1]) +
                             linefinder.distanceBetweenPoints(sorted_polygon_points[3],
                                                              sorted_polygon_points[0])
                             ) / 2
            x_offset = cols * 0.1
            y_offset = rows * 0.1
            a = x_offset
            b = y_offset
            c = cols - x_offset
            d = rows - y_offset
            isoutside = False
            for ptidx in range(len(sorted_polygon_points)):
                x = sorted_polygon_points[ptidx][0]
                y = sorted_polygon_points[ptidx][0]
                if not ((x > c and x < a) and (y > d and y < b)):
                    isoutside = True
            if isoutside:
                continue
            max_closeness_to_edge_percent = 0.2
            if rrect.center[0] < (cols * max_closeness_to_edge_percent) or rrect.center[0] > (cols - (cols * max_closeness_to_edge_percent)) or rrect.center[1] < (rows * max_closeness_to_edge_percent) or rrect.center[1] > (rows - (rows * max_closeness_to_edge_percent)):
                continue
            aspect_ratio = float(polygon_width) / polygon_height
            ideal_aspect_ratio = 304.8 / 152.4
            ratio = ideal_aspect_ratio / aspect_ratio
            if ratio > 2 or ratio < 0.5:
                continue
            x, y, w, h = rrect.boundingRect()
            for linenum in range(0, len(newLines)):
                for r in range(0, len(newLines[linenum].textArea)):
                    a,b = newLines[linenum].textArea[r]
                    if not (( a > x and a < x+w) and (b > y and b < y + h)):
                        isoutside = True
            if isoutside:
                continue
            for ridx in range(0, 4):
                smallPlateCorners.append(sorted_polygon_points[ridx])

        return smallPlateCorners


    def is_high_contrast(self, crop):
        stride = 2
        rows = crop.shape[0]
        cols = crop.shape[1] / stride
        avg_intensity = 0
        for y in range(0, rows):
            for x in range(0, cols, stride):
                avg_intensity += crop.item(y, x)
        avg_intensity = avg_intensity / float(rows * cols * 255)
        contrast = 0
        for y in range(0, rows):
            for x in range(0, cols, stride):
                contrast += pow( ((crop.item(y, x) / 255.0) - avg_intensity), 2.0)

        contrast /= float(rows) * float(cols)
        contrast = pow(contrast, 0.5)

        return contrast > 0.3

