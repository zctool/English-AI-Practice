from pyannote.audio import Model
model = Model.from_pretrained("pyannote/embedding", 
                              use_auth_token="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")

from pyannote.audio import Inference
inference = Inference(model, window="whole")
embedding1 = inference("data\parler_tts_out_11447.wav")
embedding2 = inference("parler_tts_out_11466.wav")
# `embeddingX` is (1 x D) numpy array extracted from the file as a whole.

#print(embedding1)
from scipy.spatial.distance import cdist
distance = cdist(embedding1.reshape(1, -1), embedding2.reshape(1, -1), metric="cosine")[0,0]

print(distance)
# `distance` is a `float` describing how dissimilar speakers 1 and 2 are.