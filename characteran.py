import cv2
import numpy as np
import bin
import textcontours
import platemask
import linefinder
import textline
import copy
from operator import attrgetter

def getKey(item):
    return item.topLine.p1[1]


def characteranalysis(img_data):

    img = img_data.crop_gray
    bin_img = copy.deepcopy(img_data.thresholds)
    b_img = copy.deepcopy(bin_img)
    allTextContours = []
    for i in range(0, len(bin_img)):
        tc = textcontours.textcontours(b_img[i], img)
        allTextContours.append(tc)
    b_img = copy.deepcopy(bin_img)

    for i in range(0, len(bin_img)):
        # some problems
        allTextContours[i] = filter(b_img[i], allTextContours[i])
        print "Threshold (%s) is %d" %(i, allTextContours[i].getGoodIndicesCount())


    plateMask = platemask.platemask(bin_img)
    plateMask.findOuterBoxMask(allTextContours)
    img_data.hasPlateBorder = plateMask.hasplatemask
    img_data.plateBorderMask = plateMask.getMask()
    if plateMask.hasplatemask:
        for i in range(0, len(bin_img)):
            allTextContours[i] = filterByOuterMask(allTextContours[i], img_data.hasPlateBorder, img_data.plateBorderMask)
    bestFitScore = -1
    bestFitIndex = -1

    #################################
    bestThreshold = None
    bestContours = None
    #################################

    for i in range(0, len(bin_img)):
        segmentCount = allTextContours[i].getGoodIndicesCount()
        if segmentCount > bestFitScore:
            bestFitScore = segmentCount
            bestFitIndex = i
            bestThreshold = bin_img[i]
            bestContours = allTextContours[i]
    print "BestFitScore: %d, Index: %d"%(bestFitScore, bestFitIndex)
    if bestFitScore <= 1:
        print "low best fit score"
        return None

    img_contours = bestContours.drawContours(bestThreshold)
    cv2.imshow("bestThreshold", bestThreshold)
    cv2.imshow("Matching Contours", img_contours)

    lf = linefinder.LineFinder(img)

    linePolygons = lf.findLines(img_data.crop_gray, bestContours)
    print "***linePolygons***"
    print linePolygons
    tempTextLines = []
    for i in range(0, len(linePolygons)):
        linePolygon = linePolygons[i]
        topLine = linefinder.LineSegment(linePolygon[0][0], linePolygon[0][1],
                                         linePolygon[1][0], linePolygon[1][1])
        bottomLine = linefinder.LineSegment(linePolygon[3][0], linePolygon[3][1],
                                            linePolygon[2][0], linePolygon[2][1])
        textArea = getCharArea(topLine, bottomLine, bestContours)

        textLine = textline.TextLine(textArea, linePolygon, img.shape[1], img.shape[0])
        tempTextLines.append(textLine)
        print textLine.lineHeight

    bestContours = filterBetweenLines(bestThreshold, bestContours, tempTextLines)

    tempTextLines = sorted(tempTextLines, key=getKey)
    ###textliens###
    textLines = []
    #################
    rows, cols = img.shape

    for i in range(0, len(tempTextLines)):
        updatedTextArea = getCharArea(tempTextLines[i].topLine, tempTextLines[i].bottomLine, bestContours)
        linePolygon = tempTextLines[i].linePolygon
        if len(updatedTextArea) > 0 and len(linePolygon) > 0:
            textLines.append(textline.TextLine(updatedTextArea, linePolygon, cols, rows))
    if len(textLines) > 0:
        confidenceDrainers = 0
        charSegmentCount = bestContours.getGoodIndicesCount()
        if charSegmentCount == 1:
            confidenceDrainers += 91
        elif charSegmentCount < 5:
            confidenceDrainers += (5 - charSegmentCount) * 10
        absangle = abs(textLines[0].topLine.angle)
        if absangle > 15:
            confidenceDrainers += 91
        elif absangle > 1:
            confidenceDrainers += absangle

    img_data.textLines = textLines
    print "another textline "
    print img_data.textLines[0].lineHeight
    return img_data

