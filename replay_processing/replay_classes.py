import logging
from abc import ABC, abstractmethod
from time import sleep
from typing import List

import numpy as np
import pandas as pd
import os
import requests

from errors.replay_errors import *
from rlpc.players import Identifier, PlayersHandler
from tools.mongo import Session, teamIds
from settings import valid_stats

try:
    from passwords import BALLCHASING_TOKEN
except:
    from dotenv import load_dotenv
    load_dotenv(f'{os.getcwd()}\.env')
    BALLCHASING_TOKEN = os.getenv("BALLCHASING_TOKEN")


def id_player(player: dict, identifier: Identifier):
    name = identifier.identify(player['id']['id'])
    if name == None:
        name = identifier.identify(player['name'])
        if name == None:
            name = identifier.tracker_identify(player['name'])
            if name == None:
                name = player['name']

    return name


class Replay(ABC):
    @abstractmethod
    def __init__(self, file_path: str, session: Session, playersHandler: PlayersHandler, identifier: Identifier):
        self.session = session
        self.playersHandler = playersHandler
        self.identifier = identifier
        self.path = file_path
        self.failed = False

    @abstractmethod
    def process(self) -> dict:
        pass

    @abstractmethod
    def get_teams(self) -> List[str]:
        pass

    @abstractmethod
    def get_players(self) -> List[str]:
        pass

    @abstractmethod
    def convert(self) -> pd.DataFrame:
        pass


