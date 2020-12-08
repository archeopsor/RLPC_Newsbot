import carball
from google.protobuf.json_format import MessageToDict
import os
from database import engine, select
from zipfile import ZipFile
import time
import pandas as pd
from RLPC_Players import download_ids, identify, find_team, find_league, check_players
import logging

def fantasy_formula(row: pd.Series) -> int:
    """
    Determines fantasy points earned by a player given their stats

    Parameters
    ----------
    row : pd.Series
        Row of Dataframe with all the player's stats.

    Returns
    -------
    int
        Number of fantasy points earned.

    """
    points = 0
    gp = row['Games Played']
    
    if gp == 0:
        return 0
    
    points += (row['Goals']/gp)*21
    points += (row['Assists']/gp)*15
    points += (row['Shots']/gp)*3
    points += (row['Saves']/gp)*13
    points += (row['Demos Inflicted']/gp)*6
    points += (row['Clears']/gp)*4
    points += (row['Passes']/gp)*2
    points += (row['Turnovers Won']/gp)*0.6
    points += (row['Turnovers Lost']/gp)*(-0.3)
    points += (row['Series Won'])*5
    points += (row['Games Won'])*1
    
    return round(points)

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

    analysis_manager = carball.analyze_replay_file(replay, logging_level=logging.CRITICAL)
        
    # return the proto object in python
    proto_object = analysis_manager.get_protobuf_data()
    
    # return the pandas data frame in python
    #dataframe = analysis_manager.get_data_frame()
    
    stats = MessageToDict(proto_object)
    
    return stats

def get_own_replay_files(path = 'C:/Users/Simi/Documents/My Games/Rocket League/TAGame/Demos') -> list:
    """

    Parameters
    ----------
    path : str, optional
        Where to get the replay files from. The default is 'C:/Users/Simi/Documents/My Games/Rocket League/TAGame/Demos'.

    Returns
    -------
    replays : list
        List of strings that are paths to replay files.

    """
    replays = []
    for file in os.listdir(path):
        replays.append(f"{path}/{file}")
    return replays

def get_rlpc_replays(path='C:/Users/Simi/Downloads', download_files = True) -> list:
    """

    Parameters
    ----------
    path : str, optional
        Where to get the downloaded replay files from. The default is 'C:/Users/Owner/Downloads'.
        
    download_files : bool, optional
        Whether or not to download replay files from the rlpcgamelogs website. The default is True.

    Returns
    -------
    files : list
        Extracts files from downloads to replay files folder, then gets a list of those filenames.

    """
    # if download_files:
    #     import download
    
    files = {}
    for download in os.listdir(path):
        new = os.path.getmtime(f"{path}/{download}") > time.time()-(5*80000) # Make sure to only include files newer than 1 day
        if download.endswith('.zip') and new:
            replays = []
            teams = download.split(" - ")[0].split(" vs. ")
            name = f"{teams[0]} - {teams[1]}"
            with ZipFile(f"{path}/{download}", 'r') as zip_ref:
                zip_ref.extractall(f"C:/Users/Simi/Desktop/Replay Files/{name}") # Extract files to new folder
            for folder in os.listdir(f"C:/Users/Simi/Desktop/Replay Files/{name}"):
                filename = os.listdir(f"C:/Users/Simi/Desktop/Replay Files/{name}/{folder}")[0]
                replays.append(f"C:/Users/Simi/Desktop/Replay Files/{name}/{folder}/{filename}")
            files[name] = replays
    return files

