import cv2
import numpy as np


class Histogram:

    def __init__(self):
        self.histoImg = None
        self.colHeights = []
    def analyzeImage(self, inputImage, mask, use_y_axis):
        rows, cols = inputImage.shape[:2]
        max_col_size = 0
        if use_y_axis:
            for col in range(0, cols):
                columnCount = 0
                for row in range(0, rows):
                    if inputImage.item(row, col) > 0 and mask.item(row, col) > 0:
                        columnCount += 1
                self.colHeights.append(columnCount)
                if columnCount > max_col_size:
                    max_col_size = columnCount
        else:
            for row in range(0, rows):
                columnCount = 0
                for col in range(0, cols):
                    if inputImage.item(row, col) > 0 and mask.item(row, col) > 0:
                        columnCount += 1
                self.colHeights.append(columnCount)
                if columnCount > max_col_size:
                    max_col_size = columnCount
        histo_width = len(self.colHeights)
        histo_height = max_col_size + 10
        print "histo_width is %d" % histo_width
        print "histo_height is %d" % histo_height
        self.histoImg = np.zeros((histo_height, histo_width), np.uint8)
        for col in range(0, self.histoImg.shape[1]):
            if col > len(self.colHeights):
                break
            columnCount = self.colHeights[col]
            while columnCount > 0:
                self.histoImg.itemset((histo_height - columnCount, col), 255)
                columnCount -= 1
    def getLocalMinimum(self, leftX, rightX):
        minimum = self.histoImg.shape[0] + 1
        lowestX = leftX
        for i in range(leftX, rightX + 1):
            if self.colHeights[i] < minimum:
                lowestX = i
                minimum = self.colHeights[i]
        return lowestX


    def getLocalMaximum(self, leftX, rightX):
        maximum = -1
        highestX = leftX
        for i in range(leftX, rightX + 1):
            if self.colHeights[i] > maximum:
                highestX = i
                maximum = self.colHeights[i]
        return highestX


    def getHeightAt(self, x):
        return self.colHeights[x]

    def detect_peak(self, data, data_count, emi_peaks, num_emi_peaks, max_emi_peaks, absop_peaks, num_absop_peaks, max_absop_peaks,
                    delta, emi_first):
        mx_pos = 0
        mn_pos = 0
        is_detecting_emi = emi_first
        mx = data[0]
        mn = data[0]
        num_emi_peaks = 0
        num_absop_peaks = 0

        for i in range(1, data_count):
            if data[i] > mx:
                mx_pos = i
                mx = data[i]
            if data[i] <  mn:
                mn_pos = i
                mn = data[i]
            if is_detecting_emi and data[i] < mx - delta:
                if num_emi_peaks > max_emi_peaks:
                    return 1
                emi_peaks[num_emi_peaks] = mx_pos
                num_emi_peaks += 1
                is_detecting_emi = 0
                i = mx_pos -1
                mn = data[mx_pos]
                mn_pos = mx_pos
            elif (not is_detecting_emi) and data[i] > mn + delta:
                if num_absop_peaks > max_absop_peaks:
                    return 2
                absop_peaks[num_absop_peaks] = mn_pos
                num_absop_peaks += num_absop_peaks

                is_detecting_emi = 1
                i = mn_pos - 1
                mx = data[mn_pos]
                mx_pos = mn_pos
        return 0
    def get1DHits(self, yOffset):
        hits = []
        onSegment = False
        curSegmentLength = 0
        for col in range(0, self.histoImg.shape[1]):

            isOn = bool(self.histoImg.item(self.histoImg.shape[0] - 1 - yOffset, col))


            if isOn:
                onSegment = True
                curSegmentLength += 1
            if onSegment and (isOn == False or col == self.histoImg.shape[1] -1):
                pair = (col - curSegmentLength, col)
                hits.append(pair)
                onSegment = False
                curSegmentLength = 0
        return hits