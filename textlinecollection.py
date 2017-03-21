import cv2
import linefinder


class TextLineColeection:


    def __init__(self, textLines):
        self.charHeight = 0
        self.charAngle = 0
        for i in range(0, len(textLines)):
            self.charHeight += textLines[i].lineHeight
            self.charAngle += textLines[i].angle

        self.topCharArea = textLines[0].charBoxTop
        self.bottomCharArea = textLines[0].charBoxBottom
        for i in range(1, len(textLines)):
            if self.topCharArea.isPointBelowLine(textLines[i].charBoxTop.midpoint() == False):
                self.topCharArea = textLines[i].charBoxTop
            if self.bottomCharArea.isPointBelowLine(textLines[i].charBoxBottom.midpoint()):
                self.bottomCharArea = textLines[i].charBoxBottom
        self.longerSegment = self.bottomCharArea
        self.shorterSegment = self.topCharArea
        if self.topCharArea.length > self.bottomCharArea.length:
            longerSegment = self.topCharArea
            shorterSegment = self.bottomCharArea

        self.findCenterHorizontal()
        self.findCenterVertical()

    def findCenterHorizontal(self):
        leftP1 = self.shorterSegment.closestPointOnSegmentTo(self.longerSegment.p1)
        leftP2 = self.longerSegment.p1
        left = linefinder.LineSegment(leftP1, leftP2)
        leftMidpoint = left.midpoint()
        rightP1 = self.shorterSegment.closestPointOnSegmentTo(self.longerSegment.p1)
        rightp2 = self.longerSegment.p2
        right = linefinder.LineSegment(rightP1, rightp2)
        rightMidpoint = right.midpoint()
        self.centerHorizontalLine = linefinder.LineSegment(leftMidpoint, rightMidpoint)

    def findCenterVertical(self):
        p1 = self.longerSegment.midpoint()
        p2 = self.shorterSegment.closestPointOnSegmentTo(p1)
        if p1[1] < p2[1]:
            self.centerVerticalLine = linefinder.LineSegment(p1, p2)
        else:
            self.centerVerticalLine = linefinder.LineSegment(p2, p1)
    def isLeftOfText(self, line):
        leftSide = linefinder.LineSegment(self.bottomCharArea.p1, self.topCharArea.p1)
        topLeft = line.closestPointOnSegmentTo(leftSide.p2)
        bottomLeft = line.closestPointOnSegmentTo(leftSide.p1)
        lineIsAboveLeft = (not leftSide.isPointBelowLine(topLeft)) and (not leftSide.isPointBelowLine(bottomLeft))
        if lineIsAboveLeft:
            return 1
        rightSide = linefinder.LineSegment(self.bottomCharArea.p2, self.topCharArea.p2)
        topRight = line.closestPointOnSegmentTo(rightSide.p2)
        bottomRight = line.closestPointOnSegmentTo(rightSide.p1)

        lineIsBelowRight = rightSide.isPointBelowLine(topRight) and rightSide.isPointBelowLine(bottomRight)
        if lineIsBelowRight:
            return -1
        return 0
    def isAboveText(self, line):
        topLeft = line.closestPointOnSegmentTo(self.topCharArea.p1)
        topRight = line.closestPointOnSegmentTo(self.topCharArea.p2)
        lineIsBelowTop = self.topCharArea.isPointBelowLine(topLeft) or self.topCharArea.isPointBelowLine(topRight)
        if not lineIsBelowTop:
            return 1
        bottomLeft = line.closestPointOnSegmentTo(self.bottomCharArea.p1)
        bottomRight = line.closestPointOnSegmentTo(self.bottomCharArea.p2)

        lineIsBelowBottom = self.bottomCharArea.isPointBelowLine(bottomLeft) and self.bottomCharArea.isPointBelowLine(bottomRight)
        if lineIsBelowBottom:
            return -1
        return 0


