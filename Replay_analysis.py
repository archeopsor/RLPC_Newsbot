import carball
from google.protobuf.json_format import MessageToDict
import os
from Google_Sheets import get_google_sheet, gsheet2df
from database import engine, select
import shutil
from zipfile import ZipFile
import time

def get_replay_stats(replay):
    analysis_manager = carball.analyze_replay_file(replay)
        
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

def get_rlpc_replays(path='C:/Users/Owner/Downloads'):
    # Extracts files from downloads to replay files folder, then gets a list of those filenames
    files = {}
    for download in os.listdir(path):
        new = os.path.getmtime(f"{path}/{download}") > time.time()-80000 # Make sure to only include files newer than 1 day
        if download.endswith('.zip') and new:
            replays = []
            teams = download.split(" - ")[0].split(" vs. ")
            name = f"{teams[0]} - {teams[1]}"
            with ZipFile(f"{path}/{download}", 'r') as zip_ref:
                zip_ref.extractall(f"C:/Users/Owner/Desktop/Replay Files/{name}") # Extract files to new folder
            for folder in os.listdir(f"C:/Users/Owner/Desktop/Replay Files/{name}"):
                filename = os.listdir(f"C:/Users/Owner/Desktop/Replay Files/{name}/{folder}")[0]
                replays.append(f"C:/Users/Owner/Desktop/Replay Files/{name}/{folder}/{filename}")
            files[name] = replays
    return files

def rlpc_replay_analysis():
    # Get player names, teams, leagues, and IDs in a dataframe for reference
    players = select("select * from players")
    replays = get_rlpc_replays()
    for series in list(replays): # Repeats this for every series downloaded
        team1 = series.split(" - ")[0]
        team2 = series.split(" - ")[1]
        for replay in replays[series]:
            # Analyze the game here
            stats = get_replay_stats(replay)[0]
            if stats['gameMetadata']['playlist'] != "CUSTOM_LOBBY":
                print(f"Error {replay}: replay does not appear to be the right playlist")
                return
            players = stats[players]
            # TODO: Analyze game stats
        # TODO: Analyze series stats, save everything to players database
        