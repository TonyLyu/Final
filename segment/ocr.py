from charactersegmenter import CharacterSegmenter
import cv2
import tesserocr
from OcrChar import OcrChar
from PIL import Image
import copy
from rect import Rect
class OCR:
    def __init__(self):
        pass
    def performOCR(self, img_data):

        seg = CharacterSegmenter(img_data)
        img_data = seg.segment()

        absolute_charpos = 0

        for line_idx in range(0, len(img_data.textLines)):
            chars = self.recognize_line(line_idx, img_data)
            print chars
    def expandRect(self, original, expandXPixels, expandYPixels, maxX, maxY):
        expandedRegion = copy.deepcopy(original)
        halfX = round(expandXPixels / 2.0)
        halfY = round(expandYPixels / 2.0)
        expandedRegion.x = expandedRegion.x - halfX
        expandedRegion.width = expandedRegion.width + expandXPixels
        expandedRegion.y = expandedRegion.y - halfY
        expandedRegion.height = expandedRegion.height + expandYPixels
        expandedRegion.x = min(max(expandedRegion.x, 0), maxX)
        expandedRegion.y = min(max(expandedRegion.y, 0), maxY)
        if expandedRegion.x + expandedRegion.width > maxX:
            expandedRegion.width = maxX - expandedRegion.x
        if expandedRegion.y + expandedRegion.height > maxY:
            expandedRegion.height = maxY - expandedRegion.y
        return expandedRegion
    def recognize_line(self, line_idx, img_data):
        with tesserocr.PyTessBaseAPI() as api:
            space_char_code = 32
            recognized_chars = []

            for i in range(0, len(img_data.thresholds)):
                img_data.thresholds[i] = cv2.bitwise_not(img_data.thresholds[i])
                # cv2.imwrite("233.jpg", img_data.thresholds[i])
                cv2.imshow("234123", img_data.thresholds[0])
                cv2.waitKey(0)
                img = Image.fromarray(img_data.thresholds[i])

                #api.SetImage(img)
                api.SetImageFile("233.jpg")
                absolute_charpos = 0
                for j in range(0, len(img_data.charRegions[line_idx])):

                    expandedRegion = self.expandRect(img_data.charRegions[line_idx][j], 2, 2, img_data.thresholds[i].shape[1], img_data.thresholds[i].shape[0])
                    print "finaaly"
                    print expandedRegion.x
                    print expandedRegion.y
                    print expandedRegion.width
                    print expandedRegion.height
                    #api.SetRectangle(expandedRegion.x, expandedRegion.y, expandedRegion.width, expandedRegion.height)

                    api.SetRectangle(0, 0, 180, 80)
                    api.Recognize()
                    ri = api.GetIterator()
                    level = tesserocr.RIL.SYMBOL
                    # while True:
                    for r in tesserocr.iterate_level(ri, level):
                        # symbol = ri.GetUTF8Text(level)
                        symbol = r.GetUTF8Text(level)
                        print symbol
                        conf = r.Confidence(level)
                        fontindex = 0
                        pointsize = 0
                        fontName = r.WordFontAttributes()
                        if symbol != 0 and symbol[0] != space_char_code and pointsize >= 6:
                            c = OcrChar()
                            c.char_index = absolute_charpos
                            c.confidence = conf
                            c.letter = str(symbol)
                            recognized_chars.append(c)
                            indent = False
                            ci = tesserocr.PyChoiceIterator(ri)
                            while True:
                                choice = ci.GetUTF8Text()
                                c2 = OcrChar()
                                c2.char_index = absolute_charpos
                                c2.confidence = ci.Confidence()
                                c2.letter = str(choice)
                                if str(symbol) != str(choice):
                                    recognized_chars.append(c2)
                                else:
                                    recognized_chars.append(c2)
                                indent = True
                                if not ci.Next():
                                    break
                        del symbol
                        if not ri.Next(level):
                                break
                    del ri
                    absolute_charpos += 1
            return recognized_chars




