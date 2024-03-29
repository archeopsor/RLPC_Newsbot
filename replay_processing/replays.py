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
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.firefox_binary import FirefoxBinary
from selenium.webdriver.remote.remote_connection import LOGGER as seleniumLogger
from urllib3.connectionpool import log as urllibLogger
from webdriver_manager.firefox import GeckoDriverManager

from dotenv import load_dotenv
load_dotenv(f'{os.getcwd()}\.env')

# Allow imports when running script from within project dir
import sys
[sys.path.append(i) for i in ['.', '..']]

from errors.replay_errors import ReplayFailedError
from replay_classes import BallchasingReplay, CarballReplay, Replay

from tools.mongo import Session, teamIds, findCategory
from tools.sheet import Sheet

from rlpc.players import PlayersHandler, Identifier
from rlpc.elo import EloHandler
from rlpc.stats import StatsHandler, get_latest_gameday, dates, snakecase_stat

from settings import sheet_p4, valid_stats, gdstats_sheet, current_season

seleniumLogger.setLevel(logging.WARNING)
urllibLogger.setLevel(logging.WARNING)

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

        # To prevent download dialog
        # profile = webdriver.FirefoxProfile()


        options = Options()
        # options.profile = profile
        options.add_argument('-headless')

        options.set_preference(
            'browser.download.folderList', 2)  # custom location
        options.set_preference(
            'browser.download.manager.showWhenStarting', False)
        options.set_preference('browser.download.dir', f'{os.getcwd()}\\replay_processing\\Downloaded_Replays')
        options.set_preference('browser.helperApps.neverAsk.saveToDisk',
                            'application/octet-stream, application/zip')

        if os.environ.get('PROD') == "false": # Running on a machine with firefox downloaded

            browser = webdriver.Firefox(executable_path=GeckoDriverManager().install(), options=options)

        else: # Running on a heroku server using firefox buildpack

            options.add_argument("-remote-debugging-port=9224")
            options.add_argument("-disable-gpu")
            options.add_argument("-no-sandbox")

            binary = FirefoxBinary(os.environ.get('FIREFOX_BIN'))

            browser = webdriver.Firefox(
                firefox_binary=binary,
                executable_path=os.environ.get('GECKODRIVER_PATH'),
                options=options
            )

        browser.get("https://rlpcgamelogs.com/")

        browser.find_element_by_xpath(
            "/html/body/app-root/div/app-main/div/div[1]/div[4]").click()  # Click "Status" tab
        time.sleep(3)
        browser.find_element_by_xpath(
            "/html/body/app-root/div/app-main/div/div[2]/div[1]").click()  # Click "Logs" tab
        time.sleep(10)
        browser.find_element_by_xpath(
            "/html/body/app-root/div/app-main/div/app-logs-status/div/div[2]/p-dropdown/div/label").click()
        time.sleep(3)

        dates = browser.find_elements_by_xpath(
            '/html/body/app-root/div/app-main/div/app-logs-status/div/div[2]/p-dropdown[1]/div/div[4]/div/ul/li')
        target_date = datetime.now(tz=pytz.timezone(
            "US/Eastern")) - timedelta(days=1)

        games_available = False
        for date in dates[::-1]:
            # Click the date for yesterday
            if date.text == target_date.strftime('%m/%d/%Y'):
                date.click()
                games_available = True
                break
        time.sleep(3)

        if not games_available:
            browser.quit()
            return False

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
                    row.find_element_by_xpath('td[7]/div').click()  # Download logs
                except:
                    pass  # If no logs are available

                score = f'{winner} {winnerScore}-{loserScore} {loser}'
                if scores != '':  # Add new line if this isn't the first score being added
                    scores += '\n'
                scores += score

            time.sleep(20)

        if update_elo:
            EloHandler().autoparse(scores)

        browser.quit()
        return True

    @staticmethod
    def get_own_replays(path='C:/Users/Simcha/Documents/My Games/Rocket League/TAGame/Demos') -> list:
        """
        Gets a list of replays from the file at the given path

        Parameters
        ----------
        path : str, optional
            Where to get the replay files from. The default is 'C:/Users/Simcha/Documents/My Games/Rocket League/TAGame/Demos'.

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
    def get_downloaded_replays(path: str = f'{os.getcwd()}/replay_processing/Downloaded_Replays', target: str = f"{os.getcwd()}/replay_processing/Replay_Files", max_age: float = 0.5) -> list:
        """
        Moves replay zip files downloaded from rlpcgamelogs.com to the target folder, and unfolds them in the process. Returns a list of retreived replays.

        Parameters
        ----------
        path : str, optional
            Where the downloaded replays are located. The default is './replay_processing/Downloaded_Replays'.
        target : str, optional
            Where to move unfolded replays. The default is "./replay_processing/Replay_Files".
        max_age : float, optional
            Maximum age, in days, of files to get. The default is 0.5.

        Returns
        -------
        files : list
            List of replay file paths unfolded and retreived

        """
        print(os.listdir(path))
        Retreiver.clean_folder(path=target)
        
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
                    dir = os.listdir(f"{target}/{name}/{folder}")
                    filename = dir[0]
                    for key in dir:
                        if os.path.getctime(f"{target}/{name}/{folder}/{key}") > os.path.getctime(f"{target}/{name}/{folder}/{filename}"):
                            filename = key
                    replays.append(f"{target}/{name}/{folder}/{filename}")
                files[name] = replays
                
                if os.environ.get('PROD') == 'false':
                    filepath = os.path.join(path, download).replace('/', '\\')
                else:
                    filepath = f'Downloads/{download}'
                
                os.remove(filepath)
                # shutil.rmtree(filepath)

        return files

    @staticmethod
    def clean_folder(path: str = f'{os.getcwd()}/replay_processing/Replay_Files'):
        for file in os.listdir(path):
            if 'gitignore' in file:
                continue
            filepath = os.path.join(path, file)
            try:
                shutil.rmtree(filepath)
            except:
                os.remove(filepath)


class Series:
    def __init__(self, session: Session, identifier: Identifier, length: int, replays: List[Replay]) -> None:
        self.failed = []
        self.unknown = []
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
        player_stats = pd.DataFrame(columns=["Username", *valid_stats])

        for replay in self.replays:
            try:
                replay.process()
            except ReplayFailedError:
                print(f"REPLAY FAILED: {replay.path}")
                self.failed.append(replay.path)
                self.length -= 1
                continue
            if replay.failed:
                print(f"REPLAY FAILED: {replay.path}")
                self.failed.append(replay.path)
                self.length -= 1  # Not sure if I should keep this in
                continue
            else:
                stats, unknown = replay.convert()
                player_stats = player_stats.append(stats)
                self.unknown = [*unknown, *self.unknown]

        player_stats = player_stats.groupby(player_stats.index).agg(lambda x: x.sum() if x.dtype=='float64' else x[0])

        # Add Series Played and Series Won stats
        for player in player_stats.index:
            player_stats.loc[player, 'Series Played'] = 1
            if (player_stats.loc[player, 'Games Won']/self.length) > 0.5:
                player_stats.loc[player, 'Series Won'] = 1

        return player_stats


class RLPCAnalysis:
    def __init__(self, session: Session = None, identifier: Identifier = None, p4sheet: Sheet = None, playersHandler: PlayersHandler = None) -> None:
        if not session:
            self.session = Session()
        else:
            self.session = session
        if not p4sheet:
            self.p4sheet = Sheet(sheet_p4)
        else:
            self.p4sheet = p4sheet
        if not identifier:
            self.identifier = Identifier(self.session, self.p4sheet)
        else:
            self.identifier = identifier
        if not playersHandler:
            self.playersHandler = PlayersHandler(self.session, self.p4sheet, self.identifier)
        else:
            self.playersHandler = playersHandler

        self.failed = []
        self.unknown = []

    def checks(self):
        self.playersHandler.check_players()
        # self.playersHandler.download_ids()

    def get_replays(self):
        if os.environ.get('PROD') == 'false':
            path = f'./replay_processing/Downloaded_Replays'
            target = f'./replay_processing/Replay_Files'
        else:
            path = './Downloads'
            target = f'./replay_processing/Replay_Files'
        replays = Retreiver.get_downloaded_replays(path=path, target=target)
        self.replays = replays
        return replays

    def analyze_replays(self):
        stats = pd.DataFrame(columns=["Username", *valid_stats])
        counter = 1
        replays = self.get_replays()
        series_list = []

        for series in list(replays):
            print(f'Uploading series {counter} of {len(list(replays))} ({round(((counter-1)/len(list(replays)))*100)}%)')

            games = []
            for replay_path in replays[series]:
                replay = BallchasingReplay(replay_path, self.session, self.playersHandler, self.identifier)
                if replay.uploaded:
                    games.append(replay)

            series_obj = Series(self.session, self.identifier, len(games), games)
            series_list.append(series_obj)

            counter += 1

        counter = 1
        for series in series_list:
            print(f'Analyzing series {counter} of {len(list(replays))} ({round(((counter-1)/len(list(replays)))*100)}%)')
            series: Series

            try:
                series_stats = series.get_stats()
                failed = series.failed
                unknown = series.unknown
                stats = stats.append(series_stats)
                self.failed = [*self.failed, *failed]  
                self.unknown = [*self.unknown, *unknown] 
            except KeyError:
                print("SERIES FAILED")  
                self.failed.append("SERIES " + str(counter))   

            counter += 1         

        self.stats = stats
        return stats

    def upload_stats(self, stats: pd.DataFrame):
        stats = stats.groupby(stats.index).agg(lambda x: x.sum() if x.dtype=='float64' else x[0])
        for player in stats.index:
            update = {'$inc': {}}

            for col in stats.columns:
                if col in ('Username', 'Fantasy Points', 'League'):
                    continue

                snake_stat = snakecase_stat(col)
                if type(stats.loc[player, col]) == np.int64:
                    datapoint = int(stats.loc[player, col])
                else:
                    datapoint = round(float(stats.loc[player, col]), 2)
                update['$inc'][f'seasons.$[season].season_stats.{snake_stat}'] = datapoint

            try:
                self.session.all_players.update_one(
                    {'_id': player},
                    update,
                    array_filters = [{"season.season_num": current_season}]
                )
            except:
                print("PLAYER STATS FAILED: "+player)
                continue

    def update_fantasy(self, stats: pd.DataFrame) -> None:
        if 'League' not in stats.columns:
            stats['Fantasy Points'] = stats.apply(lambda row: fantasy_formula(row), axis=1)
            stats['League'] = stats.apply(lambda row: self.identifier.find_league(self.identifier.find_team([row.name])), axis=1)
        fantasy = self.session.fantasy.find()

        if datetime.now(tz=pytz.timezone("US/Eastern")).weekday() == 4:
            self.session.fantasy.update_many({}, {'$set': {'transfers_left': 2}})

        while fantasy.alive:
            if fantasy.count() == 0:
                break
            account = fantasy.next()
            for player in account['players']:
                username = self.session.all_players.find_one({'_id': player})['username']

                if username not in stats.index: # They didn't have stats for this gameday
                    continue

                points = int(stats.loc[username, 'Fantasy Points'])
                self.session.fantasy.update_one(
                    {'_id': account['_id'], 'player_history.Player': player},
                    {'$inc': {'player_history.$.Points': points, 'points': points}}
                    )
        
        for player in stats.index:
            self.session.all_players.update_one(
                {'username': player},
                {'$inc': {'fantasy.fantasy_points': int(stats.loc[player, 'Fantasy Points'])}}
            )

    def log_data(self, stats: pd.DataFrame, range: str):
        def get_league(row):
            try:
                league = self.identifier.find_league(self.identifier.find_team([row.name]))
                if not league:
                    return "Unknown"
                else:
                    return league
            except:
                return "Unknown"

        if 'League' not in stats.columns:
            stats['Fantasy Points'] = stats.apply(lambda row: fantasy_formula(row), axis=1)
            stats['League'] = stats.apply(lambda row: get_league(row), axis=1)

        known = stats.loc[~stats['Username'].isin(self.unknown)]
        unknown = stats.loc[stats['Username'].isin(self.unknown)]

        sheet = Sheet(gdstats_sheet)
        sheet.push_df(range, known.reset_index().fillna(value=0))
        sheet.push_df("Failed Players!A2:Z", unknown.reset_index().fillna(value=0))

    def fix_failed(self):
        sheet = Sheet(gdstats_sheet)
        failed = sheet.to_df('Failed Players!A1:AN')
        fixed = pd.DataFrame(columns=failed.columns)
        if failed.empty:
            return print("No players found!")
        for row in failed.index:
            username = failed.loc[row, 'Username']
            known = input(f"Do you know who {username} is? (y/n) ")
            if known == "y":
                _id = input("Please type their discord id: ")
                # Add rl id to their account
                found = self.session.all_players.find_one_and_update({"_id": _id}, {"$push": {"rl_id": failed.loc[row, "Discord ID"]}})
                if found:
                    fixed = fixed.append(failed.loc[row])
                    fixed.loc[fixed['Username']==username, 'Discord ID'] = _id
                    fixed.loc[fixed['Username']==username, 'Username'] = found['username']
                    failed.drop(row)

        self.unknown = failed['Username'].values
        sheet.clear("Failed Players!A2:AN")
        self.log_data(fixed.set_index("Discord ID"), f'{dates[get_latest_gameday()]}!A2:Z')
        self.upload_stats(fixed.set_index("Discord ID"))


    def main(self):
        print("Checks")
        self.checks()

        print("Getting replays")
        stats = self.analyze_replays()

        print("Logging data")
        self.log_data(stats, f'{dates[get_latest_gameday()]}!A2:Z')

        print("Uploading Stats")
        self.upload_stats(stats)

        # print("Updating fantasy points")
        # self.update_fantasy(stats)

        print("FAILED: "+str(self.failed))


if __name__ == "__main__":
    download = Retreiver.download(update_elo=True)
    if download:
        RLPCAnalysis().main() # Only run if there were files to download
    # RLPCAnalysis().fix_failed()