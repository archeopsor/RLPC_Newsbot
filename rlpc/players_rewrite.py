import pandas as pd
import logging

from tools.mongo import Session, teamIds
from tools.sheet import Sheet

from settings import sheet_p4

p4sheet = Sheet(sheet_p4)
db = Session()
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
        self.db = db

    def add_player(self, username: str, region: str, platform: str, mmr: int, team: str, league: str, discord_id: int, ids: list = []): 
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
        discord_id: int
            Player's discord id
        ids : list, optional
            List of IDs of rocket league accounts from the sheet. The default is [].

        Returns
        -------
        None.

        """
        players = self.p4sheet.to_df('Players!A1:W')
        players['Sheet MMR'] = players['Sheet MMR'].apply(lambda x: int(x) if x != '' else x)
        players['Tracker MMR'] = players['Tracker MMR'].apply(lambda x: int(x) if x != '' else x)
        data: pd.DataFrame = players.loc[(players['League']==league) & ~(players['Team'].isin(['Not Playing', 'Waitlist', 'Future Star']))].reset_index(drop=True) # Get valid players from correct league
        mmr = int(mmr)
        num_greater: int = data[data['Tracker MMR'] > mmr]['Tracker MMR'].count()
        num_less: int = data[data['Tracker MMR'] < mmr]['Tracker MMR'].count()
        percentile = num_less/(num_greater+num_less)
        fantasy_value = round(80 + 100*percentile)
        
        doc = db.structures['players']
        doc["username"] = username
        doc['info']['region'] = region
        doc['info']['platform'] = platform
        doc['info']['mmr'] = mmr
        doc['info']['team'] = teamIds[team.title()]
        doc['info']['league'] = league
        doc['info']['id'] = ids
        doc['info']['discord_id'] = discord_id
        doc['fantasy']['fantasy_value'] = fantasy_value

        return self.db.players.insert_one(doc).inserted_id
        
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
        
        for player in sheetdata['Username']:
            
            # Make sure to only care about active players
            if sheetdata.loc[sheetdata['Username']==player, 'Team'].values[0] in ['Not Playing', 'Ineligible', 'Future Star', 'Departed', 'Banned', 'Waitlist']:
                continue
            
            # See if the player's username is in the database
            if self.db.players.count_documents({'username': player}) == 0:
                fixed = False
                
                # Look through ids on the sheet, see if it maches any in the database
                # Any matches indicate a name change
                for playerid in sheetdata.loc[player, 'Unique IDs']:
                    if playerid == '':
                        continue # No ids are available, so just ignore
                    else:
                        try: # Find any usernames linked to id
                            old_doc = self.db.players.find_one({'info': {'id': playerid}})
                            old_username = old_doc['username']
                            
                            # Found their new and old usernames, so make the change
                            logger.info(f'{old_username} has changed their name to {player}')
                            old_doc['info']['id'].append(playerid)
                            self.db.players.update_one({"_id": old_doc['_id']}, old_doc)
                            fixed = True
                            break
                        
                        except: # There are none, so go to next id
                            continue
                    
                if not fixed:
                    # Can't find the id anywhere in db, so add a new player
                    playerinfo = sheetdata.loc[sheetdata['Username']==player]
                    self.add_player(player, playerinfo['Region'].values[0], playerinfo['Platform'].values[0], playerinfo['Sheet MMR'].values[0], playerinfo['Team'].values[0], playerinfo['League'].values[0], int(playerinfo['Discord ID'].values[0]), ids = playerinfo['Unique IDs'].tolist())
                    logger.info(f'{player} added')
                    
            else: # Player's username is found in db
                doc = self.db.players.find_one({'username': player})
                db_ids = set(doc['info']['id'])
                sheet_ids = set(sheetdata.loc[sheetdata['Username']==player, 'Unique IDs'].values[0])
            
                # Check if database ids are a superset of sheet ids
                superset = db_ids.issuperset(sheet_ids)
                if not superset:
                    # Sheet has id(s) that aren't in db, so combine both sets to get updated list
                    ids = sheet_ids.union(db_ids)
                    doc['info']['ids'] = ids
                    self.db.players.update_one({"username": player}, doc)
                    logger.info(f"{player} ids updated")
                    
        self.session.commit()
        

class Identifier:
    def __init__(self):
        self.p4sheet = p4sheet
        
        
        