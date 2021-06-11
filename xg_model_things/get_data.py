import os
from xg_model_things.x_goals import xG
import numpy as np

unprocessedReplays: np.ndarray = np.load("xg_model_things/unprocessedReplays.npy")
allReplays: np.ndarray = np.load("xg_model_things/replays.npy")
total_data: np.ndarray = np.load("xg_model_things/data.npy")
counter: int = len(allReplays) - len(unprocessedReplays) + 1

for replay in unprocessedReplays:
    print(f"Replay {counter} of {len(allReplays)}")
    replay: str = replay
    try:
        frames, stats = xG.decompile_replay(replay)
        data: np.ndarray = xG.get_input_data(frames, stats)
        for hit in data:
            total_data = np.append(total_data, hit)
    except:
        print(replay + " failed")
    unprocessedReplays = np.delete(unprocessedReplays, 0)
    counter += 1

    np.save("./xg_model_things/data.npy", total_data)
    np.save("./xg_model_things/unprocessedReplays", unprocessedReplays)