def filter(threshold, tc):
    rows, cols = threshold.shape[:2]
    starting_min_height = round(rows * 0.3)
    starting_max_height = round(rows * (0.3 + 0.2))
    height_step = round(rows * 0.1)
    num_steps = 4
    bestFitScore = -1

    bestIndices = []
    for i in range(0, num_steps):
        l = tc.size()
        for z in range(0, l):
            tc.goodIndices[z] = True
        tc = filterByBoxSize(tc, starting_min_height + (i * height_step), starting_max_height + (i * height_step))
        goodIndices = tc.getGoodIndicesCount()
        if goodIndices == 0 or goodIndices <= bestFitScore:
            continue
        tc = filterContourHoles(tc)
        goodIndices = tc.getGoodIndicesCount()
        if goodIndices == 0 or goodIndices <= bestFitScore:
            continue
        segmentCount = tc.getGoodIndicesCount()
        if segmentCount > bestFitScore:

            bestFitScore = segmentCount
            bestIndices = tc.getIndicesCopy()

    tc.setIndices(bestIndices)
    return tc



def filterByBoxSize(tc, minHeightPx, maxHeightPx):
    larger_char_height_mm = 70.0
    larger_char_width_mm = 35.0
    idealAspect = larger_char_width_mm / larger_char_height_mm
    aspecttolerance = 0.25
    for i in range(0, tc.size()):
        if tc.goodIndices[i] == False:
            continue
        tc.goodIndices[i] = False
        x, y, width, height = cv2.boundingRect(tc.contours[i])
        minWidth = height * 0.2
        if height >= minHeightPx and height <= maxHeightPx and width > minWidth:
            charAspect = float(width) / float (height)
            if abs(charAspect - idealAspect) < aspecttolerance:
                tc.goodIndices[i] = True

    return tc

def filterContourHoles(tc):
    for i in range(0, tc.size()):
        if tc.goodIndices[i] == False:
            continue
        tc.goodIndices[i] = False
        parentIndex = tc.hierarchy[0][i][3]

        if parentIndex >= 0 and tc.goodIndices[parentIndex]:
            print "filterContourHoles:contour index: %d"% i
        else:
            tc.goodIndices[i] = True
    return tc

def filterByOuterMask(textcontours, hasPlateBorder, plateBorderMask):
    minimum_percent_left_after_mask = 0.1
    minium_percent_of_chars_inside_plate_mask = 0.6
    if hasPlateBorder == False:
        return textcontours
    plateMask = plateBorderMask
    tempMaskedContour = np.zeros((plateMask.shape[0],plateMask.shape[1]), dtype="uint8")
    tempFullContour = np.zeros((plateMask.shape[0],plateMask.shape[1]), dtype="uint8")
    charsInsideMask = 0
    totalChars = 0
    originalindices = []
    for i in range(0, len(textcontours)):
        originalindices.append(textcontours.goodIndices[i])
    for i in range(0, len(textcontours)):
        if(textcontours.goodIndices[i] == False):
            continue
        totalChars += 1
        tempFullContour = np.zeros((plateMask.shape[0],plateMask.shape[1]), dtype="uint8")
        cv2.drawContours(tempFullContour, textcontours.contours, i, (255, 255, 255), cv2.FILLED, 8, textcontours.hierarchy)
        plateMask = cv2.bitwise_not(tempFullContour, tempMaskedContour)
        textcontours.goodIndices[i] = False
        beforeMaskWhiteness = cv2.mean(tempFullContour)[0]
        afterMaskWhiteness = cv2.mean(tempMaskedContour)[0]
        if float(afterMaskWhiteness) / beforeMaskWhiteness > minimum_percent_left_after_mask:
            charsInsideMask += 1
            textcontours.goodIndices[i] = True
    if(totalChars == 0):
        textcontours.goodIndices = originalindices
        return textcontours
    percentCharsInsideMask = float(charsInsideMask) / totalChars
    if percentCharsInsideMask < minium_percent_of_chars_inside_plate_mask:
        textcontours.goodIndices = originalindices
        return textcontours

