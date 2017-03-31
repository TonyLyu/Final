from charactersegmenter import CharacterSegmenter
import cv2
import tesserocr
from detector import expandRect
from OcrChar import OcrChar
class OCR:
    def __init__(self):
        pass
    def performOCR(self, img_data):
        seg = CharacterSegmenter(img_data)
        seg.segment()
        absolute_charpos = 0
        for line_idx in range(0, len(img_data.testLines)):
            chars = self.recognize_line(line_idx, img_data)

    def recognize_line(self, line_idx, img_data):
        with tesserocr.PyTessBaseAPI() as api:
            space_char_code = 32
            recognized_chars = []
            for i in range(0, len(img_data.thresholds)):
                img_data.thresholds[i] = cv2.bitwise_not(img_data.thresholds[i])
                api.SetImage(img_data.thresholds[i], img_data.thresholds[i].shape[0],
                             img_data.thresholds[i].shape[1])
                absolute_charpos = 0
                for j in range(0, len(img_data.charRegions[line_idx])):
                    expandedRegion = expandRect(img_data.charRegions[line_idx][j], 2, 2, img_data.thresholds[i].shape[1], img_data.thresholds[i].shape[0])
                    api.SetRectangle(expandRect(expandedRegion[0], expandedRegion[1], expandedRegion[2], expandedRegion[3]))
                    api.Recognize(None)
                    ri = api.GetIterator()
                    level = tesserocr.RIL.SYMBOL
                    while True:
                        symbol = ri.GetUTF8Text(level)
                        conf = ri.Confidence(level)
                        fontindex = 0
                        pointsize = 0
                        fontName = ri.WordFontAttributes()
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
                    del  ri
                    absolute_charpos += 1
            return recognized_chars




