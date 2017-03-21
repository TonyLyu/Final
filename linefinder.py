import cv2
import textcontours
import math
import sys
class CharPointInfo:
    def __init__(self, contour, index):
        self.contourIndex = index
        self.bx, self.by, self.bw, self.bh= cv2.boundingRect(contour)
        x = self.bx + int(self.bw / 2)
        y = self.by
        self.top = (x, y)
        x = self.bx + int(self.bw / 2)
        y = self.by + self.bh
        self.bottom = (x, y)

class LineFinder:
    def __init__(self, image):
        self.image = image

    def findLines(self, image, contours):

        min_area_to_ignore = 0.65
        linesFound = []
        image = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
        charPoints = []
        for i in range(0, contours.size()):
            if contours.goodIndices[i] == False:
                continue
            charPoint = CharPointInfo(contours.contours[i], i)
            charPoints.append(charPoint)
        bestCharArea = self.getBestLine(contours, charPoints)
        bestLine = self.extendToEdges(contours.width, contours.height, bestCharArea)
        if len(bestLine) > 0:
            linesFound.append(bestLine)
        return linesFound

    def getBestLine(self, contours, charPoints):
        bestStripe = []
        if(len(charPoints) <= 1):
            return bestStripe
        charhights = []
        for i in range(0, len(charPoints)):
            charhights.append(charPoints[i].bh)
        medianCharHeight = self.median(charhights, len(charhights))
        topLines = []
        bottomLines = []
        for i in range(0, len(charPoints)-1):
            for k in range(i+1, len(charPoints)):
                if charPoints[i].top[0] < charPoints[k].top[0]:
                    leftCPIndex = i
                    rightCPIndex = k
                else:
                    leftCPIndex = k
                    rightCPIndex = i
                top = LineSegment(charPoints[leftCPIndex].top[0],
                                  charPoints[leftCPIndex].top[1],
                                  charPoints[rightCPIndex].top[0],
                                  charPoints[rightCPIndex].top[1])
                bottom = LineSegment(charPoints[leftCPIndex].bottom[0],
                                     charPoints[leftCPIndex].bottom[1],
                                     charPoints[rightCPIndex].bottom[0],
                                     charPoints[rightCPIndex].bottom[1])

                parallelBot = top.getParalleLine(medianCharHeight * -1)
                parallelTop = bottom.getParalleLine(medianCharHeight)
                if abs(top.angle) <= 15 and abs(parallelBot.angle) <= 15:
                    topLines.append(top)
                    bottomLines.append(parallelBot)
                if abs(parallelTop.angle) <= 15 and abs(bottom.angle) <= 15:
                    topLines.append(parallelTop)
                    bottomLines.append(bottom)
        bestScoreIndex = 0
        bestScore = -1
        bestScoreDistance = -1
        for i in range(0, len(topLines)):
            scoring_min_threshold = 0.97
            scoring_max_threshold = 1.03
            curScore = 0
            for charidx in range(0, len(charPoints)):
                topYPos = topLines[i].getPointAt(charPoints[charidx].top[0])
                botYPos = bottomLines[i].getPointAt(charPoints[charidx].bottom[0])
                minTop = charPoints[charidx].top[1] * scoring_min_threshold
                maxTop = charPoints[charidx].top[1] * scoring_max_threshold
                minBot = (charPoints[charidx].bottom[1]) * scoring_min_threshold
                maxBot = (charPoints[charidx].bottom[1]) * scoring_max_threshold
                if (topYPos >= minTop and topYPos <= maxTop) and (botYPos >= minBot and botYPos <= maxBot):
                    curScore += 1
            if (curScore > bestScore) or (curScore == bestScore and topLines[i].length > bestScoreDistance):
                bestScore = curScore
                bestScoreIndex = i
                bestScoreDistance = topLines[i].length
        if bestScore < 0:
            return
        bestStripe.append(topLines[bestScoreIndex].p1)
        bestStripe.append(topLines[bestScoreIndex].p2)
        bestStripe.append(bottomLines[bestScoreIndex].p1)
        bestStripe.append(bottomLines[bestScoreIndex].p2)

        return bestStripe



    def extendToEdges(self, width, height, charArea):
        extended = []
        if(len(charArea) < 4):
            return extended
        top = LineSegment(charArea[0][0], charArea[0][1], charArea[1][0], charArea[1][1])
        bottom = LineSegment(charArea[3][0], charArea[3][1], charArea[2][0], charArea[2][1])
        topLeft = (0, top.getPointAt(0))
        topRight = (width, top.getPointAt(width))
        bottomRight = (width, bottom.getPointAt(width))
        bottomLeft = (0, bottom.getPointAt(0))
        extended.append(topLeft)
        extended.append(topRight)
        extended.append(bottomRight)
        extended.append(bottomLeft)

        return extended



    def median(self, array, arraySize):
        if arraySize == 0:
            return 0
        array = sorted(array)
        if arraySize % 2 ==1:
            return array[arraySize / 2]
        else:
            return  array[arraySize / 2 - 1] + array[arraySize / 2] / 2
