import histogram
import cv2


class HistogramVertical(histogram.Histogram):

    def __init__(self, inputImage, mask):
        histogram.Histogram.__init__(self)
        histogram.Histogram.analyzeImage(self, inputImage, mask, True)
