import histogram
import cv2

class HistogramVertical(histogram.Histogram):

    def __init__(self, inputImage, mask):

        histogram.Histogram.analyzeImage(inputImage, mask, True)
