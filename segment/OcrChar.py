import cv2

class OcrChar:
    def __init__(self):
        self.letter = ""
        self.char_index = 0
        self.confidence = 0.0