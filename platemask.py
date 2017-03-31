import cv2
import numpy as np

class platemask:

    def __init__(self, thresholds):
        self.hasplatemask = False
        self.thresholds = thresholds
        self.plateMask = None

    def getMask(self):
        return self.plateMask
    def findOuterBoxMask(self, contours):

        min_parent_area = 120 * 60 * 0.10
        winningIndex = -1
        winningParentId = -1
        bestCharCount = 0
        lowestArea = 99999999999

        for imgIndex in range(0, len(contours)):
            charsRecognized = 0

            parentId = -1

            hasParent = False

            bestParentId = -1
            charsRecognizedInContours = np.zeros(len(contours[imgIndex].goodIndices))
            for i in range(0, len(contours[imgIndex].goodIndices)):
                if contours[imgIndex].goodIndices[i]:
                    charsRecognized += 1
                if contours[imgIndex].goodIndices[i] and contours[imgIndex].hierarchy[0][i][3] != -1:
                    parentId = contours[imgIndex].hierarchy[i][3]
                    hasParent = True
                    charsRecognizedInContours[parentId] += 1
            if charsRecognized == 0:
                continue
            if hasParent:
                charsRecognized = 0
            for i in range(0, len(contours[imgIndex].goodIndices)):
                if charsRecognizedInContours[i] > charsRecognized:
                    charsRecognized = charsRecognizedInContours[i]
                    bestParentId = i
            boxarea = cv2.contourArea(contours[imgIndex].contours[bestParentId])
            if boxarea < min_parent_area:
                continue
            if charsRecognized > bestCharCount or (charsRecognized == bestCharCount and boxarea < lowestArea):
                bestCharCount = charsRecognized
                winningIndex = imgIndex
                winningParentId = bestParentId
                lowestArea = boxarea
        print "Winning image index (findOOuterBoxMask) is : %d" % winningIndex
        if winningIndex != -1 and bestCharCount >= 3:
            mask = np.zeros(len(self.thresholds[winningIndex]), dtype = 'uint8')
            cv2.drawContours(mask, contours[winningIndex].contours, winningParentId,
                             (255, 255, 255),cv2.FILLED, 8, contours[winningIndex].hierarchy,
                             0)
            morph_elem = 2
            morph_size = 3
            element = cv2.getStructuringElement(morph_elem,
                                                (2 * morph_size + 1, 2 * morph_size + 1),
                                                (morph_size, morph_size))
            mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, element)
            contoursSecondRound = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            biggestContourIndex = -1
            largestArea = 0.0
            for c in range(0, len(contoursSecondRound)):
                area = cv2.contourArea(contoursSecondRound[c])
                if area > largestArea:
                    biggestContourIndex = c
                    largestArea = area
            if biggestContourIndex != -1:
                mask = np.zeros((self.thresholds[winningIndex].shape[0], self.thresholds[winningIndex].shape[1]), dtype = 'uint8')
                smoothedMaskPoints = cv2.approxPolyDP(contoursSecondRound[biggestContourIndex], 2, True)
                tempvec = []
                tempvec.append(smoothedMaskPoints)
                cv2.drawContours(mask, tempvec, 0, (255, 255, 255), cv2.FILLED, 8, contours[winningIndex].hierarchy, 0)
            self.hasplatemask = True
            self.plateMask = mask
        else:
            self.hasplatemask = False
            fullMask = np.zeros((self.thresholds[0].shape[0], self.thresholds[0].shape[1]), dtype="uint8")
            fullMask = cv2.bitwise_not(fullMask)
            self.plateMask = fullMask
