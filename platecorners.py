import cv2
import copy

from scorekeeper import ScoreKeeper
from textlinecollection import TextLineColeection
from linefinder import LineSegment, distanceBetweenPoints
class PlateCorners:
    def __init__(self, inputImage, plateLines, img_data, textLines):
        self.tlc = TextLineColeection(textLines)
        self.img_data = img_data
        self.inputImage = inputImage
        self.plateLines = plateLines
        self.textLines = textLines
        self.bestHorizontalScore = 999999999
        self.bestVerticalScore = 99999999
        self.bestTop = LineSegment()
        self.bestBottom = LineSegment()
        self.bestLeft = LineSegment()
        self.bestRight = LineSegment()

    def getPlateLines(self):
        return self.plateLines

    def findPlateCorners(self):
        horizontalLines = len(self.plateLines.horizontalLines)
        verticalLines = len(self.plateLines.verticalLines)

        for h1 in range(-1, horizontalLines):
            for h2 in range(-1, horizontalLines):
                if h1 == h2 and h1 != -1:
                    continue
                self.scoreHorizontals(h1, h2)
        for v1 in range(-1, verticalLines):
            for v2 in range(-1, verticalLines):
                if v1 == v2 and v1 != -1:
                    continue
                self.scoreVerticals(v1, v2)
        ##show
        imgCorner = copy.deepcopy(self.inputImage)
        imgCorner = cv2.cvtColor(imgCorner, cv2.COLOR_GRAY2RGB)
        for linenum in range(0, len(self.textLines)):
            for i in range(0, 4):
                imgCorner = cv2.circle(imgCorner, self.textLines[linenum].textArea[i], 2, (0, 0, 0))


        imgCorner = cv2.line(imgCorner, self.bestTop.p1, self.bestTop.p2, (255, 0, 0), 1, cv2.LINE_AA)
        imgCorner = cv2.line(imgCorner, self.bestRight.p1, self.bestRight.p2, (0, 0, 255), 1, cv2.LINE_AA)
        imgCorner = cv2.line(imgCorner, self.bestBottom.p1, self.bestBottom.p2, (0, 0, 255), 1, cv2.LINE_AA)
        imgCorner = cv2.line(imgCorner, self.bestLeft.p1, self.bestLeft.p2, (255, 0, 0), 1, cv2.LINE_AA)
        cv2.imshow("winning top and bottom lines", imgCorner)
        ##end
        if self.bestLeft.p1[0] == 0 and self.bestLeft.p1[1] ==0 and self.bestLeft.p2[0] == 0 and self.bestLeft.p2[1] == 0:
            self.img_data.disqualified = True
        elif self.bestTop.p1[0] == 0 and self.bestTop.p1[1] ==0 and self.bestTop.p2[0] == 0 and self.bestTop.p2[1] == 0:
            self.img_data.disqualified = True



        corners = []
        corners.append(self.bestTop.intersection(self.bestLeft))
        corners.append(self.bestTop.intersection(self.bestRight))
        corners.append(self.bestBottom.intersection(self.bestRight))
        corners.append(self.bestBottom.intersection(self.bestLeft))

        return corners

    def scoreVerticals(self, v1, v2):
        scoreKeeper = ScoreKeeper()
        left = LineSegment()
        right = LineSegment()
        charHeightToPlateWidthRatio = 304.8 / 70
        idealPixelWidth = self.tlc.charHeight * (charHeightToPlateWidthRatio * 1.03)
        confidenceDiff = 0
        missingSegmentPenalty = 0


        if v1 == -1 and v2 == -1:
            left = self.tlc.centerVerticalLine.getParalleLine(-1 * idealPixelWidth / 2.0)
            right = self.tlc.centerVerticalLine.getParalleLine(idealPixelWidth / 2.0)
            missingSegmentPenalty = 2
            confidenceDiff += 2

        elif v1 != -1 and v2 != -1:
            left = self.plateLines.verticalLines[v1].line
            right = self.plateLines.verticalLines[v2].line
            confidenceDiff += (1.0 - self.plateLines.verticalLines[v1].confidence)
            confidenceDiff += (1.0 - self.plateLines.verticalLines[v2].confidence)

        elif v1 == -1 and v2 != -1:
            right = self.plateLines.verticalLines[v2].line
            left = right.getParalleLine(idealPixelWidth)
            missingSegmentPenalty += 1
            confidenceDiff += (1.0 - self.plateLines.verticalLines[v2].confidence)
        elif v1 != -1 and v2 == -1:
            left = self.plateLines.verticalLines[v1].line
            right = left.getParalleLine(-1 * idealPixelWidth)
            missingSegmentPenalty += 1
            confidenceDiff += (1.0 - self.plateLines.verticalLines[v1].confidence)
        scoreKeeper.setScore("SCORING_LINE_CONFIDENCE_WEIGHT",confidenceDiff, 18.0)
        scoreKeeper.setScore("SCORING_MISSING_SEGMENT_PENALTY_VERTICAL", missingSegmentPenalty, 10)
        if self.tlc.isLeftOfText(left) < 1 or self.tlc.isLeftOfText(right) > -1:
            return None
        perpendicularCharAngle = self.tlc.charAngle - 90
        charanglediff = abs(perpendicularCharAngle - left.angle) + abs(perpendicularCharAngle - right.angle)
        scoreKeeper.setScore("SCORING_ANGLE_MATCHES_LPCHARS_WEIGHT", charanglediff, 1.1)
        leftMidLinePoint = left.closestPointOnSegmentTo(self.tlc.centerVerticalLine.midpoint())
        rightMidLinePoint = right.closestPointOnSegmentTo(self.tlc.centerHorizontalLine.midpoint())
        actual_width = distanceBetweenPoints(leftMidLinePoint, rightMidLinePoint)
        if actual_width < (idealPixelWidth / 4):
            return None
        plateDistance = abs(idealPixelWidth - actual_width)
        plateDistance = plateDistance / float(self.inputImage.shape[1])
        scoreKeeper.setScore("SCORING_DISTANCE_WEIGHT_VERTICAL",plateDistance, 4.0)
        score = scoreKeeper.getTotal()



        if score < self.bestVerticalScore:

            self.bestVerticalScore = score
            self.bestLeft = LineSegment(left.p1[0], left.p1[1], left.p2[0], left.p2[1])
            self.bestRight = LineSegment(right.p1[0], right.p1[1], right.p2[0], right.p2[1])

    def scoreHorizontals(self, h1, h2):

        scoreKeeper = ScoreKeeper()
        top = LineSegment()
        bottom = LineSegment()

        extra_vertical_pixels = 3
        charHeightToPlateHeightRatio = 152.4 / 70
        idealPixelHeight = self.tlc.charHeight * charHeightToPlateHeightRatio

        missingSegmengtPenalty = 0
        if h1 == -1 and h2 == -1:
            top  =self.tlc.centerHorizontalLine.getParalleLine(idealPixelHeight / 2)
            bottom = self.tlc.centerHorizontalLine.getParalleLine(-1 * idealPixelHeight / 2)
            missingSegmengtPenalty = 2
        elif h1 != -1 and h2 != -1:
            top = self.plateLines.horizontalLines[h1].line
            bottom = self.plateLines.horizontalLines[h2].line
        elif h1 == -1 and h2 != -1:
            bottom = self.plateLines.horizontalLines[h2].line
            top = bottom.getParalleLine(idealPixelHeight + extra_vertical_pixels)
            missingSegmengtPenalty += 1
        elif h1 !=-1 and h2 == -1:
            top = self.plateLines.horizontalLines[h1].line
            bottom = top.getParalleLine(-1 * idealPixelHeight - extra_vertical_pixels)
            missingSegmengtPenalty += 1
        scoreKeeper.setScore("SCORING_MISSING_SEGMENT_PENALTY_HORIZONTAL", missingSegmengtPenalty, 1)

        if self.tlc.isAboveText(top) < 1 or self.tlc.isAboveText(bottom) > -1:
            return None


        topPoint = top.midpoint()
        botPoint = bottom.closestPointOnSegmentTo(topPoint)
        plateHeightPx = distanceBetweenPoints(topPoint, botPoint)
        heightRatio = self.tlc.charHeight / float(plateHeightPx)
        idealHeightRatio = ( 70.0 / 152.4 )



        heightRatioDiff = abs(heightRatio - idealHeightRatio)

        scoreKeeper.setScore("SCORING_PLATEHEIGHT_WEIGHT", heightRatioDiff, 2.2)

        charAreaMidPoint =self.tlc.centerHorizontalLine.midpoint()
        topLineSpot = top.closestPointOnSegmentTo(charAreaMidPoint)
        botLineSpot = bottom.closestPointOnSegmentTo(charAreaMidPoint)
        topDistanceFromMiddle = distanceBetweenPoints(topLineSpot, charAreaMidPoint)
        bottomDistanceFromMiddle = distanceBetweenPoints(botLineSpot, charAreaMidPoint)
        idealDistanceFromMiddle = idealPixelHeight / 2.0

        middleScore = abs(topDistanceFromMiddle - idealDistanceFromMiddle) / float(idealDistanceFromMiddle)
        middleScore += abs(bottomDistanceFromMiddle - idealDistanceFromMiddle) / idealDistanceFromMiddle

        scoreKeeper.setScore("SCORING_TOP_BOTTOM_SPACE_VS_CHARHEIGHT_WEIGHT", middleScore, 2.0)
        charanglediff = abs(self.tlc.charAngle - top.angle) + abs(self.tlc.charAngle - bottom.angle)


        scoreKeeper.setScore("SCORING_ANGLE_MATCHES_LPCHARS_WEIGHT", charanglediff, 1.1)
        score = scoreKeeper.getTotal()

        if score < self.bestHorizontalScore:

            self.bestHorizontalScore = score
            self.bestTop = LineSegment(top.p1[0], top.p1[1], top.p2[0], top.p2[1])
            self.bestBottom = LineSegment(bottom.p1[0], bottom.p1[1], bottom.p2[0], bottom.p2[1])