def get_series_stats(replays: list, players: pd.DataFrame) -> pd.DataFrame:
    """

    Parameters
    ----------
    replays : list
        Takes in a list of replay file paths to be analyzed. List should be between 3 and 5 replays
        for regular season games, and 4-7 for playoffs.

    players : DataFrame
        DataFrame containing SQL players database info

    Returns
    -------
    DataFrame
        Returns a dataframe with all of the stats for each player, plus the stats for all teams
        of 3 players (which would be more than one if a team subbed out a player mid-series).

    """

    players.fillna(value=0, inplace=True)
    player_stats = pd.DataFrame(columns = list(players.columns))
    player_stats = player_stats.iloc[:,9:]
    columns = list(player_stats.columns)
    team_stats = pd.DataFrame(columns = columns)
    for replay in replays:
        stats = get_replay_stats(replay)
        
        temp_player_stats = player_stats.copy()
        temp_player_stats = temp_player_stats.iloc[0:0]
        
        winner = 0
        if stats['teams'][1]['score'] > stats['teams'][0]['score']:
            winner = 1
        
        if stats['gameMetadata']['playlist'] != "CUSTOM_LOBBY":
            print(f"Error {replay}: replay does not appear to be the right playlist")
            continue # I don't even know why I included this, but it makes sure it's a private match
        
        team1_name = find_team([x['id'] for x in stats['teams'][0]['playerIds']], players, id_players = True)
        team2_name = find_team([x['id'] for x in stats['teams'][1]['playerIds']], players, id_players = True)
            
        team1_stats = pd.Series(index = columns, name=team1_name, dtype=object).fillna(0)
        team2_stats = pd.Series(index = columns, name=team2_name, dtype=object).fillna(0)
        team1_players = []
        team2_players = []
        
        for player in stats['players']: 
            name = identify(player['id']['id'], players)
            if name == None:
                name = player['name']
            if name not in temp_player_stats.index.values:
                temp_player_stats = temp_player_stats.append(pd.Series(name=name, dtype=object)).fillna(0) # Create an empty row for each player's stats
            
            # Add individual stats to the temp_player_stats dataframe
            temp_player_stats.loc[name, 'Games Played'] += 1 # Add 1 game played
            if str(player['id']['id']) in [x['id'] for x in stats['teams'][winner]['playerIds']]:
                temp_player_stats.loc[name, 'Games Won'] += 1 # Add 1 game won only if they won
            try: temp_player_stats.loc[name, 'Goals'] += player['goals']
            except: pass
            try: temp_player_stats.loc[name, 'Assists'] += player['assists']
            except: pass
            try: temp_player_stats.loc[name, 'Saves'] += player['saves']
            except: pass
            try: temp_player_stats.loc[name, 'Shots'] += player['shots']
            except: pass
            try: temp_player_stats.loc[name, 'Dribbles'] += player['stats']['hitCounts']['totalDribbles']
            except: pass
            try: temp_player_stats.loc[name, 'Passes'] += player['stats']['hitCounts']['totalPasses']
            except: pass
            try: temp_player_stats.loc[name, 'Aerials'] += player['stats']['hitCounts']['totalAerials']
            except: pass
            try: temp_player_stats.loc[name, 'Hits'] += player['stats']['hitCounts']['totalHits']
            except: pass
            try: temp_player_stats.loc[name, 'Boost Used'] += player['stats']['boost']['boostUsage']
            except: pass
            try: temp_player_stats.loc[name, 'Wasted Collection'] += player['stats']['boost']['wastedCollection']
            except: pass
            try: temp_player_stats.loc[name, 'Wasted Usage'] += player['stats']['boost']['wastedUsage']
            except: pass
            try: temp_player_stats.loc[name, '# Small Boosts'] += player['stats']['boost']['numSmallBoosts']
            except: pass
            try: temp_player_stats.loc[name, '# Large Boosts'] += player['stats']['boost']['numLargeBoosts']
            except: pass
            try: temp_player_stats.loc[name, '# Boost Steals'] += player['stats']['boost']['numStolenBoosts']
            except: pass
            try: temp_player_stats.loc[name, 'Wasted Big'] += player['stats']['boost']['wastedBig']
            except: pass
            try: temp_player_stats.loc[name, 'Wasted Small'] += player['stats']['boost']['wastedSmall']
            except: pass
            try: temp_player_stats.loc[name, 'Time Slow'] += player['stats']['speed']['timeAtSlowSpeed']
            except: pass
            try: temp_player_stats.loc[name, 'Time Boost'] += player['stats']['speed']['timeAtBoostSpeed']
            except: pass
            try: temp_player_stats.loc[name, 'Time Supersonic'] += player['stats']['speed']['timeAtSuperSonic']
            except: pass
            try: temp_player_stats.loc[name, 'Turnovers Lost'] += player['stats']['possession']['turnovers']
            except: pass
            try: temp_player_stats.loc[name, 'Defensive Turnovers Lost'] += (player['stats']['possession']['turnovers'] - player['stats']['possession']['turnoversOnTheirHalf'])
            except: pass
            try: temp_player_stats.loc[name, 'Offensive Turnovers Lost'] += player['stats']['possession']['turnoversOnTheirHalf']
            except: pass
            try: temp_player_stats.loc[name, 'Turnovers Won'] += player['stats']['possession']['wonTurnovers']
            except: pass
            try: temp_player_stats.loc[name, 'Kickoffs'] += player['stats']['kickoffStats']['totalKickoffs']
            except: pass
            try: temp_player_stats.loc[name, 'First Touches'] += player['stats']['kickoffStats']['numTimeFirstTouch']
            except: pass
            try: temp_player_stats.loc[name, 'Kickoff Cheats'] += player['stats']['kickoffStats']['numTimeCheat']
            except: pass
            try: temp_player_stats.loc[name, 'Kickoff Boosts'] += player['stats']['kickoffStats']['numTimeBoost']
            except: pass
            try: temp_player_stats.loc[name, 'Demos Inflicted'] += [x['attackerId']['id'] for x in stats['gameMetadata']['demos']].count(player['id']['id'])
            except: pass
            try: temp_player_stats.loc[name, 'Demos Taken'] += [x['victimId']['id'] for x in stats['gameMetadata']['demos']].count(player['id']['id'])
            except: pass
            try: temp_player_stats.loc[name, 'Clears'] += player['stats']['hitCounts']['totalClears']
            except: pass
            
            if str(player['id']['id']) in [x['id'] for x in stats['teams'][0]['playerIds']]:
                for column in temp_player_stats.columns:
                    team1_stats[column] += temp_player_stats.loc[name, column]
                team1_players.append(name)
            elif str(player['id']['id']) in [x['id'] for x in stats['teams'][1]['playerIds']]:
                for column in temp_player_stats.columns:
                    team2_stats[column] += temp_player_stats.loc[name, column]
                team2_players.append(name)
                    
        team_stats = team_stats.append(team1_stats)
        team_stats = team_stats.append(team2_stats)

        for player in temp_player_stats.index:
            if player in player_stats.index.values:
                player_stats.loc[player] = player_stats.loc[player].add(temp_player_stats.loc[player], fill_value=0)
            else:
                player_stats = player_stats.append(temp_player_stats.loc[player])
            
        for player in player_stats.index:
            player_stats.loc[player, 'Series Played'] = 1 # Add 1 series played for each player
            if (player_stats.loc[player, 'Games Won']/player_stats.loc[player, 'Games Played']) > 0.5:
                player_stats.loc[player, 'Series Won'] = 1
            
    team_stats = team_stats.groupby(team_stats.index).sum()
    team_stats.loc[:,'Series Played'] = team_stats.loc[:,'Series Played'] + 1
    team_stats.loc[:,'Games Played'] = team_stats.loc[:,'Games Played']/3
    team_stats.loc[:,'Games Won'] = team_stats.loc[:,'Games Won']/3
    for team in team_stats.index:
        if (team_stats.loc[team, 'Games Won']/team_stats.loc[team, 'Games Played']) > 0.5:
            team_stats.loc[team, 'Series Won'] = 1
    
    team_stats = team_stats.drop(columns = 'id')
        
    return(player_stats, team_stats)

