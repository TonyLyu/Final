import cv2
import copy
import numpy as np
from linefinder import LineSegment
from bin import produceThresholds
from segment.rect import Rect
from histogramvertical import HistogramVertical
from linefinder import median
import copy

class CharacterSegmenter:

    def __init__(self, img_data):
        self.img_data = img_data
        self.confidence = 0
        an_img = copy.copy(img_data.crop_gray)

        self.img_data.thresholds = produceThresholds(an_img)

        self.img_data.crop_gray = cv2.medianBlur(self.img_data.crop_gray, 3)
        self.top = LineSegment()
        self.bottom = LineSegment()

    def segment(self):
        edge_filter_mask = np.zeros((self.img_data.thresholds[0].shape[0],
                                    self.img_data.thresholds[0].shape[1]), np.uint8)
        edge_filter_mask = cv2.bitwise_not(edge_filter_mask)

        for lineidx in range(len(self.img_data.textLines)):
            self.top = self.img_data.textLines[lineidx].topLine
            self.bottom = self.img_data.textLines[lineidx].bottomLine

            avgCharHeight = self.img_data.textLines[lineidx].lineHeight
            print "avgCharHeight is %d" % avgCharHeight


            # avgCharHeight = 70
            ####
            ###height_to_width_ratio = self.img_data.charHeightMM[lineidx] /
            height_to_width_ratio = 70 / 35.0
            avgCharWidth = avgCharHeight / height_to_width_ratio

            cv2.imshow("before", self.img_data.thresholds[0])
            self.img_data.thresholds = self.removeSmallContours(self.img_data.thresholds, avgCharHeight, self.img_data.textLines[lineidx])

            allHistograms = []
            lineBoxes = []
            for i in range(0, len(self.img_data.thresholds)):
                histogramMask = np.zeros((self.img_data.thresholds[i].shape[0],
                                          self.img_data.thresholds[i].shape[1]), np.uint8)
                lp = np.array(self.img_data.textLines[lineidx].linePolygon, np.int32)

                histogramMask = cv2.fillConvexPoly(histogramMask, lp, (255, 255, 255))
                vertHistogram = HistogramVertical(self.img_data.thresholds[i], histogramMask)
                cv2.imshow("histogram %d" % i, vertHistogram.histoImg)
                score = 0.0
                charBoxes, score = self.getHistogramBoxes(vertHistogram, avgCharWidth, avgCharHeight, score)

                for z in range(0, len(charBoxes)):
                    lineBoxes.append(charBoxes[z])
            cv2.imshow("after", self.img_data.thresholds[0])

            # print "lineBoxes: "
            # for lineBox in lineBoxes:
            #     print lineBox.x
            #     print lineBox.y
            #     print lineBox.width
            #     print lineBox.height
            #     print "-----------------------------"
            # print avgCharHeight
            # print avgCharWidth
            candidateBoxes = self.getBestCharBoxes(self.img_data.thresholds[0], lineBoxes, avgCharWidth)
            # print "***********cnadidateBoxes**********"
            # for box in candidateBoxes:
            #     print box.x
            #     print box.y
            #     print box.width
            #     print box.height
            #     print "-------------------------"

            #show
            cleanStages = []
            for threshold in self.img_data.thresholds:
                cleanImg = np.zeros((threshold.shape[0], threshold.shape[1]), threshold.dtype)
                boxMask = self.getCharBoxMask(threshold, candidateBoxes)
                cleanImg = copy.deepcopy(threshold)
                cleanImg = cv2.bitwise_and(cleanImg, boxMask)
                cleanImg = cv2.cvtColor(cleanImg, cv2.COLOR_GRAY2RGB)
                for c in range(0, len(candidateBoxes)):
                    cleanImg = cv2.rectangle(cleanImg, candidateBoxes[c].p1, candidateBoxes[c].p2, (0, 255, 0), 1)
                cleanStages.append(cleanImg)
            cv2.imshow("clean1", cleanStages[0])
            cv2.imshow("clean2", cleanStages[1])
            cv2.imshow("clean3", cleanStages[2])
            cv2.waitKey(0)
            ##end
            edge_mask = self.filterEdgeBoxes(self.img_data.thresholds, candidateBoxes, avgCharWidth, avgCharHeight)


            edge_filter_mask = cv2.bitwise_and(edge_filter_mask, edge_mask)
            candidateBoxes = self.combineCloseBoxes(candidateBoxes)
            candidateBoxes = self.filterMostlyEmptyBoxes(self.img_data.thresholds, candidateBoxes)
            self.img_data.charRegions.append(candidateBoxes)
            for cboxidx in range(0, len(candidateBoxes)):
                self.img_data.charRegionsFlat.append(candidateBoxes[cboxidx])
        for i in range(0, len(self.img_data.thresholds)):
            self.img_data.thresholds[i] = cv2.bitwise_and(self.img_data.thresholds[i], edge_filter_mask)
        all_regions_combined = []

        for lidx in range(0, len(self.img_data.charRegions)):
            for boxidx in range(0, len(self.img_data.charRegions[lidx])):
                all_regions_combined.append(self.img_data.charRegions[lidx][boxidx])

        self.img_data.thresholds = self.cleanCharRegions(self.img_data.thresholds, all_regions_combined)
        cv2.waitKey(0)

        return self.img_data


    def getCharGap(self, leftBox, rightBox):
        right_midpoint = (rightBox.x + (rightBox.width / 2))
        left_midpoint = (leftBox.x + (leftBox.width / 2))
        return  right_midpoint - left_midpoint
    def combineCloseBoxes(self, charBoxes, ):
        if len(charBoxes) < 4:
            return charBoxes
        char_gaps = []
        for i in range(0, len(charBoxes)):
            if i == len(charBoxes) - 1:
                break
            char_gaps.append(self.getCharGap(charBoxes[i], charBoxes[i + 1]))
        median_char_gap = median(char_gaps, len(char_gaps))
        char_sizes = []
        for i in range(0, len(charBoxes)):
            char_sizes.append(charBoxes[i].width)
        char_sizes = sorted(char_sizes)
        biggestCharWidth = float(char_sizes[-2])

        newCharBoxes = []
        for i in range(0, len(charBoxes)):
            if i == len(charBoxes) - 1:
                newCharBoxes.append(charBoxes[i])
                break
            bigWidth = float(charBoxes[i + 1].x + charBoxes[i + 1].width - charBoxes[i].x)
            if i== 0:
                left_gap = 999999999999
            else:
                left_gap = self.getCharGap(charBoxes[i-1], charBoxes[i])
            right_gap =self.getCharGap(charBoxes[i], charBoxes[i + 1])
            min_gap = int(median_char_gap * 0.75)
            max_gap = int(median_char_gap * 1.25)
            max_width = int(biggestCharWidth * 1.2)
            has_good_gap = (left_gap >= min_gap and left_gap <= max_gap) or (right_gap >= min_gap and right_gap <= max_gap)
            if has_good_gap and bigWidth <= max_width:
                bigRect = Rect(charBoxes[i].x, charBoxes[i].y, bigWidth, charBoxes[i].height)
                newCharBoxes.append(bigRect)
                i += 1
            else:
                newCharBoxes.append(charBoxes[i])

        return newCharBoxes





    def removeSmallContours(self, thresholds, avgHeight, textLine):
        min_contour_height = 0.3 * avgHeight
        textLineMask = np.zeros((thresholds[0].shape[0], thresholds[0].shape[1]), np.uint8)
        lp = np.array(textLine.linePolygon, np.int32)


        textLineMask = cv2.fillConvexPoly(textLineMask, lp, (255, 255, 255))

        for i in range(0, len(thresholds)):
            contours = []
            hierarchy = []
            # thresholdsCopy = thresholds[i] * (textLineMask.astype(thresholds[i].dtype))
            #thresholdsCopy = thresholds[i] * textLineMask

            thresholdsCopy = cv2.bitwise_and(thresholds[i],thresholds[i], mask=textLineMask)

            img2, contours, hierarchy = cv2.findContours(thresholdsCopy, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
            for c in range(0, len(contours)):
                if len(contours[c]) == 0:
                    continue
                x, y , weight, height = cv2.boundingRect(contours[c])
                if height < min_contour_height:
                    cv2.drawContours(thresholds[i], contours, c, (0, 0, 0), -1)
                    continue
        return thresholds
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
        histoImg = np.zeros((rows, cols), np.uint8)
        for col in range(0, cols):
            columnCount =0
            for i in range(0, len(charBoxes)):

                if col >= charBoxes[i].x and col < (charBoxes[i].x + charBoxes[i].width):
                    columnCount += 1
            while(columnCount > 0):
                histoImg.itemset((histoImg.shape[0] - columnCount, col), 255)
                columnCount -= 1
        histogram = HistogramVertical(histoImg, np.ones((histoImg.shape[0], histoImg.shape[1]), np.uint8))
        bestRowIndex = 0
        bestRowScore = 0
        bestBoxes = []
        for row in range(0, histogram.histoImg.shape[0]):
            validBoxes = []
            allBoxes = self.convert1DHitsToRect(histogram.get1DHits(row), self.top, self.bottom)

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
                bestRowIndex = row
                bestBoxes = validBoxes

        return bestBoxes
    def filterMostlyEmptyBoxes(self, thresholds, charRegions):
        min_contour_height_percent = 0.5
        boxScores = []
        for i in range(0, len(charRegions)):
            boxScores.append(0)
        for i in range(0, len(thresholds)):
            for j in range(len(charRegions)):
                tempImg = np.zeros((thresholds[i].shape[0], thresholds[i].shape[1]), thresholds[i].dtype)
                tempImg = cv2.rectangle(tempImg, (int(charRegions[j].x), int(charRegions[j].y)),
                                        (int(charRegions[j].x + charRegions[j].width), int(charRegions[j].y + charRegions[j].height)),
                                        (255, 255 ,255), cv2.FILLED)
                tempImg = cv2.bitwise_and(thresholds[i], tempImg)
                img2, contours, hi = cv2.findContours(tempImg, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                allPointsInBox = []

                for c in range(0, len(contours)):
                    if len(contours[c]) == 0:
                        continue
                    for z in range(0, len(contours[c])):
                        allPointsInBox.append(contours[c][z][0])
                height = 0.0
                allPointsInBox = np.array(allPointsInBox, np.int32)

                if len(allPointsInBox) > 0:
                    _, _, _, height = cv2.boundingRect(allPointsInBox)

                if height >= float(charRegions[j].height * min_contour_height_percent):
                    boxScores[j] = boxScores[j] + 1
        newCharRegions = []
        maxBoxScore = 0
        for i in range(0, len(charRegions)):
            if boxScores[i] > maxBoxScore:
                maxBoxScore = boxScores[i]
        min_full_boxes = maxBoxScore * 0.49

        for i in range(0, len(charRegions)):
            if boxScores[i] > min_full_boxes:
                newCharRegions.append(charRegions[i])
        return newCharRegions




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
                rotated = cv2.warpAffine(thresholds[i], rot_mat, dsize = (thresholds[i].shape[1], thresholds[i].shape[0]))
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

                mask = cv2.rectangle(mask, (0, int(charRegions[0].y)), (int(leftEdge), int(charRegions[0].y + charRegions[0].height)), (0, 0, 0), -1)
                mask = cv2.rectangle(mask, (int(rightEdge), int(charRegions[0].y)), (int(mask.shape[1]), int(charRegions[0].y + charRegions[0].height)), (0, 0, 0), -1)

                if abs(self.top.angle > min_angle_for_rotation):
                    center = (mask.shape[1] / 2, mask.shape[0] / 2)
                    rot_mat = cv2.getRotationMatrix2D(center, self.top.angle * -1, 1.0 )
                    mask = cv2.warpAffine(mask, rot_mat, dsize = (mask.shape[1], mask.shape[0]))
                max_coverage_percent = 0.5
                leftCoveragePx = leftEdge - charRegions[0].x
                leftCoveragePercent = float(leftCoveragePx) / float(charRegions[0].width)
                rightCoveragePx = (charRegions[len(charRegions) - 1].x + charRegions[len(charRegions) - 1].width) - rightEdge
                rightCoveragePercent = float(rightCoveragePx) / float(charRegions[len(charRegions) - 1].width)


                if leftCoveragePercent > max_coverage_percent or charRegions[0].width - leftCoveragePx < 4:
                    mask = cv2.rectangle(mask, (int(charRegions[0].x), int(charRegions[0].y)),
                                         (int(charRegions[0].x + charRegions[0].width), int(charRegions[0].y + charRegions[0].height)),
                                         (0, 0, 0), -1)
                if rightCoveragePercent > max_coverage_percent or charRegions[len(charRegions) - 1].width - rightCoveragePx < 4:
                    mask = cv2.rectangle(mask, (int(charRegions[-1].x), int(charRegions[-1].y)),
                                         (int(charRegions[-1].x + charRegions[-1].width), int(charRegions[-1].y + charRegions[-1].height)),
                                         (0, 0, 0), -1)

                return mask
        return empty_mask


    def getLongestBloblengthBetweenLines(self, img, col):
        longestBloblength = 0
        onSegment = False
        wasbetweenLines = False
        curSegmentLength = 0
        for row in range(0, img.shape[0]):
            isbetweenLines = False
            isOn = bool(img.item(row, col))
            if isOn:
                isbetweenLines = self.top.isPointBelowLine((col, row)) and (not self.bottom.isPointBelowLine((col, row)))
                incrementBy = 1
                if not isbetweenLines:
                    incrementBy = 1.1
                onSegment = True
                curSegmentLength += incrementBy
            if isOn and isbetweenLines:
                wasbetweenLines = True
            if onSegment and (isOn == False or row == img.shape[0] - 1):
                if wasbetweenLines and curSegmentLength > longestBloblength:
                    longestBloblength = int(curSegmentLength)
                onSegment = False
                isbetweenLines = False
                curSegmentLength = 0

        return longestBloblength


    def convert1DHitsToRect(self, hits, top, bottom):
        boxes = []
        for i in range(0, len(hits)):
            topLeft = (int(hits[i][0]), int(top.getPointAt(hits[i][0]) - 1))
            botRight = (int(hits[i][1]), int(bottom.getPointAt(hits[i][1]) + 1))
            rect = Rect(topLeft, botRight)
            boxes.append(rect)
        return boxes
    def cleanCharRegions(self, thresholds, charRegions):
        min_speckle_height_percent = 0.13
        min_speckle_width_px = 3
        min_contour_area_percent = 0.1
        min_contour_height_percent = 0.5

        mask = self.getCharBoxMask(thresholds[0], charRegions)
        for i in range(0, len(thresholds)):
            thresholds[i] = cv2.bitwise_and(thresholds[i], mask)
            contours = []
            tempImg = copy.deepcopy(thresholds[i])
            img2, contours, hi = cv2.findContours(tempImg, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            for j in range(0, len(charRegions)):
                min_speckle_height = float(charRegions[j].height) * min_speckle_height_percent
                min_contour_area = float(charRegions[j].area()) * min_contour_area_percent

                tallestContourHeight = 0
                totalArea = 0

                for c in range(0, len(contours)):
                    if len(contours[c]) == 0:
                        continue


                    if charRegions[j].contains(contours[c][0][0]) == False:
                        continue
                    r_x, r_y, r_width, r_height = cv2.boundingRect(contours[c])
                    if r_height <= min_speckle_height or r_width <= min_speckle_width_px:
                        thresholds[i] = cv2.drawContours(thresholds[i], contours, c, (0, 0, 0), cv2.FILLED)
                    else:
                        if r_height > tallestContourHeight:
                            tallestContourHeight = r_height
                        totalArea += cv2.contourArea(contours[c])
                if totalArea < min_contour_area:

                    thresholds[i] = cv2.rectangle(thresholds[i], charRegions[j].p1, charRegions[j].p2, (0, 0, 0), -1)
                elif tallestContourHeight < float(charRegions[j].height) * min_contour_height_percent:
                    thresholds[i] = cv2.rectangle(thresholds[i], charRegions[j].p1, charRegions[j].p2, (0, 0, 0), -1)
            morph_size = 1
            closureElement = cv2.getStructuringElement(2, (2 * morph_size + 1, 2 * morph_size +1), (morph_size, morph_size))

            thresholds[i] = cv2.morphologyEx(thresholds[i], cv2.MORPH_CLOSE, closureElement)

            for j in range(0, len(charRegions)):
                thresholds[i] = cv2.line(thresholds[i], (int(charRegions[j].x - 1), int(charRegions[j].y)),
                                         (int(charRegions[j].x - 1), int(charRegions[j].y + charRegions[j].height)),
                                         (0, 0, 0))
                thresholds[i] = cv2.line(thresholds[i], (int(charRegions[j].x + charRegions[j].width + 1), int(charRegions[j].y)),
                                         (int(charRegions[j].x + charRegions[j].width + 1),
                                          int(charRegions[j].y + charRegions[j].height)),
                                         (0, 0, 0))

        return thresholds


    def getCharBoxMask(self, img_threshold, charBoxes):
        mask = np.zeros((img_threshold.shape[0], img_threshold.shape[1]), np.uint8)
        for i in range(0, len(charBoxes)):
            mask = cv2.rectangle(mask, charBoxes[i].p1, charBoxes[i].p2, (255, 255, 255), -1)
        return mask

