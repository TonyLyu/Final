


class Letter:

    def __init__(self):
        self.letter = ""
        self.line_index = 0
        self.charposition = 0
        self.totalscore = 0.0
        self.occurences = 0
class ResultProcess:

    def __init__(self):
        self.min_confidence = 0
        self.skip_level = 0
        self.letters = []

    def setConfidenceThreshold(self, min_confidence, skip_level):
        self.min_confidence = min_confidence
        self.skip_level = skip_level

    def addLetter(self, letter, line_index, charposition, score):
        if score < self.min_confidence:
            return
        self.insertLetter(letter, line_index, charposition, score)
        if score < self.skip_level:
            adjustedScore = abs(self.skip_level - score) + self.min_confidence
            self.insertLetter("~", line_index, charposition, adjustedScore)

    def insertLetter(self, letter, line_index, charposition, score):
        score = score - self.min_confidence
        existingIndex = -1
        if len(self.letters) < charposition + 1:
            for i in range(len(self.letters), charposition + 1):
                tmp = []
                self.letters.append(tmp)
        for i in range(0, len(self.letters[charposition])):
            if self.letters[charposition][i].letter == letter and self.letters[charposition][i].line_index == line_index and self.letters[charposition][i].charposition == charposition:
                existingIndex = i
                break
        if existingIndex == -1:
            newLetter = Letter()
            newLetter.line_index = line_index
            newLetter.charposition = charposition
            newLetter.letter = letter
            newLetter.occurences = 1
            newLetter.totalscore = score
            self.letters[charposition].append(newLetter)
        else:
            self.letters[charposition][existingIndex].occurences = self.letters[charposition][existingIndex].occurences + 1
            self.letters[charposition][existingIndex].totalscore = self.letters[charposition][existingIndex].totalscore + score