class LineSegment:

    def __init__(self, x1 = 0, y1 = 0, x2 = 0, y2 = 0):
        self.p1 = (x1, y1)
        self.p2 = (x2, y2)
        if self.p2[0] - self.p1[0] == 0:
            self.slope = 0.00000000001
        else:
            self.slope = float(self.p2[1] - self.p1[1]) / float(self.p2[0] - self.p1[0])
        self.length = distanceBetweenPoints(self.p1, self.p2)
        self.angle = angleBetweenPoints(self.p1, self.p2)

    def getParalleLine(self, distance):
        diff_x = self.p2[0] - self.p1[0]
        diff_y = self.p2[1] - self.p1[1]
        angle = math.atan2(diff_x, diff_y)
        dist_x = distance - math.cos(angle)
        dist_y = distance - math.sin(angle)
        offsetX = int(round(dist_x))
        offsetY = int(round(dist_y))
        result = LineSegment(self.p1[0] + offsetX, self.p1[1] + offsetY,
                             self.p2[0] + offsetX, self.p2[1] + offsetY)
        return result
    def getPointAt(self, x):
        return self.slope * (float(x) - self.p2[0]) + self.p2[1]

    def closestPointOnSegmentTo(self, p):
        top = (p[0] - self.p1[0]) * (self.p2[0] - self.p1[0]) + (p[1] - self.p1[1]) * (self.p2[1] - self.p1[1])
        bottom = distanceBetweenPoints(self.p2, self.p1)
        u = float(top) / bottom
        x = self.p1[0] + u * (self.p2[0] - self.p1[0])
        y = self.p1[1] + u * (self.p2[1] - self.p1[1])
        return (x, y)

    def isPointBelowLine(self, tp):
        return ((self.p2[0] - self.p1[0]) * (tp[1] - self.p1[1]) -
                (self.p2[1] - self.p1[1]) * (tp[0] - self.p1[0])) > 0

    def midpoint(self):
        if self.p1[0] == self.p2[0]:
            ydiff = self.p2[1] - self.p1[1]
            y = self.p1[1] + (float(ydiff) / 2)
        diff = self.p2[0] - self.p1[0]
        midX = float(self.p1[0]) + (float(diff) / 2)
        midY = self.getPointAt(midX)
        return (midX, midY)

    def intersection(self, line):
        intersection_X = -1
        intersection_Y = -1
        c1 = self.p1[1] - self.slope * self.p1[0]
        c2 = line.p2[1] - line.slope * line.p2[0]
        if (self.slope - line.slope) == 0:
            k = 0
        elif self.p1[0] == self.p2[0]:
            return (self.p1[0], line.getPointAt(self.p1[0]))
        elif line.p1[0] == line.p2[0]:
            return (line.p1[0], self.getPointAt(line.p1[0]))
        else:
            intersection_X = (c1 - c2) / (self.slope - line.slope)
            intersection_Y = self.slope * intersection_X + c1

        return (intersection_X, intersection_Y)
def distanceBetweenPoints(p1, p2):
    asquared = float(p2[0] - p1[0]) * (p2[0] - p1[0])
    bsquared = float(p2[1] - p1[1]) * (p2[1] - p1[1])
    return math.sqrt(asquared + bsquared)

def angleBetweenPoints(p1, p2):
    deltaY = int(p2[1] - p1[1])
    deltaX = int(p2[0] - p1[0])
    return math.atan2(float(deltaY), float(deltaX) * (180 / math.pi)
    )
def findClosestPoint(polygon_points, num_points, position):

    closest_point_index = 0
    smallest_distance = sys.maxint
    for i in range(0, num_points):
        pos = (int(polygon_points[i][0]), int(polygon_points[i][1]))
        distance = distanceBetweenPoints(pos, position)
        if distance < smallest_distance:
            smallest_distance = distance
            closest_point_index = i
    return (int(polygon_points[closest_point_index][0]), int(polygon_points[closest_point_index][1]))


def sortPolygonPoints(polygon_points, surrounding_image):
    height, width = surrounding_image
    return_points = []
    return_points.append(findClosestPoint(polygon_points, 4, (0, 0)))
    return_points.append(findClosestPoint(polygon_points, 4, (width, 0)))
    return_points.append(findClosestPoint(polygon_points, 4, (width, height)))
    return_points.append(findClosestPoint(polygon_points, 4, (0, height)))

    return return_points
def drawImageDashboard(images, imageType, numColumns):
    numRows = math.ceil(len(images) / float(numColumns))