def getCharArea(topLine, bottomLine, bestContours):
    max = 100000
    min = -1
    leftX = max
    rightX = min
    for i in range(0, bestContours.size()):
        if bestContours.goodIndices[i] == False:
            continue
        for z in range(0, len(bestContours.contours[i])):
            if bestContours.contours[i][z][0][0] < leftX:
                leftX = bestContours.contours[i][z][0][0]
                l = leftX
            if bestContours.contours[i][z][0][0] > rightX:
                rightX = bestContours.contours[i][z][0][0]
    charArea = []


    if leftX != max and rightX != min:
        tl = (leftX, topLine.getPointAt(leftX))
        tr = (rightX, topLine.getPointAt(rightX))
        br = (rightX, bottomLine.getPointAt(rightX))
        bl = (leftX, bottomLine.getPointAt(leftX))
        charArea.append(tl)
        charArea.append(tr)
        charArea.append(br)
        charArea.append(bl)
    return charArea

def filterBetweenLines(img, textContours, textLines):
    min_area_percent_within_lines = 0.88
    max_distance_percent_from_lines = 0.15
    if len(textLines) == 0:
        return
    validPoints = []
    rows, cols = img.shape
    outerMask = np.zeros((rows, cols), np.uint8)
    for i in range(0, len(textLines)):

        lp = np.array(textLines[i].linePolygon, np.int32)

        outerMask = cv2.fillConvexPoly(outerMask, lp, (255, 255, 255))
    for i in range(0, textContours.size()):
        if textContours.goodIndices[i] == False:
            continue
        percentInsideMask = getContourAreaPercentInsideMask(outerMask,
                                                            textContours.contours,
                                                            textContours.hierarchy,
                                                            i)

        if percentInsideMask < min_area_percent_within_lines:
            textContours.goodIndices[i] = False
            continue
        x, y, w, h = cv2.boundingRect(textContours.contours[i])
        xmiddle = int(x + (w / 2))
        topMiddle = (xmiddle, y)
        botMiddle = (xmiddle, y + h)

        for j in range(0, len(textLines)):
            closetTopPoint = textLines[j].topLine.closestPointOnSegmentTo(topMiddle)
            closetBottomPoint = textLines[j].bottomLine.closestPointOnSegmentTo(botMiddle)
            absTopDistance = linefinder.distanceBetweenPoints(closetTopPoint, topMiddle)
            absBottomDistance = linefinder.distanceBetweenPoints(closetBottomPoint, botMiddle)
            maxDistance = textLines[j].lineHeight * max_distance_percent_from_lines
            if absTopDistance < maxDistance and absBottomDistance < maxDistance:
                a = 0
            else:
                textContours.goodIndices[j] = False
    return textContours


def getContourAreaPercentInsideMask(mask, contours, hierarchy, contourIndex):
    innerArea = np.zeros((mask.shape[0],mask.shape[1]), dtype="uint8")
    innerArea = cv2.drawContours(innerArea, contours, contourIndex,
                     (255, 255, 255), cv2.FILLED, 8, hierarchy, 2)
    startingPixels = cv2.countNonZero(innerArea)
    innerArea = cv2.bitwise_and(innerArea, mask)
    endingPixels = cv2.countNonZero(innerArea)
    return (float(endingPixels) / float(startingPixels))
# def findOuterBoxMask(contours, hierarchy, thresh):
#     min_parent_are = 100 * 100 * 0.10
#     winningIndex = -1
#     winningParentId = -1
#     bestCharCount = 0
#     lowestArea = 99999999999
#
#     charsRecognizedInContours = np.zeros(len(contours))
#
#     charsRecognized = 0
#
#     parentId = -1
#
#     hasParent = False
#
#     bestParentId = -1
#     i = 0
#     while(i < len(contours)):
#         charsRecognized = charsRecognized + 1
#         parentId = hierarchy[i][3]
#         hasParent = True
#         charsRecognizedInContours[parentId] = + charsRecognizedInContours[parentId] + 1
#         j = 0
#         while(j < len(contours)):
#             if(charsRecognizedInContours[i] > charsRecognized):
#                 charsRecognized = charsRecognizedInContours[i]
#                 bestParentId = i
#             j = j + 1
#
#         boxarea = cv2.contourArea()
#         if(boxarea < min_parent_are):
#             continue
#         if((charsRecognized > bestCharCount) or (charsRecognized == bestCharCount and boxarea < lowestArea)):
#             bestCharCount = charsRecognized
#             winningIndex = i
#             winningParentId = bestParentId
#             lowestArea = boxarea
#
#     if(winningIndex != -1 and bestCharCount >=3):
