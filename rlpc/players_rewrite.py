import pandas as pd
import logging

from tools.database import select, Players, Session
from tools.sheet import Sheet

from settings import sheet_p4

p4sheet = Sheet(sheet_p4)
session = Session().session
logger = logging.getLogger(__name__)

def flatten(items, seqtypes=(list, tuple)):
    for i, x in enumerate(items):
        while i < len(items) and isinstance(items[i], seqtypes):
            items[i:i+1] = items[i]
    items = [i for i in items if i != '']
    return items


class Players:
    def __init__(self):
        self.p4sheet = p4sheet
        self.session = session

    def add_player(self, username: str, region: str, platform: str, mmr: int, team: str, league: str, ids: list = []): 
        """
        Adds a row to  the players database

        Parameters
        ----------
        username : str
            Player's username.
        region : str
            Region where the player plays from.
        platform : str
            Player's main platform.
        mmr : int
            Player's mmr as listed on the sheet.
        team : str
            Team the player is on.
        league : str
            League the player plays in.
        ids : list, optional
            List of IDs of rocket league accounts from the sheet. The default is [].

        Returns
        -------
        None.

        """
        players = self.p4sheet.to_df('Players!A1:W')
        players['Sheet MMR'] = players['Sheet MMR'].apply(lambda x: int(x) if x != '' else x)
        players['Tracker MMR'] = players['Tracker MMR'].apply(lambda x: int(x) if x != '' else x)
        data = players.loc[(players['League']==league) & ~(players['Team'].isin(['Not Playing', 'Waitlist', 'Future Star']))].reset_index(drop=True) # Get valid players from correct league
        mmr = int(mmr)
        num_greater = data[data['Tracker MMR'] > mmr]['Tracker MMR'].count()
        num_less = data[data['Tracker MMR'] < mmr]['Tracker MMR'].count()
        percentile = num_less/(num_greater+num_less)
        fantasy_value = round(80 + 100*percentile)
        
        row = Players(username, region, platform, mmr, team, league, fantasy_value)
        
        if ids:
            ids = ids.reset_index(drop=True) # Not really sure why this is needed, but it is
            row.id = ids
      
        self.session.add(row)
        self.session.commit()
        return
        
    def download_ids(self):
        """
        Takes player IDs from the RLPC Sheet and adds them to the database
    
        Returns
        -------
        None.
    
        """
        logger.info("Downloading IDs...")
        sheetdata = self.p4sheet.to_df('Players!A1:AE')
        sheetdata['Unique IDs'] = sheetdata['Unique IDs'].map(lambda x: x.split(","))
        sheetdata = sheetdata.drop_duplicates(subset='Username')
        sheetdata = sheetdata.loc[sheetdata['Username']!=""]
        
        players = self.session.query(Players)
        for player in sheetdata['Username']:
            
            # Make sure to only care about active players
            if sheetdata.loc[sheetdata['Username']==player, 'Team'].values[0] in ['Not Playing', 'Ineligible', 'Future Star', 'Departed', 'Banned', 'Waitlist']:
                continue
            
            # See if the player's username is in the database
            row = self.session.query(Players).get(player)
            if row == None:
                fixed = False
                
                # Look through ids on the sheet, see if it maches any in the database
                # Any matches indicate a name change
                for playerid in sheetdata.loc[player, 'Unique IDs']:
                    if playerid == '':
                        continue # No ids are available, so just ignore
                    else:
                        try: # Find any usernames linked to id
                            old_username = self.session.query(Players.username).filter(Players.id.any(playerid)).first()[0]
                            
                            # Found their new and old usernames, so make the change
                            logger.info(f'{old_username} has changed their name to {player}')
                            self.session.query(Players).get(old_username).username = player
                            fixed = True
                        
                        except: # There are none, so go to next id
                            continue
                    
                if not fixed:
                    # Can't find the id anywhere in db, so add a new player
                    playerinfo = sheetdata.loc[sheetdata['Username']==player]
                    self.add_player(player, playerinfo['Region'].values[0], playerinfo['Platform'].values[0], playerinfo['Sheet MMR'].values[0], playerinfo['Team'].values[0], playerinfo['League'].values[0], ids = playerinfo['Unique IDs'])
                    logger.info(f'{player} added')
                    
            else: # Player's username is found in db
                db_ids = set(row.id)
                sheet_ids = set(sheetdata.loc[sheetdata['Username']==player, 'Unique IDs'].values[0])
            
                # Check if database ids are a superset of sheet ids
                superset = db_ids.issuperset(sheet_ids)
                if not superset:
                    # Sheet has id(s) that aren't in db, so combine both sets to get updated list
                    ids = sheet_ids.union(db_ids)
                    row.ids = ids
                    logger.info(f"{player} ids updated")
                    
        self.session.commit()
        

class Identifier:
    def __init__(self):
        self.p4sheet = p4sheet
        
        
        