class BallchasingReplay(Replay):
    def __init__(self, file_path: str, session: Session, playersHandler: PlayersHandler, identifier: Identifier):
        super().__init__(file_path, session, playersHandler, identifier)
        self.token = BALLCHASING_TOKEN
        self.uploaded = False
        self.processed = False
        try:
            self.upload()
        except requests.exceptions.ConnectionError:
            print("REPLAY FAILED (Host Connection Error): " + file_path)

    def upload(self) -> str:
        """Uploads a replay to the season 15 replays group on ballchasing.com

        Returns:
            str: replay ID to get the replay from ballchasing
        """

        group = "rlpc-season-15-replays-hpgwi3tqrc"
        upload_url = f"https://ballchasing.com/api/v2/upload?visibility=public&?group={group}"

        files = {'file': open(self.path, 'rb')}
        
        r = requests.post(upload_url, headers={'Authorization': self.token}, files=files)
        r_json = r.json()

        files['file'].close()

        if r.status_code == 201:    # replay successfully created, return it's id
            self.uploaded = True
            self.replay_id = r.json()['id']
            r.close()
            return r_json['id']
        elif r.status_code == 409:  # duplicate replay, return existing replay id
            self.uploaded = True
            self.replay_id = r_json['id']
            r.close()
            return r_json['id']
        elif r.status_code == 429:  # rate limit, wait 2 seconds and try again
            sleep(2)
            r.close()
            return self.upload()
        else:                       # raise an error for other status codes (50x, ...)
            r.raise_for_status()
    
    def process(self) -> dict:
        """Gets the ballchasing.com stats of a replay file, first uploading it and then retreiving the stats via the api

        Raises:
            ReplayFailedError: Ballchasing was unable to process the replay

        Returns:
            dict: Json with all the ballchasing.com data for the given replay
        """
        if not self.uploaded:
            self.replay_id = self.upload()

        replay_url = f"https://ballchasing.com/api/replays/{self.replay_id}"
        try:
            r = requests.get(replay_url, headers={'Authorization': self.token})
        except requests.exceptions.ConnectionError:
            raise ReplayFailedError(self.path)
        r_json = r.json()

        if r.status_code == 429:            # Rate limit, wait 2 seconds and try again     
            sleep(2)
            return self.process()
        elif r_json['status'] == 'ok':  
            r.close()         # Success, return stats json
            self.stats = r_json
            self.processed = True
            return r_json
        elif r_json['status'] == 'pending':      # Replay not processed yet, wait 5 seconds and try again
            sleep(5)
            r.close()
            return self.process()
        elif r_json['status'] == 'failed':       # Replay could not be processed
            self.failed = True
            r.close()
            raise ReplayFailedError(self.path)

    def get_teams(self) -> List[str]:
        """Gets an ordered list of the two teams' names

        Returns:
            List[str]: The two teams in the replay
        """
        choices = self.path.split('/')[-3].split(' - ')
        self._teams = choices
        return choices 
    
    def get_players(self) -> List[str]:
        """Gets a list of all the valid (non-sub) players

        Returns:
            List[str]: list of all balid players in the replay.
        """
        try:
            return self.data.index
        except AttributeError:
            return self.convert().index
            
    @property
    def teams(self):
        try:
            return self._teams
        except AttributeError:
            return self.get_teams()
    
    @property
    def players(self):
        try:
            return self.players
        except AttributeError:
            return self.get_players()

    def convert(self) -> pd.DataFrame:
        """Converts a replay's stats dict into a dataframe with only the stats relevant to RLPC

        Returns:
            pd.DataFrame: Dataframe with player names as indices and one stat it each column
        """
        stats = self.stats
        player_stats = pd.DataFrame(columns=["Username", *valid_stats])
        # teams = self.teams
        players = []
        unknown = []
        winner = "blue" if stats['blue']['stats']['core']['goals'] > stats['blue']['stats']['core']['goals_against'] else 'orange'
        
        for player in stats['blue']['players']:
            if player['end_time'] - player['start_time'] < 250: # Ensure only players who played most of the game will be included
                continue
            else:
                players.append(player)
        for player in stats['orange']['players']:
            if player['end_time'] - player['start_time'] < 250: # Ensure only players who played most of the game will be included
                continue
            else:
                players.append(player)

        for player in players:
            name = id_player(player, self.identifier)
            discord_id = ""
                
            # Handle unknown players
            try:
                doc = self.session.all_players.find_one({'username': name})
                discord_id = doc['_id']
            except: 
                # Player isn't in database at all
                print("PLAYER FAILED: " + name)
                unknown.append(name)
                discord_id = name

            # Add player's stats
            player_stats = player_stats.append(pd.Series(name=discord_id, dtype=object)).fillna(0)
            player_stats.loc[discord_id, 'Username'] = name
            player_stats.loc[discord_id, 'Games Played'] += 1
            if player['id']['id'] in [x['id']['id'] for x in stats[winner]['players']]:
                # Add 1 game won only if they won
                player_stats.loc[discord_id, 'Games Won'] += 1

            player_stats.loc[discord_id, 'MVPs'] += player['stats']['core']['mvp']
            player_stats.loc[discord_id, 'Goals'] += player['stats']['core']['goals']
            player_stats.loc[discord_id, 'Assists'] += player['stats']['core']['assists']
            player_stats.loc[discord_id, 'Saves'] += player['stats']['core']['saves']
            player_stats.loc[discord_id, 'Shots'] += player['stats']['core']['shots']
            player_stats.loc[discord_id, 'Goals Against'] += player['stats']['core']['goals_against']
            player_stats.loc[discord_id, 'Shots Against'] += player['stats']['core']['shots_against']
            player_stats.loc[discord_id, 'Demos Inflicted'] += player['stats']['demo']['inflicted']
            player_stats.loc[discord_id, 'Demos Taken'] += player['stats']['demo']['taken']

            player_stats.loc[discord_id, 'Boost Used'] += player['stats']['boost']['amount_collected']
            player_stats.loc[discord_id, 'Wasted Collection'] += player['stats']['boost']['amount_overfill']
            player_stats.loc[discord_id, 'Wasted Usage'] += player['stats']['boost']['amount_used_while_supersonic']
            player_stats.loc[discord_id, '# Small Boosts'] += player['stats']['boost']['count_collected_small']
            player_stats.loc[discord_id, '# Large Boosts'] += player['stats']['boost']['count_collected_big']
            player_stats.loc[discord_id, '# Boost Steals'] += player['stats']['boost']['count_stolen_big']
            player_stats.loc[discord_id, 'Time Empty'] += player['stats']['boost']['time_boost_0_25']

            player_stats.loc[discord_id, 'Time Slow'] += player['stats']['movement']['time_slow_speed']
            player_stats.loc[discord_id, 'Time Boost'] += player['stats']['movement']['time_boost_speed']
            player_stats.loc[discord_id, 'Time Supersonic'] += player['stats']['movement']['time_supersonic_speed']
            player_stats.loc[discord_id, 'Time Powerslide'] += player['stats']['movement']['time_powerslide']
            player_stats.loc[discord_id, 'Time Ground'] += player['stats']['movement']['time_ground']
            player_stats.loc[discord_id, 'Time Low Air'] += player['stats']['movement']['time_low_air']
            player_stats.loc[discord_id, 'Time High Air'] += player['stats']['movement']['time_high_air']

            player_stats.loc[discord_id, 'Time Behind Ball'] += player['stats']['positioning']['time_behind_ball']
            player_stats.loc[discord_id, 'Time Infront Ball'] += player['stats']['positioning']['time_infront_ball']
            player_stats.loc[discord_id, 'Time Defensive Half'] += player['stats']['positioning']['time_defensive_half']
            player_stats.loc[discord_id, 'Time Offensive Half'] += player['stats']['positioning']['time_offensive_half']
            player_stats.loc[discord_id, 'Time Most Back'] += player['stats']['positioning']['time_most_back']
            player_stats.loc[discord_id, 'Time Most Forward'] += player['stats']['positioning']['time_most_forward']
            player_stats.loc[discord_id, 'Time Closest'] += player['stats']['positioning']['time_closest_to_ball']
            player_stats.loc[discord_id, 'Time Furthest'] += player['stats']['positioning']['time_farthest_from_ball']
            try:
                player_stats.loc[discord_id, 'Conceded When Last'] += player['stats']['positioning']['goals_against_while_last_defender']
            except:
                pass

        self._player_stats = player_stats
        self.unknown = unknown

        return player_stats, unknown

    @property
    def player_stats(self) -> pd.DataFrame:
        try:
            return self._player_stats
        except AttributeError:
            self.process()
            return self.convert()

