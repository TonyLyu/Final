import cv2

class Rect:

    def __init__(self, p1, p2, k=0, j=0):
        self.width = 0
        self.height = 0
        if k == 0 and j == 0:
            self.x = min(p1[0], p2[0])
            self.y = min(p1[1], p2[1])

            self.width = max(p1[0], p2[0]) - self.x
            self.height = max(p1[1], p2[1]) - self.y
        else:
            self.x = p1
            self.y = p2
            self.width = k
            self.height = j
        self.p1 = (int(self.x), int(self.y))
        self.p2 = (int(self.x + self.width), int(self.y + self.height))

    def tl(self):

        return (self.x, self.y)

    def br(self):
        return (int(self.x + self.width), int(self.y + self.height))
    def size(self):
        return (self.width, self.height)
    def area(self):
        return self.width * self.height
    def contains(self, pt):
        return self.x <= pt[0] and pt[0] < self.x + self.width and self.y <= pt[1] and pt[1] < self.y + self.height
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

