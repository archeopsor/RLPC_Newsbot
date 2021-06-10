import numpy as np

processed = np.load("./xg_model_things/replays.npy")
unprocessed = np.load("./xg_model_things/unprocessedReplays.npy")

print(processed[0])
print(unprocessed[0])