class CarballReplay(Replay):
    def __init__(self, file_path: str, session: Session, playersHandler: PlayersHandler, identifier: Identifier):
        super().__init__(file_path, session, playersHandler, identifier)
        self.stats = self.process()

    def process(self) -> dict:
        """Processes the replay with carball to get stats and frame data

        Returns:
            dict: Large json style dict with game stats and metadata
        """
        try:
            analysis_manager = carball.analyze_replay_file(
                self.path, logging_level=logging.CRITICAL)

            self.frames = analysis_manager.get_data_frame().fillna(value=0)
            stats = dict(analysis_manager.get_json_data())

            return stats
        
        except:
            self.failed = True
            return None

    def get_teams(self) -> List[str]:
        """Gets an ordered list of the two teams' names

        Returns:
            List[str]: The two teams in the replay
        """
        choices = self.path.split('/')[-3].split(' - ')
        self._teams = choices
        return choices 

    def get_players(self) -> List[str]:
        """Gets a list of all the valid (non-sub) players

        Returns:
            List[str]: list of all balid players in the replay.
        """
        try:
            return self.data.index
        except AttributeError:
            return self.convert().index

    @property
    def teams(self):
        try:
            return self._teams
        except AttributeError:
            return self.get_teams()
    
    @property
    def players(self):
        try:
            return self._players
        except AttributeError:
            return self.get_players()

    def convert(self) -> pd.DataFrame:
        """Converts a replay's stats dict into a dataframe with only the stats relevant to RLPC

        Returns:
            pd.DataFrame: Dataframe with player names as indices and one stat it each column
        """
        stats = self.stats
        player_stats = pd.DataFrame(columns=valid_stats)
        teams = self.teams
        players = []
        winner = 0 if stats['teams'][1]['score'] < stats['teams'][0]['score'] else 1

        for player in stats['players']:
            if player['timeInGame'] < 250 or player['firstFrameInGame'] > 100: # In case they joined mid-game, these are pretty generous though
                continue
            else:
                players.append(player)

        for player in players:
            name = id_player(player, self.identifier)

            # Handle subs
            try:
                doc = self.session.players.find_one({'username': name})
                if doc['info']['team'] not in [teamIds[teams[0]], teamIds[teams[1]]]:
                    # Player is on a different team (sub)
                    continue
            except:
                # Player isn't in database at all
                print("PLAYER FAILED: " + name)
                continue
            
            # Add player's stats
            player_stats = player_stats.append(pd.Series(name=name, dtype=object)).fillna(0)
            player_stats.loc[name, 'Games Played'] += 1
            if str(player['id']['id']) in [x['id'] for x in stats['teams'][winner]['playerIds']]:
                # Add 1 game won only if they won
                player_stats.loc[name, 'Games Won'] += 1
            try:
                player_stats.loc[name, 'Goals'] += player['goals']
            except:
                pass
            try:
                player_stats.loc[name, 'Assists'] += player['assists']
            except:
                pass
            try:
                player_stats.loc[name, 'Saves'] += player['saves']
            except:
                pass
            try:
                player_stats.loc[name, 'Shots'] += player['shots']
            except:
                pass
            try:
                player_stats.loc[name, 'Dribbles'] += player['stats']['hitCounts']['totalDribbles']
            except:
                pass
            try:
                player_stats.loc[name, 'Passes'] += player['stats']['hitCounts']['totalPasses']
            except:
                pass
            try:
                player_stats.loc[name, 'Aerials'] += player['stats']['hitCounts']['totalAerials']
            except:
                pass
            try:
                player_stats.loc[name, 'Hits'] += player['stats']['hitCounts']['totalHits']
            except:
                pass
            try:
                player_stats.loc[name, 'Boost Used'] += player['stats']['boost']['boostUsage']
            except:
                pass
            try:
                player_stats.loc[name, 'Wasted Collection'] += player['stats']['boost']['wastedCollection']
            except:
                pass
            try:
                player_stats.loc[name, 'Wasted Usage'] += player['stats']['boost']['wastedUsage']
            except:
                pass
            try:
                player_stats.loc[name, '# Small Boosts'] += player['stats']['boost']['numSmallBoosts']
            except:
                pass
            try:
                player_stats.loc[name, '# Large Boosts'] += player['stats']['boost']['numLargeBoosts']
            except:
                pass
            try:
                player_stats.loc[name, '# Boost Steals'] += player['stats']['boost']['numStolenBoosts']
            except:
                pass
            try:
                player_stats.loc[name, 'Wasted Big'] += player['stats']['boost']['wastedBig']
            except:
                pass
            try:
                player_stats.loc[name, 'Wasted Small'] += player['stats']['boost']['wastedSmall']
            except:
                pass
            try:
                player_stats.loc[name, 'Time Slow'] += player['stats']['speed']['timeAtSlowSpeed']
            except:
                pass
            try:
                player_stats.loc[name, 'Time Boost'] += player['stats']['speed']['timeAtBoostSpeed']
            except:
                pass
            try:
                player_stats.loc[name, 'Time Supersonic'] += player['stats']['speed']['timeAtSuperSonic']
            except:
                pass
            try:
                player_stats.loc[name, 'Turnovers Lost'] += player['stats']['possession']['turnovers']
            except:
                pass
            try:
                player_stats.loc[name, 'Defensive Turnovers Lost'] += (
                    player['stats']['possession']['turnovers'] - player['stats']['possession']['turnoversOnTheirHalf'])
            except:
                pass
            try:
                player_stats.loc[name, 'Offensive Turnovers Lost'] += player['stats']['possession']['turnoversOnTheirHalf']
            except:
                pass
            try:
                player_stats.loc[name, 'Turnovers Won'] += player['stats']['possession']['wonTurnovers']
            except:
                pass
            try:
                player_stats.loc[name, 'Kickoffs'] += player['stats']['kickoffStats']['totalKickoffs']
            except:
                pass
            try:
                player_stats.loc[name, 'First Touches'] += player['stats']['kickoffStats']['numTimeFirstTouch']
            except:
                pass
            try:
                player_stats.loc[name, 'Kickoff Cheats'] += player['stats']['kickoffStats']['numTimeCheat']
            except:
                pass
            try:
                player_stats.loc[name, 'Kickoff Boosts'] += player['stats']['kickoffStats']['numTimeBoost']
            except:
                pass
            try:
                player_stats.loc[name, 'Demos Inflicted'] += [x['attackerId']['id']
                                                            for x in stats['gameMetadata']['demos']].count(player['id']['id'])
            except:
                pass
            try:
                player_stats.loc[name, 'Demos Taken'] += [x['victimId']['id']
                                                        for x in stats['gameMetadata']['demos']].count(player['id']['id'])
            except:
                pass
            try:
                player_stats.loc[name, 'Clears'] += player['stats']['hitCounts']['totalClears']
            except:
                pass
            try:
                player_stats.loc[name, 'Flicks'] += player['stats']['ballCarries']['totalFlicks']
            except:
                pass

        return player_stats

    def normalise_frames(self, inplace: bool = False) -> pd.DataFrame:
        """
        A function to convert frame-by-frame values into numbers between -1 and 1

        Parameters
        ----------
        inplace : bool, optional
            Whether or not to modify the original dataframe or a copy. The default is False.

        Returns
        -------
        df : pd.DataFrame
            Normalised Dataframe.

        """
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

        df = self.frames.copy()
        for column, normalisation_factor in NORMALISATION_FACTORS.items():
            df.loc[:, (slice(None), column)] /= normalisation_factor

        if inplace:
            self._frames = df

        return df
