from charactersegmenter import CharacterSegmenter
import cv2
import tesserocr
from OcrChar import OcrChar
from PIL import Image
from resultprocess import ResultProcess
import copy
import os
from rect import Rect
class OCR:
    def __init__(self):
        pass
    def performOCR(self, img_data):
        postResultMaxCharacters = 8
        seg = CharacterSegmenter(img_data)
        img_data = seg.segment()
        resultProcess = ResultProcess()
        resultProcess.setConfidenceThreshold(65, 80)


        absolute_charpos = 0
        result = []
        for line_idx in range(0, len(img_data.textLines)):
            chars = self.recognize_line(line_idx, img_data)
            for i in range(0, len(chars)):
                line_order_index = line_idx * postResultMaxCharacters + chars[i].char_index
                resultProcess.addLetter(chars[i].letter, line_idx, line_order_index, chars[i].confidence)
            # confidence = 0
            # bestChar = None
            # for char in chars:
            #     print "******"
            #     print char.char_index
            #     print char.letter
            #     print char.confidence
            #     print "********"
            #
            #     if char.char_index == absolute_charpos:
            #         if char.confidence > confidence:
            #             bestChar = char
            #             confidence = char.confidence
            #     if char.char_index > absolute_charpos and isinstance(bestChar, OcrChar):
            #         result.append(bestChar.letter)
            #         absolute_charpos += 1
            #         confidence = 0
            for letter in resultProcess.letters:
                print letter[0].letter



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
        cv2.imshow("final", img_data.thresholds[0])
        with tesserocr.PyTessBaseAPI() as api:
            space_char_code = 32
            recognized_chars = []
            l = os.path.dirname(__file__)
            api.Init(l, "lus")
            api.SetVariable("save_blob_choices", "T")
            api.SetVariable("debug_file", "/dev/null")
            api.SetPageSegMode(tesserocr.PSM.SINGLE_CHAR)
            for i in range(0, len(img_data.thresholds)):

                img_data.thresholds[i] = cv2.bitwise_not(img_data.thresholds[i])

                img = Image.fromarray(img_data.thresholds[i])

                api.SetImage(img)

                absolute_charpos = 0

                for j in range(0, len(img_data.charRegions[line_idx])):

                    expandedRegion = self.expandRect(img_data.charRegions[line_idx][j], 2, 2, img_data.thresholds[i].shape[1], img_data.thresholds[i].shape[0])
                    api.SetRectangle(expandedRegion.x, expandedRegion.y, expandedRegion.width, expandedRegion.height)

                    api.Recognize()
                    ri = api.GetIterator()
                    level = tesserocr.RIL.SYMBOL
                    # while True:
                    for r in tesserocr.iterate_level(ri, level):
                        # symbol = ri.GetUTF8Text(level)
                        symbol = r.GetUTF8Text(level)
                        conf = r.Confidence(level)
                        fontindex = 0
                        pointsize = 0
                        fontName = r.WordFontAttributes()
                        if isinstance(fontName, dict):
                            pointsize = fontName.get('pointsize')
                            fontindex = fontName.get('font_id')

                        if symbol != 0 and symbol[0] != space_char_code and pointsize >= 6:
                            c = OcrChar()
                            c.char_index = absolute_charpos
                            c.confidence = conf
                            c.letter = str(symbol)
                            recognized_chars.append(c)
                            indent = False
                            ci = r.GetChoiceIterator()
                            for c in ci:
                                choice = ci.GetUTF8Text()
                                c2 = OcrChar()
                                c2.char_index = absolute_charpos
                                c2.confidence = c.Confidence()
                                c2.letter = str(choice)
                                if str(symbol) != str(choice):
                                    recognized_chars.append(c2)
                                else:
                                    recognized_chars.append(c2)
                                indent = True

                        del symbol
                        if not ri.Next(level):
                                break
                    del ri
                    absolute_charpos += 1
            return recognized_chars




