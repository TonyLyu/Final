import numpy as np
import cv2

GAUSSIAN_SMOOTH_FILTER_SIZE = (5, 5)
ADAPTIVE_THRESH_BLOCK_SIZE = 19
ADAPTIVE_THRESH_WEIGHT = 9

def maximizeContrast(imgGrayscale):

    height, width = imgGrayscale.shape

    imgTopHat = np.zeros((height, width, 1), np.uint8)
    imgBlackHat = np.zeros((height, width, 1), np.uint8)

    structuringElement = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))

    imgTopHat = cv2.morphologyEx(imgGrayscale, cv2.MORPH_TOPHAT, structuringElement)
    imgBlackHat = cv2.morphologyEx(imgGrayscale, cv2.MORPH_BLACKHAT, structuringElement)

    imgGrayscalePlusTopHat = cv2.add(imgGrayscale, imgTopHat)
    imgGrayscalePlusTopHatMinusBlackHat = cv2.subtract(imgGrayscalePlusTopHat, imgBlackHat)

    return imgGrayscalePlusTopHatMinusBlackHat
def preprocess(original_image):

	height, width, colorchannel = original_image.shape
	imgHSV = np.zeros((height, width, 3), np.uint8)
	imgHSV = cv2.cvtColor(original_image, cv2.COLOR_BGR2HSV)
	imgHue, imgSaturation, imgValue = cv2.split(imgHSV)

	imgMaxContrastGrayscale = maximizeContrast(imgValue)

	imgBlur = np.zeros((height, width, 1), np.uint8)
	imgBlur = cv2.GaussianBlur(imgMaxContrastGrayscale, GAUSSIAN_SMOOTH_FILTER_SIZE, 0)
	imgThresh = cv2.adaptiveThreshold(imgBlur, 255.0, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, ADAPTIVE_THRESH_BLOCK_SIZE, ADAPTIVE_THRESH_WEIGHT)

	return imgValue, imgThresh

img = cv2.imread('imgplate.png')
imgvalue,imgThresh = preprocess(img)
cv2.imshow('1',imgThresh)
cv2.waitKey(0)
