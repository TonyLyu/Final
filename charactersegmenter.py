import cv2
import numpy as np
from linefinder import LineSegment
from bin import produceThresholds
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

