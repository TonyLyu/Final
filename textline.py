import cv2
import  linefinder


class TextLine:

    def __init__(self, textArea, linePolygon, width, height):
        self.width = width
        self.linePolygon = []
        self.textArea = []
        textAreaInts = []
        linePolygonInts = []
        for i in range(0, len(textArea)):
            textAreaInts.append((int(round(textArea[i][0])), int(round(textArea[i][1]))))
        for i in range(0, len(linePolygon)):
            linePolygonInts.append((int(round(linePolygon[i][0])), int(round(linePolygon[i][1]))))
        self.initialize(textAreaInts, linePolygonInts, width, height)


    def initialize(self, textArea, linePolygon, width, height):
        if len(textArea)  > 0:
            if(len(self.textArea) > 0):
                self.textArea = []
            if(len(self.linePolygon) > 0):
                self.linePolygon = []

        for i in range(0, len(textArea)):
            self.textArea.append(textArea[i])
        self.topLine = linefinder.LineSegment(linePolygon[0][0], linePolygon[0][1], linePolygon[1][0], linePolygon[1][1])
        self.bottomLine = linefinder.LineSegment(linePolygon[3][0], linePolygon[3][1], linePolygon[2][0], linePolygon[2][1])
        if linePolygon[0][0] != 0:
            linePolygon[0] = (0, self.topLine.getPointAt(linePolygon[0][0]))
        if linePolygon[1][0] != width:
            linePolygon[1] = (width, self.topLine.getPointAt(linePolygon[1][0]))
        if linePolygon[2][0] != width:
            linePolygon[2] = (width, self.bottomLine.getPointAt(linePolygon[2][0]))
        if linePolygon[3][0] != 0:
            linePolygon[3] = (0, self.bottomLine.getPointAt(linePolygon[3][0]))

        for i in range(0, len(linePolygon)):
            self.linePolygon.append(linePolygon[i])
        self.charBoxTop = linefinder.LineSegment(textArea[0][0], textArea[0][1], textArea[1][0], textArea[1][1])
        self.charBoxBottom = linefinder.LineSegment(textArea[3][0], textArea[3][1], textArea[2][0], textArea[2][1])
        self.charBoxLeft = linefinder.LineSegment(textArea[3][0], textArea[3][1], textArea[0][0],textArea[0][1])
        self.charBoxRight = linefinder.LineSegment(textArea[2][0], textArea[2][1], textArea[1][0], textArea[1][1])
        x = float(linePolygon[1][0]) / 2
        midpoint = (int(x), int(self.bottomLine.getPointAt(x)))
        acrossFromMidpoint = self.topLine.closestPointOnSegmentTo(midpoint)

        self.lineHeight = linefinder.distanceBetweenPoints(midpoint, acrossFromMidpoint)
        self.lineHeight = self.lineHeight - 1
        self.angle = (self.topLine.angle + self.bottomLine.angle) / 2
