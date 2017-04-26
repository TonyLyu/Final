from featurematcher import FeatureMatcher
import os
fea = FeatureMatcher()
runDir = os.path.dirname(__file__)
fea.loadRecognitionSet(runDir, "ca")
