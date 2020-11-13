import carball
from google.protobuf.json_format import MessageToDict

import pandas as pd
import numpy as np

import tensorflow as tf
from tensorflow import keras
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense

NORMALISATION_FACTORS = {
    'pos_x': 4096,
    'pos_y': 6000,
    'pos_z': 2048,
    'vel_x': 23000,
    'vel_y': 23000,
    'vel_z': 23000,
    'ang_vel_x': 5500,
    'ang_vel_y': 5500,
    'ang_vel_z': 5500,
    'throttle': 255,
    'steer': 255,
    'rot_x': np.pi,
    'rot_y': np.pi,
    'rot_z': np.pi,
    'boost': 255,
}

def normalise_df(df: pd.DataFrame, inplace: bool = False) -> pd.DataFrame:
    """
    A function to convert frame-by-frame values into numbers between -1 and 1
    
    Parameters
    ----------
    df : pd.DataFrame
        Dataframe containing the frame info from the replay.
    inplace : bool, optional
        Whether or not to keep the original numbers in the dataframe.
        The default is False.

    Returns
    -------
    df : pd.DataFrame
        Normalised Dataframe.

    """
    
    if not inplace:
        df = df.copy()
    for column, normalisation_factor in NORMALISATION_FACTORS.items():
        df.loc[:, (slice(None), column)] /= normalisation_factor
    return df
    
    
def decompile_replay(replay_path: str):
    analysis_manager = carball.analyze_replay_file(replay_path)
    frames = analysis_manager.get_data_frame().fillna(value=0)
    stats = MessageToDict(analysis_manager.get_protobuf_data())
    return frames, stats


def get_input_data(frames: pd.DataFrame, stats: pd.DataFrame) -> np.ndarray:
    labels = [[],[]]
    
    hits = stats['gameStats']['hits'] # List of each hit in the game
    hits = [hit for hit in hits if not hit['isKickoff']] # Don't include kickoff hits
    
    frames = normalise_df(frames)
    
    teams = [{}, {}] # List with dicts for id/name pairs for each team
    for i in [0,1]:
        for playerId in stats['teams'][i]['playerIds']:
            for player in stats['players']:
                if player['id']['id'] == playerId['id']:
                    teams[i][playerId['id']] = player['name']
                    break
                else:
                    continue
    
    datapoints = []
    for hit in hits:
        values = []
        
        shooting_team = 0
        playerId = hit['playerId']['id']

        try:
            player = teams[0][playerId]
            shooting_team = 0
        except:
            player = teams[1][playerId]
            shooting_team = 1
        frame_num = hit['frameNumber'] - 15 # 15 frames (half a sec) before hit
        
        # Add shooting player's stats to the first 15 values
        for value in frames.loc[frame_num, player].loc[list(NORMALISATION_FACTORS)]:
            values.append(value)
            
        # Add two team members' stats to next 30 values
        for teammateId in teams[shooting_team]:
            if teammateId == playerId:
                continue
            teammateName = teams[shooting_team][teammateId]
            for value in frames.loc[frame_num, teammateName].loc[list(NORMALISATION_FACTORS)]:
                values.append(value)
                
        # Add three defenders' stats to next 45 values
        for defenderId in teams[1-shooting_team]:
            defenderName = teams[1-shooting_team][defenderId]
            for value in frames.loc[frame_num, defenderName].loc[list(NORMALISATION_FACTORS)]:
                values.append(value)
                
        # Add the ball's position and velocity to next 6 values
        for value in frames.loc[frame_num, 'ball'].loc['pos_x':'vel_z']:
            values.append(value)
            
        # Add additional hit stats to goal to the last two values
        values.append(hit['distanceToGoal']/12000)
        try:
            values.append(0+hit['passed'])
        except:
            values.append(0)
        
        datapoints.append(np.array(values))
        
        labels[0].append(player)
        try:
            labels[1].append(1 if hit['goal'] else 0)
        except:
            labels[1].append(0)
    
    return np.array(datapoints)
    
def build_model():
    model = Sequential([
    Dense(64, activation='relu', input_shape=(98,)), # 98-value input, 15 values per player plus 6 for the ball and 2 for the distance to goal/if passed
    Dense(64, activation='relu'),
    Dense(64, activation='relu'),
    Dense(1, activation='softmax'),
    ])
    
    model.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['accuracy'])