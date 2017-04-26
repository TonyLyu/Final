import cv2
from segment.rect import Rect
from linefinder import LineSegment
import os
class RecognitionResult:

    def __init__(self):
        self.haswinner = False
        self.winner = ""
        self.confidence = 0

class FeatureMatcher:
    def __init__(self):
        self.descriptorMatcher = cv2.BFMatcher(cv2.NORM_HAMMING, False)
        self.detector = cv2.FastFeatureDetector_create(5, True)
        self.extractor = cv2.BRISK_create(5, 1, 0.9)
        self.billMapping = []
        self.h = 0
        self.w = 0
        self.trainingImgKeypoints = []

    def isLoaded(self):
        if self.descriptorMatcher == None or self.extractor == None or self.detector == None:
            return False
        return True
    def numTrainingElements(self):
        return len(self.billMapping)
    def surfStyleMatching(self, queryDescriptors, queryKeypoints, matches12):

        matchesKnn = self.descriptorMatcher.radiusMatch(queryDescriptors, 100.0)
        tempMatches = []
        queryDescriptors, tempMatches = self._surfStyleMatching(queryDescriptors, matchesKnn, tempMatches)
        queryKeypoints, matches12 = self.crisscrossFiltering(queryKeypoints, tempMatches, matches12)
        return  queryKeypoints, matches12
    def _surfStyleMatching(self, queryDescriptors, matchesKnn, matches12):
        rows, cols = queryDescriptors.shape[:2]
        for descInd in range(rows):
            if len(matchesKnn[descInd]) > 1:
                ratioThreshold = 0.75
                if matchesKnn[descInd][0].imgIdx == matchesKnn[descInd][1].imgIdx:
                    ratioThreshold = 0.85
                if matchesKnn[descInd][0].distance / matchesKnn[descInd][1].distance < ratioThreshold:
                    already_exists = False
                    for q in range(len(matches12)):
                        if matchesKnn[descInd][0].queryIdx == matches12[q].queryIdx:
                            already_exists = True
                            break
                        elif matchesKnn[descInd][0].trainIdx == matches12[q].trainIdx and matchesKnn[descInd][0].imgIdx == matches12[q].imgIdx:
                            already_exists = True
                            break
                    if already_exists == False:
                        matches12.append(matchesKnn[descInd][0])
            elif len(matchesKnn[descInd]) == 1:
                matches12.append(matchesKnn[descInd][0])
        return queryDescriptors, matches12
    def crisscrossFiltering(self, queryKeypoints, inputMatches, outputMatches):
        crissCrossAreaVertical = Rect(0, 0, self.w, self.h * 2)
        crissCrossAreaHorizontal = Rect(0, 0, self.w * 2, self.h)
        for i in range(len(self.billMapping)):
            matchesForOnePlate = []
            for j in range(len(inputMatches)):
                if inputMatches[j].imgIdx == int(i):
                    matchesForOnePlate.append(inputMatches[j])
            vlines = []
            hlines = []
            matchIdx = []
            for j in range(len(matchesForOnePlate)):
                tkp = self.trainingImgKeypoints[i][matchesForOnePlate[j].trainIdx]
                qkp = queryKeypoints[matchesForOnePlate[j].queryIdx]
                vlines.append(LineSegment(tkp.pt[0], tkp.pt[1] + self.h, qkp.pt[0], qkp.pt[1]))
                hlines.append(LineSegment(tkp.pt[0], tkp.pt[1], qkp.pt[0] + self.w, qkp.pt[1]))
                matchIdx.append(j)
            mostIntersections = 1
            while mostIntersections > 0 and len(vlines) > 0:
                mostIntersectionsIndex = -1
                mostIntersections = 0
                for j in range(len(vlines)):
                    intrCount = 0
                    for q in range(len(vlines)):
                        vintr = vlines[j].intersection(vlines[q])
                        hintr = hlines[j].intersection(hlines[q])
                        vangleDiff = abs(vlines[j].angle - vlines[q].angle)
                        hangleDiff = abs(hlines[j].angle - hlines[q].angle)

                        if self.inside(vintr, crissCrossAreaVertical) and vangleDiff > 10:
                            intrCount += 1
                        elif self.inside(hintr, crissCrossAreaHorizontal) and hangleDiff > 10:
                            intrCount += 1
                    if intrCount > mostIntersections:
                        mostIntersections = intrCount
                        mostIntersectionsIndex = j
                if mostIntersectionsIndex >= 0:
                    del vlines[mostIntersectionsIndex]
                    del hlines[mostIntersectionsIndex]
                    del matchIdx[mostIntersectionsIndex]
            for j in range(len(matchIdx)):
                outputMatches.append(matchesForOnePlate[matchIdx[j]])
        return queryKeypoints, outputMatches
    def inside(self, point, rect):
        if point[0] > rect.x and point[0] < rect.x + rect.width and point[1] > rect.y and point[1] < rect.y + rect.height:
            return True
        return False
    def recognize(self, queryImg, drawOnImage, outputImage, debug_on, debug_matches_array):

        result = RecognitionResult()
        self.w = queryImg.shape[1]
        self.h = queryImg.shape[0]
        result.haswinner = False
        result.confidence = 0

        queryKeypoints = self.detector.detect(queryImg, None)
        queryKeypoints, queryDescriptors = self.extractor.compute(queryImg, queryKeypoints)
        if len(queryKeypoints) <= 5:
            if drawOnImage:
                cv2.drawKeypoints(queryImg, queryKeypoints, outputImage, (0, 255, 0), cv2.DrawMatchesFlags_DEFAULT)
            return result
        filteredMatches = []
        queryDescriptors, filteredMatches = self.surfStyleMatching(queryDescriptors, queryKeypoints, filteredMatches)

        bill_match_counts = []
        for i in range(len(self.billMapping)):
            bill_match_counts.append(0)
        for i in range(len(filteredMatches)):
            bill_match_counts[filteredMatches[i].imgIdx] += 1
        max_count = 0
        secondmost_count = 0
        maxcount_index = -1
        for i in range(len(self.billMapping)):
            if bill_match_counts[i] > max_count and bill_match_counts[i] >= 4:
                secondmost_count = max_count
                if secondmost_count <= 2:
                    secondmost_count = 0
                max_count = bill_match_counts[i]
                maxcount_index = i
        score = ((max_count - secondmost_count - 1) / 10.0) * 100.0
        if score < 0:
            score = 0
        elif score > 100:
            score = 100

        if score > 0:
            result.haswinner = True
            result.winner = self.billMapping[maxcount_index]
            result.confidence = score
            if drawOnImage:
                positiveMatches = []
                for i in range(len(filteredMatches)):
                    if filteredMatches[i].imgIdx == maxcount_index:
                        positiveMatches.append(queryKeypoints[filteredMatches[i].queryIdx])
                temImg = None
                temImg = cv2.drawKeypoints(queryImg, queryKeypoints, temImg, (185, 0, 0), cv2.DrawMatchesFlags_DEFAULT)
                cv2.drawKeypoints(temImg, positiveMatches, outputImage, (0, 255, 0), cv2.DrawMatchesFlags_DEFAULT)
                if result.haswinner:
                    print "result is %s" % result.winner
        return result
    def loadRecognitionSet(self, directory, country):
        country_dir = directory + "/" + country + "/"
        print country_dir
        plateFiles = []
        if os.path.isdir(country_dir):
            trainImages = []
            plateFiles = []
            for (dirpath, dirnames, filenames) in os.walk(country_dir):
                for f in filenames:
                    if os.path.splitext(f)[1] == ".jpg" or os.path.splitext(f)[1] == ".png":
                        filepath = os.path.join(dirpath, f)
                        plateFiles.append(f)
            for plateFile in plateFiles:
                fullpath = country_dir + plateFile
                img = cv2.imread(fullpath)
                img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                # if img == None:
                #     print "can not read images"
                #     return False
                keypoints = []
                keypoints = self.detector.detect(img, None)
                keypoints, descriptors = self.extractor.compute(img, keypoints)
                if descriptors.shape[1] > 0:
                    self.billMapping.append(plateFile[0:2])
                    trainImages.append(descriptors)
                    self.trainingImgKeypoints.append(keypoints)
            self.descriptorMatcher.add(trainImages)
            self.descriptorMatcher.train()
            return True
        return False














