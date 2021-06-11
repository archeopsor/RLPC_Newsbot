import os
import shutil
import time
from typing import Union
import pandas as pd
import numpy as np
import logging
from zipfile import ZipFile
from datetime import datetime, timedelta
import pytz

import carball

from tools.database import engine, select
from tools.sheet import Sheet

from rlpc.players import download_ids, identify, find_team, find_league, check_players, tracker_identify
from rlpc import elo


class Structs: # TODO: Make an analysis class and put all these in there
    def __init__(self):
        self._players = select("players").fillna(value=0)
        
    @property
    def players(self):
        return self._players


class Retreiver:
    def __init__(self):
        pass
    
    @staticmethod
    def download(elo=True):
        """
        Downloads yesterday's replays from the rlpcgamelogs website

        Returns
        -------
        None.

        """
        from selenium import webdriver
        
        # To prevent download dialog
        profile = webdriver.FirefoxProfile()
        profile.set_preference('browser.download.folderList', 2) # custom location
        profile.set_preference('browser.download.manager.showWhenStarting', False)
        profile.set_preference('browser.download.dir', '/tmp')
        profile.set_preference('browser.helperApps.neverAsk.saveToDisk', 'application/octet-stream, application/zip')
        
        browser = webdriver.Firefox(profile, executable_path=r'C:\Users\Simi\Documents\geckodriver.exe')
        browser.get("https://rlpcgamelogs.com/")
        
        browser.find_element_by_xpath("/html/body/app-root/div/app-main/div/div[1]/div[4]").click() # Click "Status" tab
        time.sleep(3)
        browser.find_element_by_xpath("/html/body/app-root/div/app-main/div/div[2]/div[1]").click() # Click "Logs" tab
        time.sleep(3)
        browser.find_element_by_xpath("/html/body/app-root/div/app-main/div/app-logs-status/div/div[2]/p-dropdown/div/label").click()
        time.sleep(3)
        
        dates = browser.find_elements_by_xpath('/html/body/app-root/div/app-main/div/app-logs-status/div/div[2]/p-dropdown[1]/div/div[4]/div/ul/li')
        target_date = datetime.now(tz=pytz.timezone("US/Eastern")) - timedelta(days=1)
        for date in dates[::-1]:
            if date.text == target_date.strftime('%m/%d/%Y'): # Click the date for yesterday
                date.click()
                break
        time.sleep(3)
        
        browser.find_element_by_xpath('/html/body/app-root/div/app-main/div/app-logs-status/div/div[2]/p-dropdown[2]/div/label').click() # Click "League" tab
        time.sleep(3)
        leagues = browser.find_elements_by_xpath('/html/body/app-root/div/app-main/div/app-logs-status/div/div[2]/p-dropdown[2]/div/div[4]/div/ul/li')
        
        scores = ""
        
        for i in range(1, len(leagues)+1): # Does the below for every league that shows up on the website
            browser.find_element_by_xpath('/html/body/app-root/div/app-main/div/app-logs-status/div/div[2]/p-dropdown[2]/div/label').click() # Click "League" tab
            time.sleep(3)
            try:
                browser.find_element_by_xpath(f'/html/body/app-root/div/app-main/div/app-logs-status/div/div[2]/p-dropdown[2]/div/div[4]/div/ul/li[{i}]').click() # Click appropriate league on drop-down list
            except:
                browser.find_element_by_xpath('/html/body/app-root/div/app-main/div/app-logs-status/div/div[2]/p-dropdown[2]/div/label').click() # Click "League" tab
                browser.find_element_by_xpath(f'/html/body/app-root/div/app-main/div/app-logs-status/div/div[2]/p-dropdown[2]/div/div[4]/div/ul/li[{i}]').click() # Click appropriate league on drop-down list
            
            table = browser.find_elements_by_xpath('/html/body/app-root/div/app-main/div/app-logs-status/div/div[3]/table/tbody/tr')
            for row in table:
                if row.text == 'Team Team Deadline Passed': # Logs not submitted table
                    continue
                
                winner = row.find_element_by_xpath('td[1]').text
                
                if winner == 'Winning Team': # First row of the table
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
                    row.find_element_by_xpath('td[7]/div').click() # Download logs
                except:
                    pass # If no logs are available
                
                score = f'{winner} {winnerScore}-{loserScore} {loser}'
                if scores != '': # Add new line if this isn't the first score being added
                    scores += '\n'
                scores += score
                
            time.sleep(13)
        
        if elo:
            elo.autoparse(scores)
        
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
    def get_downloaded_replays(path: str = 'C:/Users/Simi/Downloads', target: str = "./Replay_Files", max_age: int = 1) -> list:
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
            new = os.path.getmtime(f"{path}/{download}") > time.time()-(max_age*80000)
            if download.endswith('.zip') and new:
                replays = []
                teams = download.split(" - ")[0].split(" vs. ")
                name = f"{teams[0]} - {teams[1]}"
                with ZipFile(f"{path}/{download}", 'r') as zip_ref:
                    zip_ref.extractall(f"{target}/{name}") # Extract files to new folder
                for folder in os.listdir(f"{target}/{name}"):
                    filename = os.listdir(f"{target}/{name}/{folder}")[0]
                    replays.append(f"{target}/{name}/{folder}/{filename}")
                files[name] = replays
                
                shutil.rmtree(f"{path}/{download}")
            
        return files
    
    @staticmethod
    def clean_folder(path: str = './Replay_Files'):
        for file in os.listdir(path):
            filepath = os.path.join(path, file)
            shutil.rmtree(filepath)
            
            
class Replay:
    def __init__(self, path: str, isPerGoal: bool = False):
        self.path = path.replace('\\', '/')
        self.failed = False
        self.structs = Structs()
        self._stats, self._frames = self.process(isPerGoal)
    
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
            analysis_manager = carball.analyze_replay_file(self.path, logging_level=logging.CRITICAL)
        except:
            print("REPLAY FAILED: " + self.path)
        
        frames = analysis_manager.get_data_frame().fillna(value=0)
        stats = dict(analysis_manager.get_json_data())
        
        return stats, frames
    
    def get_teams(self) -> Union[str, str]:
        """
        Returns a verified and ordered list of the two teams' names

        Returns
        -------
        teams : list
            The two teams in this replay.

        """
        players = self.structs.players
        stats = self._stats
        choices = self.path.split('/')[-1].split(' - ')
        
        teams = []
        teams.append([x['id'] for x in stats['teams'][0]['playerIds']])
        teams.append([x['id'] for x in stats['teams'][1]['playerIds']])
        team1 = find_team(teams[0], players, id_players = True, choices = choices)
        team2 = find_team(teams[1], players, id_players = True, choices = choices)
    
        return [team1, team2]
        
    def get_players(self):
        """
        Gets a list of all the valid (non-sub) players

        Returns
        -------
        players : list
            List of all valid players in the replay.

        """
        teams = self._teams
        stats = self._stats
        players = self.structs.players
        players: list = []
        
        for player in stats['players']:
            name = identify(player['id']['id'], players)
            if name == None:
                name = identify(player['name'], players)
                if name == None:
                    name = tracker_identify(player['name'])
                    if name == None:
                        name = player['name']
            
            # Handle subs
            try: 
                if players.loc[players['Username']==name, 'League'].values[0] != players.loc[players['Team']==teams[0], 'League'].values[0]:
                    # This should only be true if the player is not actually on the team, ie a sub or call down
                    continue
                elif players.loc[players['Username']==name, 'Team'].values[0] not in teams:
                    continue
            except:
                print("PLAYER FAILED: " + name)
                continue
            
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
    
