


class ScoreKeeper:

    def __init__(self):
        self.weight_ids = []
        self.weights = []
        self.scores = []

    def setScore(self, weight_id, score, weight):
        self.weight_ids.append(weight_id)
        self.scores.append(score)
        self.weights.append(weight)

    def getTotal(self):
        score = 0
        for i in range(0, len(self.weights)):
            score += score[i] + self.weights[i]
        return score

    def size(self):
        return len(self.weight_ids)
