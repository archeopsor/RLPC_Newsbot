import carball
from google.protobuf.json_format import MessageToDict
import os

def get_replay_stats(replay):

    analysis_manager = carball.analyze_replay_file(replay)
        
    # return the proto object in python
    proto_object = analysis_manager.get_protobuf_data()
    
    # return the pandas data frame in python
    dataframe = analysis_manager.get_data_frame()
    
    stats = MessageToDict(proto_object)
    
    return(stats, dataframe)


def get_replay_files(path = 'C:/Users/Owner/Documents/My Games/Rocket League/TAGame/Demos'):
    # Gets the replay files from the Rocket League demos file
    replays = []
    for file in os.listdir(path):
        replays.append(f"{path}/{file}")
    return replays