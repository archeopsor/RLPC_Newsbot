import carball
from google.protobuf.json_format import MessageToDict
import os
from Google_Sheets import get_google_sheet, gsheet2df
from database import engine, select

def get_replay_stats(replay):
    analysis_manager = carball.analyze_replay_file(replay, calculate_intensive_events=True)
        
    # return the proto object in python
    proto_object = analysis_manager.get_protobuf_data()
    
    # return the pandas data frame in python
    dataframe = analysis_manager.get_data_frame()
    
    stats = MessageToDict(proto_object)
    
    return(stats, dataframe)

def get_own_replay_files(path = 'C:/Users/Owner/Documents/My Games/Rocket League/TAGame/Demos'):
    # Gets the replay files from the Rocket League demos file
    replays = []
    for file in os.listdir(path):
        replays.append(f"{path}/{file}")
    return replays

def get_rlpc_replays(path='C:/Users/Owner/Desktop/Replay Files'):
    # Gets the replay files downloaded from the RLPC Gamelogs website and extracted to the 'Replay Files' folder
    replays = []
    for folder in os.listdir(path):
        for file in os.listdir(path+'/'+folder):
            replays.append(f"{path}/{folder}/{file}")
    return replays

def rlpc_replay_analysis():
    # Get player names, teams, leagues, and IDs in a dataframe for reference
    players = select("players")
    replays = get_rlpc_replays()
    for game in replays:
        # Analyze the game here
        stats = get_replay_stats(game)[0]
        if stats['gameMetadata']['playlist'] != "CUSTOM LOBBY":
            print(f"Error {game}: replay does not appear to be the right playlist")
            return
        players = stats[players]