def rlpc_replay_analysis():
    # Get player names, teams, leagues, and IDs in a dataframe for reference
    check_players() # Ensure that players database is up to date
    download_ids() # Ensure that all IDs are up to date
    players = select("players").set_index('Username')
    players = players.fillna(value=0)
    replays = get_rlpc_replays()
    #team_stats = select("team_stats")
    all_stats = pd.DataFrame(columns = list(players.columns[8:]))
    all_stats.index = all_stats.index.rename('Username')
    fantasy_players = select('fantasy_players').set_index('username')
    
    counter = 1
    failed = []

    for series in list(replays): # Repeats this for every series downloaded
        print(f'Analyzing series {counter} of {len(list(replays))} ({round(((counter-1)/len(list(replays)))*100)}%)')
        counter += 1
    
        try: indiv_stats, group_stats = get_series_stats(replays[series], players.reset_index())
        except:
            failed.append(series)
            continue
        
        all_stats = all_stats.append(indiv_stats)
        try: 
            league = find_league(group_stats.index[0], players.reset_index())
        except: 
            failed.append(series)
            continue

        # Upload team stats #
        # for team in group_stats.index:
        #     if team not in team_stats['Team'].values: # If there's not already a row for this team
        #         command = '''insert into team_stats ("League", "Team")'''
        #         values = f'''values ('{league}', '{team}')'''
        #         engine.execute(f'{command} {values}')
        #     for col in group_stats.columns:
        #         try: current_value = team_stats.loc[team_stats['Team']==team, col].values[0]
        #         except: current_value = 0
        #         engine.execute(f"""update team_stats set "{col}" = {group_stats.loc[team, col] + current_value} where "Team" = '{team}'""")
                
        # Upload player stats
        for player in indiv_stats.index:
            for col in indiv_stats.columns:
                try: engine.execute(f"""update players set "{col}" = coalesce("{col}", 0) + {indiv_stats.loc[player, col]} where "Username" = '{player}'""")
                except: continue # Temporary solution for if a player isn't on the sheet

    # Calculate fantasy points for each player
    all_stats = all_stats.groupby(all_stats.index).sum()
    all_stats['Fantasy Points'] = all_stats.apply(lambda row: fantasy_formula(row), axis=1)
    all_stats['Old Points'] = players['Fantasy Points']
    all_stats['New Points'] = all_stats['Old Points'] + all_stats['Fantasy Points']
    all_stats['League'] = players['League']
    
    # Add fantasy points to accounts
    for player in all_stats.index:
        try:
            for user in fantasy_players.index:
                if player in fantasy_players.loc[user, 'players']:
                    slot = fantasy_players.loc[user, 'players'].index(player) + 1
                    engine.execute(f"""update fantasy_players set points[{slot}] = points[{slot}] + {all_stats.loc[player, 'Fantasy Points']} where "username" = '{user}'""")
                    engine.execute(f"""update fantasy_players set "total_points" = coalesce("total_points", 0) + {all_stats.loc[player, 'Fantasy Points']} where "username" = '{user}'""")
                engine.execute(f"""update players set "Fantasy Points" = {all_stats.loc[player, "New Points"]} where "Username" = '{player}'""")
        except:
            failed.append(player)
        
    return all_stats, failed
            
def idk(all_stats):
    for player in all_stats.index:
        engine.execute(f"""update players set "Fantasy Points" = coalesce("Fantasy Points", 0) + {all_stats.loc[player, 'Fantasy Points']} where "Username" = '{player}'""")