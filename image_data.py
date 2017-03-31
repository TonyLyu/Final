import cv2

class ImageData:
    def __init__(self, colorImage):

        grayImage = cv2.cvtColor(colorImage, cv2.COLOR_BGR2GRAY)
        self.colorImg = colorImage
        self.grayImg = grayImage
        self.plate_inverted = False
        self.disqualified = False
        self.crop_gray = 0
        self.plateBorderMask = 0
        self.hasPlateBorder = False
        self.textLines = []
        self.thresholds = []
        self.plate_corners = []
        self.charRegions = []
        self.charRegionsFlat = []
        self.color_deskewed = None
        self.regionOfInterest = None