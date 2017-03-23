import cv2
import numpy as np
from linefinder import LineSegment
from bin import produceThresholds
from rect import Rect
from histogramvertical import HistogramVertical


class CharacterSegmenter:

    def __init__(self, img_data):
        self.img_data = img_data
        self.confidence = 0

        self.img_data.thresholds = produceThresholds(self.img_data.crop_gray)
        self.img_data.crop_gray = cv2.medianBlur(self.img_data.crop_gray, 3)
        self.top = LineSegment()
        self.bottom = LineSegment()

    def segment(self):
        edge_filte_mask = np.zeros((self.img_data.thresholds[0].shape[0],
                                    self.img_data.thresholds[0].shape[1]), np.uint8)
        edge_filte_mask = cv2.bitwise_not(edge_filte_mask)

        for lineidx in range(len(self.img_data.textLines)):
            self.top = self.img_data.textLines[lineidx].topLine
            self.bottom = self.img_data.textLines[lineidx].bottom

            avgCharHeight = self.img_data.textLines[lineidx].lineHeight
            ####
            ###height_to_width_ratio = self.img_data.charHeightMM[lineidx] /
            height_to_width_ratio = 70 / 35.0
            avgCharWidth = avgCharHeight / height_to_width_ratio
            self.removeSmallContours(self.img_data.thresholds, avgCharHeight, self.img_data.textLines[lineidx])
            allHistograms = []
            lineBoxes = []
            for i in range(0, len(self.img_data.thresholds)):
                histogramMask = np.zeros((self.img_data.thresholds[i].shape[0],
                                          self.img_data.thresholds[i].shape[1]), np.uint8)
                lp = np.array(self.img_data.textLines[lineidx].linePolygon, np.int32)
                histogramMask = cv2.fillConvexPoly(histogramMask, lp, (255, 255, 255))
                vertHistogram = HistogramVertical(self.img_data.thresholds[i], histogramMask)
                score = 0.0
                charBoxes = self.getHistogramBoxes(vertHistogram, avgCharWidth, avgCharHeight, score)

                for z in range(0, len(charBoxes)):
                    lineBoxes.append(charBoxes[z])

            candidateBoxes = self.getBestCharBoxes(self.img_data.thresholds[0], lineBoxes, avgCharWidth)
            edge_mask = self

    def removeSmallContours(self, thresholds, avgHeight, textLine):
        min_contour_height = 0.3 * avgHeight
        textLineMask = np.zeros((thresholds[0].shape[0], thresholds[0].shape[1]), np.uint8)
        textLineMask = cv2.fillConvexPoly(textLineMask, textLine.linePolygon, (255, 255, 255))
        for i in range(0, len(thresholds)):
            contours = []
            hierarchy = []
            thresholdsCopy = thresholds[i] * (textLine.astype(thresholds[i].dtype))
            img2, contours, hierarchy = cv2.findContours(thresholdsCopy, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
            for c in range(0, len(contours)):
                if len(contours[c]) == 0:
                    continue
                x, y , weight, height = cv2.boundingRect(contours[c])
                if height > min_contour_height:
                    cv2.drawContours(thresholds[i], contours, c, (0, 0, 0), -1)
                    continue
    def getHistogramBoxes(self, histogram, avgCharWidth, avgCharHeight, score):
        min_histogram_height =avgCharHeight * 0.5
        max_segment_width = avgCharWidth * 1.35

        pxLeniency = 2
        charBoxes = []
        allBoxes = self.convert1DHitsToRect(histogram.get1DHits(pxLeniency), self.top, self.bottom)

        for i in range(0, len(allBoxes)):
            if allBoxes[i].width >= 4 and allBoxes[i].width <= max_segment_width and allBoxes[i].height > min_histogram_height:
                charBoxes.append(allBoxes[i])
            elif allBoxes[i].width > avgCharWidth * 2 and allBoxes[i].width < max_segment_width * 2 and allBoxes[i].height > min_histogram_height:
                leftEdge = allBoxes[i].x + int(float(allBoxes[i].width) * 0.4)
                rightEdge = allBoxes[i].x + int(float(allBoxes[i].width) * 0.6)

                minX = histogram.getLocalMinimum(leftEdge, rightEdge)
                maxXChar1 = histogram.getLocalMaximum(allBoxes[i].x, minX)
                maxXChar2 = histogram.getLocalMaximum(minX, allBoxes[i].x + allBoxes[i].width)
                minHeight = histogram.getHeightAt(minX)

                maxHeightChar1 = histogram.getHeightAt(maxXChar1)
                maxHeightChar2 = histogram.getHeightAt(maxXChar2)
                if maxHeightChar1 > min_histogram_height and minHeight < (0.25 * maxHeightChar1):
                    botRight = (minX - 1, allBoxes[i].y + allBoxes[i].height)
                    charBoxes.append(Rect(allBoxes[i].tl(), botRight))
                if maxHeightChar2 > min_histogram_height and minHeight < (0.25 * maxHeightChar2):

                    topLeft = (minX - 1, allBoxes[i].y)
                    charBoxes.append(Rect(topLeft, allBoxes[i].br()))

        return charBoxes, score
    def getBestCharBoxes(self, img, charBoxes, avgCharWidth):
        rows, cols = img.shape[:2]
        max_segment_width = avgCharWidth * 1.35
        histoImg = np.zeros((cols, rows), np.uint8)
        for col in range(0, cols):
            columnCount =0
            for i in range(0, len(charBoxes)):
                if col >= charBoxes[i].x and col < (charBoxes[i].x + charBoxes[i].width):
                    columnCount += 1
            while(columnCount > 0):
                histoImg.itemset((histoImg.shape[0] - columnCount, col), 255)
                columnCount -= 1
        histogram = HistogramVertical(histoImg, np.zeros((histoImg.shape[0], histoImg.shape[1]), np.uint8))
        bestRowIndex = 0
        bestRowScore = 0
        bestBoxes = []
        for row in range(0, histogram.histoImg.shape[0]):
            validBoxes = []
            allBoxes = self.convert1DHitsToRect(histogram.getHeightAt(row), self.top, self.bottom)
            rowScore = 0.0
            for boxidx in range(0, len(allBoxes)):
                w = allBoxes[boxidx].width
                if w >= 4 and w <= max_segment_width:
                    widthDiffPixels = abs(w - avgCharWidth)
                    widthDiffPercent = float(widthDiffPixels) / avgCharWidth
                    rowScore += 10 * (1 - widthDiffPercent)
                    if widthDiffPercent < 0.25:
                        rowScore += 8
                    validBoxes.append(allBoxes[boxidx])
                elif w > avgCharWidth * 2 and w <= max_segment_width * 2:

                    leftEdge = allBoxes[boxidx].x + int(float(allBoxes[boxidx].width) * 0.4)
                    rightEdge = allBoxes[boxidx].x + int(float(allBoxes[boxidx].width) * 0.6)
                    minX = histogram.getLocalMinimum(leftEdge, rightEdge)
                    maxXChar1 = histogram.getLocalMaximum(allBoxes[boxidx].x, minX)
                    maxXChar2 = histogram.getLocalMaximum(minX, allBoxes[boxidx].x + allBoxes[boxidx].width)
                    minHeight = histogram.getHeightAt(minX)

                    maxHeightChar1 = histogram.getHeightAt(maxXChar1)
                    maxHeightChar2 = histogram.getHeightAt(maxXChar2)

                    if minHeight < (0.25 * maxHeightChar1):
                        botRight = (minX - 1, allBoxes[boxidx].y + allBoxes[boxidx].height)
                        validBoxes.append(Rect(allBoxes[boxidx].tl(), botRight))
                    if minHeight < (0.25 * maxHeightChar2):
                        topLeft = (minX + 1, allBoxes[boxidx].y)
                        validBoxes.append(Rect(topLeft, allBoxes[boxidx].br()))
            if rowScore > bestRowScore:
                bestRowScore = rowScore
                bestRowScore = row
                bestBoxes = validBoxes

        return bestBoxes

    def filterEdgeBoxes(self, thresholds, charRegions, avgCharWidth, avgCharHeight):
        min_angle_for_rotation = 0.4
        min_connected_edge_pixel = avgCharHeight * 1.5
        alternate = thresholds[0].shape[0] * 0.92
        if alternate < min_connected_edge_pixel and alternate > avgCharHeight:
            min_connected_edge_pixel = alternate
        empty_mask = np.zeros((thresholds[0].shape[0], thresholds[0].shape[1]), np.uint8)
        empty_mask = cv2.bitwise_not(empty_mask)
        if len(charRegions) <= 1:
            return empty_mask
        leftEdges = []
        rightEdges = []
        for i in range(0, len(thresholds)):
            if abs(self.top.angle) > min_angle_for_rotation:
                center = (thresholds[i].shape[1] / 2, thresholds[i].shape[0] / 2)
                rot_mat = cv2.getRotationMatrix2D(center, self.top.angle, 1.0)
                rotated = cv2.warpAffine(thresholds[i], rot_mat, (thresholds[i].shape[0], thresholds[i].shape[1]))
            else:
                rotated = thresholds[i]
            leftEdgeX = 0
            rightEdgeX = rotated.shape[1]
            col = charRegions[0].x + charRegions[0].width
            while col >= 0:
                rowLength = self.getLongestBloblengthBetweenLines(rotated, col)
                if rowLength > min_connected_edge_pixel:
                    leftEdgeX = col
                    break
                col -= 1
            col = charRegions[len(charRegions) - 1].x
            while col < rotated.shape[1]:
                rowLength = self.getLongestBloblengthBetweenLines(rotated, col)
                if rowLength > min_connected_edge_pixel:
                    rightEdgeX = col
                    break
                col += 1
            if leftEdgeX != 0:
                leftEdges.append(leftEdgeX)
            if rightEdgeX != thresholds[i].shape[1]:
                rightEdges.append(rightEdgeX)

            leftEdge = 0
            rightEdge = thresholds[0].shape[1]

            if len(leftEdges) > 1:
                leftEdges = sorted(leftEdges)
                leftEdge = leftEdges[len(leftEdges) - 2] + 1
            if len(rightEdges) > 1:
                rightEdges = sorted(rightEdges)
                rightEdge = rightEdges[1] - 1
            if leftEdge != 0 or rightEdge != thresholds[0].shape[1]:
                mask = np.zeros((thresholds[0].shape[0], thresholds[0].shape[1]), np.uint8)
                mask = cv2.bitwise_not(mask)
                mask = cv2.rectangle(mask, (0, charRegions[0].y), (leftEdge, charRegions[0].y + charRegions[0].height), (0, 0, 0), -1)

    def getLongestBloblengthBetweenLines(self, img, col):
        longestBloblength = 0
        onSegment = False
        wasbetweenLines = False
        curSegmentLength = 0
        for row in range(0, img.shape[0]):
            isbetweenLines = False
            isOn = bool(img.item(row, col))
            if isOn:
                isbetweenLines = self.top.isPointBelowLine((col, row)) and \
                                 (not self.bottom.isPointBelowLine((col, row)))
                incrementBy = 1
                if not isbetweenLines:
                    incrementBy = 1.1
                onSegment = True
                curSegmentLength += incrementBy
            if isOn and isbetweenLines:
                wasbetweenLines = True
            if onSegment and (isOn == False or row == img.shape[0] - 1):
                if wasbetweenLines and curSegmentLength > longestBloblength:
                    longestBloblength = curSegmentLength
                onSegment = False
                isbetweenLines = False
                curSegmentLength = 0

        return longestBloblength


    def convert1DHitsToRect(self, hits, top, bottom):
        boxes = []
        for i in range(0, len(hits)):
            topLeft = (hits[i][0], top.getPointAt(hits[i][0]) - 1)
            botRight = (hits[i][1], bottom.getPointAt(hits[i][1]) + 1)
            rect = Rect(topLeft, botRight)
            boxes.append(Rect)
        return boxes

