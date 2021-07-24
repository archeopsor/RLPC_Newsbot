import os
import shutil
import time
from typing import Union, List
import pandas as pd
import numpy as np
import logging
from zipfile import ZipFile
from datetime import datetime, timedelta
import pytz

import carball

from tools.mongo import Session, teamIds, findCategory
from tools.sheet import Sheet

from rlpc.players import Players, Identifier
from rlpc.elo import EloHandler

from settings import sheet_p4, valid_stats, gdstats_sheet

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


class Retreiver:
    def __init__(self):
        pass

    @staticmethod
    def download(update_elo=True):
        """
        Downloads yesterday's replays from the rlpcgamelogs website

        Returns
        -------
        None.

        """
        from selenium import webdriver

        # To prevent download dialog
        profile = webdriver.FirefoxProfile()
        profile.set_preference(
            'browser.download.folderList', 2)  # custom location
        profile.set_preference(
            'browser.download.manager.showWhenStarting', False)
        profile.set_preference('browser.download.dir', '/tmp')
        profile.set_preference('browser.helperApps.neverAsk.saveToDisk',
                               'application/octet-stream, application/zip')

        browser = webdriver.Firefox(
            profile, executable_path=r'C:\Users\Simi\Documents\geckodriver.exe')
        browser.get("https://rlpcgamelogs.com/")

        browser.find_element_by_xpath(
            "/html/body/app-root/div/app-main/div/div[1]/div[4]").click()  # Click "Status" tab
        time.sleep(3)
        browser.find_element_by_xpath(
            "/html/body/app-root/div/app-main/div/div[2]/div[1]").click()  # Click "Logs" tab
        time.sleep(3)
        browser.find_element_by_xpath(
            "/html/body/app-root/div/app-main/div/app-logs-status/div/div[2]/p-dropdown/div/label").click()
        time.sleep(3)

        dates = browser.find_elements_by_xpath(
            '/html/body/app-root/div/app-main/div/app-logs-status/div/div[2]/p-dropdown[1]/div/div[4]/div/ul/li')
        target_date = datetime.now(tz=pytz.timezone(
            "US/Eastern")) - timedelta(days=1)
        for date in dates[::-1]:
            # Click the date for yesterday
            if date.text == target_date.strftime('%m/%d/%Y'):
                date.click()
                break
        time.sleep(3)

        browser.find_element_by_xpath(
            '/html/body/app-root/div/app-main/div/app-logs-status/div/div[2]/p-dropdown[2]/div/label').click()  # Click "League" tab
        time.sleep(3)
        leagues = browser.find_elements_by_xpath(
            '/html/body/app-root/div/app-main/div/app-logs-status/div/div[2]/p-dropdown[2]/div/div[4]/div/ul/li')

        scores = ""

        # Does the below for every league that shows up on the website
        for i in range(1, len(leagues)+1):
            browser.find_element_by_xpath(
                '/html/body/app-root/div/app-main/div/app-logs-status/div/div[2]/p-dropdown[2]/div/label').click()  # Click "League" tab
            time.sleep(3)
            try:
                # Click appropriate league on drop-down list
                browser.find_element_by_xpath(
                    f'/html/body/app-root/div/app-main/div/app-logs-status/div/div[2]/p-dropdown[2]/div/div[4]/div/ul/li[{i}]').click()
            except:
                browser.find_element_by_xpath(
                    '/html/body/app-root/div/app-main/div/app-logs-status/div/div[2]/p-dropdown[2]/div/label').click()  # Click "League" tab
                # Click appropriate league on drop-down list
                browser.find_element_by_xpath(
                    f'/html/body/app-root/div/app-main/div/app-logs-status/div/div[2]/p-dropdown[2]/div/div[4]/div/ul/li[{i}]').click()

            table = browser.find_elements_by_xpath(
                '/html/body/app-root/div/app-main/div/app-logs-status/div/div[3]/table/tbody/tr')
            for row in table:
                if row.text == 'Team Team Deadline Passed':  # Logs not submitted table
                    continue

                winner = row.find_element_by_xpath('td[1]').text

                if winner == 'Winning Team':  # First row of the table
                    continue

                winnerScore = row.find_element_by_xpath('td[2]').text
                loser = row.find_element_by_xpath('td[3]').text
                try:
                    loserScore = row.find_element_by_xpath('td[4]').text
                except:
                    continue

                if winnerScore == 'FF' or loserScore == 'FF':
                    continue

                try:
                    row.find_element_by_xpath(
                        'td[7]/div').click()  # Download logs
                except:
                    pass  # If no logs are available

                score = f'{winner} {winnerScore}-{loserScore} {loser}'
                if scores != '':  # Add new line if this isn't the first score being added
                    scores += '\n'
                scores += score

            time.sleep(13)

        if update_elo:
            EloHandler().autoparse(scores)

        return browser.quit()

    @staticmethod
    def get_own_replays(path='C:/Users/Simi/Documents/My Games/Rocket League/TAGame/Demos') -> list:
        """
        Gets a list of replays from the file at the given path

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

    @staticmethod
    def get_downloaded_replays(path: str = 'C:/Users/Simi/Downloads', target: str = "./replay_processing/Replay_Files", max_age: int = 1) -> list:
        """
        Moves replay zip files downloaded from rlpcgamelogs.com to the target folder, and unfolds them in the process. Returns a list of retreived replays.

        Parameters
        ----------
        path : str, optional
            Where the downloaded replays are located. The default is 'C:/Users/Simi/Downloads'.
        target : str, optional
            Where to move unfolded replays. The default is "C:/Users/Simi/Desktop/Replay Files/".
        max_age : int, optional
            Maximum age, in days, of files to get. The default is 1.

        Returns
        -------
        files : list
            List of replay file paths unfolded and retreived

        """
        files = {}
        for download in os.listdir(path):
            new = os.path.getmtime(
                f"{path}/{download}") > time.time()-(max_age*80000)
            if download.endswith('.zip') and new:
                replays = []
                teams = download.split(" - ")[0].split(" vs. ")
                name = f"{teams[0]} - {teams[1]}"
                with ZipFile(f"{path}/{download}", 'r') as zip_ref:
                    # Extract files to new folder
                    zip_ref.extractall(f"{target}/{name}")
                for folder in os.listdir(f"{target}/{name}"):
                    filename = os.listdir(f"{target}/{name}/{folder}")[0]
                    replays.append(f"{target}/{name}/{folder}/{filename}")
                files[name] = replays
                
                filepath = os.path.join(path, download).replace('/', '\\')
                #os.remove(filepath)
                # shutil.rmtree(filepath)

        return files

    @staticmethod
    def clean_folder(path: str = './replay_processing/Replay_Files'):
        for file in os.listdir(path):
            filepath = os.path.join(path, file)
            try:
                shutil.rmtree(filepath)
            except:
                os.remove(filepath)


class Replay:
    def __init__(self, path: str, isPerGoal: bool = False, session: Session = None, p4sheet: Sheet = None, playersHandler: Players = None, identifier: Identifier = None):
        self.path = path.replace('\\', '/')

        if not session:
            self.session = Session()
        else:
            self.session = session
        if not p4sheet:
            self.p4sheet = Sheet(sheet_p4)
        else:
            self.p4sheet = p4sheet
        if not playersHandler:
            self.playersHandler = Players(self.session, self.p4sheet)
        else:
            self.playersHandler = playersHandler
        if not identifier:
            self.identifier = Identifier(self.session, self.p4sheet)
        else:
            self.identifier = identifier

        self.failed = False
        try:
            self._stats, self._frames = self.process(isPerGoal)
        except:
            self.failed = True

    def process(self, isPerGoal: bool = False) -> Union[dict, pd.DataFrame]:
        """
        Processes the replay with carball to get stats and frame data

        Returns
        -------
        stats : dict
            Large nested dict with all sorts of stats and metadata.
        frames : pd.DataFrame
            Dataframe with data for each actor every frame.

        """
        try:
            analysis_manager = carball.analyze_replay_file(
                self.path, logging_level=logging.CRITICAL)

            frames = analysis_manager.get_data_frame().fillna(value=0)
            stats = dict(analysis_manager.get_json_data())

            return stats, frames

        except:
            self.failed = True
            return None

    def get_teams(self) -> Union[str, str]:
        """
        Returns a verified and ordered list of the two teams' names

        Returns
        -------
        teams : list
            The two teams in this replay.

        """
        stats = self._stats
        choices = self.path.split('/')[-3].split(' - ')
        return choices # TODO: Fix ids not working properly

        teams = []
        teams.append([x['id'] for x in stats['teams'][0]['playerIds']])
        teams.append([x['id'] for x in stats['teams'][1]['playerIds']])
        team1 = self.identifier.find_team(teams[0], id_players=True, choices=choices)
        team2 = self.identifier.find_team(teams[1], id_players=True, choices=choices)

        return [team1, team2]

    def get_players(self):
        """
        Gets a list of all the valid (non-sub) players

        Returns
        -------
        players : list
            List of all valid players in the replay.

        """
        try:
            teams = self._teams
        except AttributeError:
            self._teams = self.get_teams()
            teams = self._teams
        stats = self._stats
        players: list = []

        for player in stats['players']:
            if player['timeInGame'] < 150 or player['firstFrameInGame'] > 100: # In case they joined mid-game, these are pretty generous though
                continue

            name = self.identifier.identify(player['id']['id'])
            if name == None:
                name = self.identifier.identify(player['name'])
                if name == None:
                    name = self.identifier.tracker_identify(player['name'])
                    if name == None:
                        name = player['name']

            # Handle subs
            try:
                doc = self.session.players.find_one({'username': name})
                if doc['info']['team'] != teamIds[teams[0]] and doc['info']['team'] != teamIds[teams[1]]:
                    continue
                # if name not in self.session.teams.find_one({"_id": doc['info']['team']})['players']: TODO: Fix this by adding players to teams in mongo
                #     # This should only be true if the player is not actually on the team, ie a sub or call down
                #     continue
            except:
                print("PLAYER FAILED: " + name)
                continue

            if name not in players:
                players.append(name)

        return players

    @property
    def stats(self):
        return self._stats

    @property
    def frames(self):
        return self._frames

    @property
    def players(self):
        self._players = self.get_players()
        return self._players

    @property
    def teams(self):
        self._teams = self.get_teams()
        return self._teams

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

        df = self._frames.copy()
        for column, normalisation_factor in NORMALISATION_FACTORS.items():
            df.loc[:, (slice(None), column)] /= normalisation_factor

        if inplace:
            self._frames = df

        return df


class Series:
    def __init__(self, session: Session, identifier: Identifier, length: int, replays: List[Replay]) -> None:
        self.failed = []
        self.session = session
        self.identifier = identifier
        self.length = 5
        self.replays = replays
        self.players = []
        try:
            self.teams = self.replays[1].teams
        except:
            self.teams = self.replays[-1].teams  # Just in case replay 1 fails

    def get_stats(self) -> pd.DataFrame:
        """Gets full-series-stats for a set of 3-7 replays

        Returns:
            pd.DataFrame: Dataframe with usernames as indexes, containing stats aggregated from each replay
        """
        player_stats = pd.DataFrame(columns=valid_stats)

        for replay in self.replays:
            if replay.failed:
                print(f"REPLAY FAILED: {replay.path}")
                self.failed.append(replay.path)
                self.length -= 1  # Not sure if I should keep this in
                continue
            else:
                stats = replay.stats

            winner = 0
            if stats['teams'][1]['score'] > stats['teams'][0]['score']:
                winner = 1

            # Get player's name
            for player in stats['players']:
                name = self.identifier.identify(player['id']['id'])
                if name == None:
                    name = self.identifier.identify(player['name'])
                    if name == None:
                        name = self.identifier.tracker_identify(player['name'])
                        if name == None:
                            name = player['name']

                # Don't include subs
                if name not in replay.players:
                    continue

                if name not in player_stats.index.values:
                    # Create an empty row for the player's stats if it isn't already there
                    player_stats = player_stats.append(
                        pd.Series(name=name, dtype=object)).fillna(0)

                # Add stats to player_stats
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
                    player_stats.loc[name,
                                    'Dribbles'] += player['stats']['hitCounts']['totalDribbles']
                except:
                    pass
                try:
                    player_stats.loc[name,
                                    'Passes'] += player['stats']['hitCounts']['totalPasses']
                except:
                    pass
                try:
                    player_stats.loc[name,
                                    'Aerials'] += player['stats']['hitCounts']['totalAerials']
                except:
                    pass
                try:
                    player_stats.loc[name,
                                    'Hits'] += player['stats']['hitCounts']['totalHits']
                except:
                    pass
                try:
                    player_stats.loc[name,
                                    'Boost Used'] += player['stats']['boost']['boostUsage']
                except:
                    pass
                try:
                    player_stats.loc[name,
                                    'Wasted Collection'] += player['stats']['boost']['wastedCollection']
                except:
                    pass
                try:
                    player_stats.loc[name,
                                    'Wasted Usage'] += player['stats']['boost']['wastedUsage']
                except:
                    pass
                try:
                    player_stats.loc[name,
                                    '# Small Boosts'] += player['stats']['boost']['numSmallBoosts']
                except:
                    pass
                try:
                    player_stats.loc[name,
                                    '# Large Boosts'] += player['stats']['boost']['numLargeBoosts']
                except:
                    pass
                try:
                    player_stats.loc[name,
                                    '# Boost Steals'] += player['stats']['boost']['numStolenBoosts']
                except:
                    pass
                try:
                    player_stats.loc[name,
                                    'Wasted Big'] += player['stats']['boost']['wastedBig']
                except:
                    pass
                try:
                    player_stats.loc[name,
                                    'Wasted Small'] += player['stats']['boost']['wastedSmall']
                except:
                    pass
                try:
                    player_stats.loc[name,
                                    'Time Slow'] += player['stats']['speed']['timeAtSlowSpeed']
                except:
                    pass
                try:
                    player_stats.loc[name,
                                    'Time Boost'] += player['stats']['speed']['timeAtBoostSpeed']
                except:
                    pass
                try:
                    player_stats.loc[name,
                                    'Time Supersonic'] += player['stats']['speed']['timeAtSuperSonic']
                except:
                    pass
                try:
                    player_stats.loc[name,
                                    'Turnovers Lost'] += player['stats']['possession']['turnovers']
                except:
                    pass
                try:
                    player_stats.loc[name, 'Defensive Turnovers Lost'] += (
                        player['stats']['possession']['turnovers'] - player['stats']['possession']['turnoversOnTheirHalf'])
                except:
                    pass
                try:
                    player_stats.loc[name,
                                    'Offensive Turnovers Lost'] += player['stats']['possession']['turnoversOnTheirHalf']
                except:
                    pass
                try:
                    player_stats.loc[name,
                                    'Turnovers Won'] += player['stats']['possession']['wonTurnovers']
                except:
                    pass
                try:
                    player_stats.loc[name,
                                    'Kickoffs'] += player['stats']['kickoffStats']['totalKickoffs']
                except:
                    pass
                try:
                    player_stats.loc[name,
                                    'First Touches'] += player['stats']['kickoffStats']['numTimeFirstTouch']
                except:
                    pass
                try:
                    player_stats.loc[name,
                                    'Kickoff Cheats'] += player['stats']['kickoffStats']['numTimeCheat']
                except:
                    pass
                try:
                    player_stats.loc[name,
                                    'Kickoff Boosts'] += player['stats']['kickoffStats']['numTimeBoost']
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
                    player_stats.loc[name,
                                    'Clears'] += player['stats']['hitCounts']['totalClears']
                except:
                    pass
                try:
                    player_stats.loc[name,
                                    'Flicks'] += player['stats']['ballCarries']['totalFlicks']
                except:
                    pass

        # Add Series Played and Series Won stats
        for player in player_stats.index:
            player_stats.loc[player, 'Series Played'] = 1
            if (player_stats.loc[player, 'Games Won']/player_stats.loc[player, 'Games Played']) > 0.5:
                player_stats.loc[player, 'Series Won'] = 1

        return player_stats


class RLPCAnalysis:
    def __init__(self, session: Session = None, identifier: Identifier = None, p4sheet: Sheet = None, playersHandler: Players = None) -> None:
        if not session:
            self.session = Session()
        else:
            self.session = session
        if not p4sheet:
            self.p4sheet = Sheet(sheet_p4)
        else:
            self.p4sheet = p4sheet
        if not playersHandler:
            self.playersHandler = Players(self.session, self.p4sheet)
        else:
            self.playersHandler = playersHandler
        if not identifier:
            self.identifier = Identifier(self.session, self.p4sheet)
        else:
            self.identifier = identifier

        self.failed = []

    def checks(self):
        self.playersHandler.check_players()
        self.playersHandler.download_ids()

    def get_replays(self):
        replays = Retreiver.get_downloaded_replays()
        self.replays = replays
        return replays

    def analyze_replays(self):
        stats = pd.DataFrame(columns=valid_stats)
        counter = 1
        replays = self.get_replays()

        for series in list(replays):
            print(f'Analyzing series {counter} of {len(list(replays))} ({round(((counter-1)/len(list(replays)))*100)}%)')

            games = []
            for replay in replays[series]:
                games.append(Replay(replay, session=self.session, p4sheet=self.p4sheet, playersHandler=self.playersHandler, identifier=self.identifier))
            series_obj = Series(self.session, self.identifier, len(games), games)

            series_stats = series_obj.get_stats()
            failed = series_obj.failed

            stats = stats.append(series_stats)
            self.failed.append(failed)        

            # self.upload_game(series_obj)
            counter += 1         

        self.stats = stats
        return stats

    def upload_game(self, series: Series):
        # game_doc = self.session.structures['games'].copy()
        # game_doc['gameday'] = str(datetime.now(tz=pytz.timezone("US/Eastern")).date())
        # game_doc['league'] = self.identifier.find_league(series.teams[0])
        # game_doc['teams'].append({
        #     'name': series.teams[0]
        # })
        pass

    def upload_stats(self, stats: pd.DataFrame):
        if 'League' in stats.columns:
            stats = stats.drop(columns=['Fantasy Points', 'League'])

        for player in stats.index:
            update = {'$inc': {}}

            for col in stats.columns:
                category = findCategory(col)
                if type(stats.loc[player, col]) == np.int64:
                    datapoint = int(stats.loc[player, col])
                else:
                    datapoint = float(stats.loc[player, col])
                update['$inc'][f'stats.{category}.{col}'] = datapoint

            try:
                self.session.players.update_one(
                    {'username': player},
                    update
                )
            except:
                print("PLAYER STATS FAILED: "+player)
                continue

    def update_fantasy(self, stats: pd.DataFrame):
        if 'League' not in stats.columns:
            stats['Fantasy Points'] = stats.apply(lambda row: fantasy_formula(row), axis=1)
            stats['League'] = stats.apply(lambda row: self.identifier.find_league(self.identifier.find_team([row.name])), axis=1)
        fantasy = self.session.fantasy.find()
        while fantasy.alive:
            account = fantasy.next()
            for player in account['players']:
                username = self.session.players.find_one({'_id': player})['username']

                if username not in stats.index: # They didn't have stats for this gameday
                    continue

                points = int(stats.loc[username, 'Fantasy Points'])
                # index = next((i for (i, d) in enumerate(account['player_history']) if d["Player"] == player), None)
                # if index == None:
                #     continue
                self.session.fantasy.update_one(
                    {'_id': account['_id'], 'player_history.Player': player},
                    {'$inc': {'player_history.$.Points': points, 'points': points}}
                    )
        
        for player in stats.index:
            self.session.players.update_one(
                {'username': player},
                {'$inc': {'fantasy.fantasy_points': int(stats.loc[player, 'Fantasy Points'])}}
            )

    def log_data(self, stats: pd.DataFrame, range: str):
        if 'League' not in stats.columns:
            stats['Fantasy Points'] = stats.apply(lambda row: fantasy_formula(row), axis=1)
            stats['League'] = stats.apply(lambda row: self.identifier.find_league(self.identifier.find_team([row.name])), axis=1)

        Sheet(gdstats_sheet).push_df(range, stats.reset_index().fillna(value=0))

    def create_post(self, stats: pd.DataFrame):
        if 'League' not in stats.columns:
            stats['Fantasy Points'] = stats.apply(lambda row: fantasy_formula(row), axis=1)
            stats['League'] = stats.apply(lambda row: self.identifier.find_league(self.identifier.find_team([row.name])), axis=1)

        stats.sort_values(by="Fantasy Points", ascending=False, inplace=True)

        with open("post.txt", 'a') as file:
            file.write("Player Leaders:\n")
            leaders = stats.head(3).index
            file.write(f"1. {leaders[0]} - {stats.loc[leaders[0], 'Fantasy Points']}\n")
            file.write(f"2. {leaders[1]} - {stats.loc[leaders[1], 'Fantasy Points']}\n")
            file.write(f"3. {leaders[2]} - {stats.loc[leaders[2], 'Fantasy Points']}\n\n")

            try:
                leaders = stats[stats['League']=='Major'].head(3).index
                file.write("Major MVPs:\n")
                file.write(f"1. {leaders[0]} - {stats.loc[leaders[0], 'Fantasy Points']}\n")
                file.write(f"2. {leaders[1]} - {stats.loc[leaders[1], 'Fantasy Points']}\n")
                file.write(f"3. {leaders[2]} - {stats.loc[leaders[2], 'Fantasy Points']}\n\n")
            except IndexError:
                pass

            try:
                leaders = stats[stats['League']=='AAA'].head(3).index
                file.write("AAA MVPs:\n")
                file.write(f"1. {leaders[0]} - {stats.loc[leaders[0], 'Fantasy Points']}\n")
                file.write(f"2. {leaders[1]} - {stats.loc[leaders[1], 'Fantasy Points']}\n")
                file.write(f"3. {leaders[2]} - {stats.loc[leaders[2], 'Fantasy Points']}\n\n")
            except IndexError:
                pass

            try:
                leaders = stats[stats['League']=='AA'].head(3).index
                file.write("AA MVPs:\n")
                file.write(f"1. {leaders[0]} - {stats.loc[leaders[0], 'Fantasy Points']}\n")
                file.write(f"2. {leaders[1]} - {stats.loc[leaders[1], 'Fantasy Points']}\n")
                file.write(f"3. {leaders[2]} - {stats.loc[leaders[2], 'Fantasy Points']}\n\n")
            except IndexError:
                pass

            try:
                leaders = stats[stats['League']=='A'].head(3).index
                file.write("A MVPs:\n")
                file.write(f"1. {leaders[0]} - {stats.loc[leaders[0], 'Fantasy Points']}\n")
                file.write(f"2. {leaders[1]} - {stats.loc[leaders[1], 'Fantasy Points']}\n")
                file.write(f"3. {leaders[2]} - {stats.loc[leaders[2], 'Fantasy Points']}\n\n")
            except IndexError:
                pass

            try:
                leaders = stats[stats['League']=='Independent'].head(3).index
                file.write("Indy MVPs:\n")
                file.write(f"1. {leaders[0]} - {stats.loc[leaders[0], 'Fantasy Points']}\n")
                file.write(f"2. {leaders[1]} - {stats.loc[leaders[1], 'Fantasy Points']}\n")
                file.write(f"3. {leaders[2]} - {stats.loc[leaders[2], 'Fantasy Points']}\n\n")
            except IndexError:
                pass

            try:
                leaders = stats[stats['League']=='Maverick'].head(3).index
                file.write("Mav MVPs:\n")
                file.write(f"1. {leaders[0]} - {stats.loc[leaders[0], 'Fantasy Points']}\n")
                file.write(f"2. {leaders[1]} - {stats.loc[leaders[1], 'Fantasy Points']}\n")
                file.write(f"3. {leaders[2]} - {stats.loc[leaders[2], 'Fantasy Points']}")
            except IndexError:
                pass

    def main(self):
        print("Checks")
        self.checks()

        print("Getting replays")
        stats = self.analyze_replays()

        print("Logging data")
        self.log_data(stats, '7/22/21 Data!A2:Z')

        print("Uploading Stats")
        self.upload_stats(stats)

        print("Updating fantasy points")
        self.update_fantasy(stats)

        print("Creating post file")
        self.create_post(stats)

        print("FAILED: "+str(self.failed))



if __name__ == "__main__":
    Retreiver.download()
    RLPCAnalysis().main()