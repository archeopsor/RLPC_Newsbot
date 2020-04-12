import carball
from google.protobuf.json_format import MessageToDict

def get_replay_stats(replay):

    analysis_manager = carball.analyze_replay_file(replay)
        
    # return the proto object in python
    proto_object = analysis_manager.get_protobuf_data()
    
    # return the pandas data frame in python
    dataframe = analysis_manager.get_data_frame()
    
    stats = MessageToDict(proto_object)
    
    return(stats, dataframe)
