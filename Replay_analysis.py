import carball
from google.protobuf.json_format import MessageToDict
import os
from database import engine, select
import shutil
from zipfile import ZipFile
import time
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor

def get_replay_stats(replay: str) -> dict:
    """

    Parameters
    ----------
    replay : string
        String containing the path to a specific replay file.

    Returns
    -------
    Dict containing all the stats and information from a replay. You'll have to look through
    the structure to find stuff, though, since it's pretty disorganized.

    """
    analysis_manager = carball.analyze_replay_file(replay)
        
    # return the proto object in python
    proto_object = analysis_manager.get_protobuf_data()
    
    # return the pandas data frame in python
    dataframe = analysis_manager.get_data_frame()
    
    stats = MessageToDict(proto_object)
    
    return stats

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

def get_series_stats(replays: list) -> pd.DataFrame:
    """

    Parameters
    ----------
    replays : list
        Takes in a list of replay file paths to be analyzed. List should be between 3 and 5 replays
        for regular season games, and 4-7 for playoffs.

    Returns
    -------
    DataFrame
        Returns a dataframe with all of the stats for each player, plus the stats for all teams
        of 3 players (if a team subbed out a player mid-series).

    """
    players = select("players") # For ID reference
    players.fillna(value=0, inplace=True)
    player_stats = pd.DataFrame(columns = list(players.columns)).set_index("Username")
    columns = list(players.columns[4:])
    columns.remove('Fantasy Value')
    columns.remove('Allowed?')
    columns.remove('Fantasy Points')
    team_stats = pd.DataFrame(columns = columns)
    for replay in replays:
        stats = get_replay_stats(replay)
        
        if stats['gameMetadata']['playlist'] != "CUSTOM_LOBBY":
            print(f"Error {replay}: replay does not appear to be the right playlist")
            continue # I don't even know why I included this, but it makes sure it's a private match
        
        for player in stats['players']: # Get the player's username in the database
            try: name = players.loc[players.id.map(lambda x: player['id']['id'] in str(x), na_action='ignore'),'Username'].values[0]
            except:
                try: name = players.loc[players['Username'] == player['name']].values[0]
                except: 
                    print(player['name'], "couldn't be found")
                    continue
        
            if name not in player_stats.index.values:
                player_stats.append(pd.Series(name=name)) # Create an empty row for each player's stats
        
            

def rlpc_replay_analysis():
    # Get player names, teams, leagues, and IDs in a dataframe for reference
    players = select("select * from players")
    replays = get_rlpc_replays()
    team_stats = select("select * from team_stats")
    all_stats = pd.DataFrame(columns = list(players.columns)).set_index("Username")
    for series in list(replays): # Repeats this for every series downloaded
        team1 = series.split(" - ")[0]
        team2 = series.split(" - ")[1]
        for replay in replays[series]:
            pass
        # TODO: Analyze series stats, save everything to players database