import cv2

class Rect:

    def __init__(self, p1, p2):
        self.x = min(p1[0], p2[0])
        self.y = min(p1[1], p2[1])

        self.width = max(p1[0], p2[0]) - self.x
        self.height = max(p1[1], p2[1]) - self.y

    def tl(self):

        return (self.x, self.y)

    def br(self):
        return (self.x + self.width, self.y + self.height)
    def size(self):
        return (self.width, self.height)

    def init(self, x, y, width = 0, height = 0):
        self.x = x
        self.y = y
        if width == 0:
            self.width = abs(self.x[0] - self.y[0])
        else:
            self.width = width
        if height == 0:
            self.height = abs(self.x[1] - self.y[1])
        else:
            self.height =height

