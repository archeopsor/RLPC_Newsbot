from __future__ import annotations
import pandas as pd
import logging
from datetime import datetime
import os
from bson import ObjectId

# Allow imports when running script from within project dir
import sys
[sys.path.append(i) for i in ['.', '..']]

from tools.mongo import Session, teamIds
from tools.sheet import Sheet
from rlpc.db_models import Player, Games, Region, Platform, MMRData, JoinMethod, LeaveMethod

from settings import sheet_p4, current_season
from errors.player_errors import *

logger = logging.getLogger(__name__)


class PlayersHandler:
    def __init__(self, session: Session = None, p4sheet: Sheet = None, identifier: Identifier = None):
        if not p4sheet:
            self.p4sheet = Sheet(sheet_p4)
        else:
            self.p4sheet = p4sheet
        if not session:
            self.session = Session()
        else:
            self.session = session
        if not identifier:
            self.identifier = Identifier()
        else:
            self.identifier = identifier

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
        players['Sheet MMR'] = players['Sheet MMR'].apply(
            lambda x: int(x) if x != '' else x)
        players['Tracker MMR'] = players['Tracker MMR'].apply(
            lambda x: int(x) if x != '' else x)
        data: pd.DataFrame = players.loc[(players['League'] == league) & ~(players['Team'].isin(
            ['Not Playing', 'Waitlist', 'Future Star']))].reset_index(drop=True)  # Get valid players from correct league
        mmr = int(mmr)
        num_greater: int = data[data['Tracker MMR']
                                > mmr]['Tracker MMR'].count()
        num_less: int = data[data['Tracker MMR'] < mmr]['Tracker MMR'].count()
        percentile = num_less/(num_greater+num_less)
        fantasy_value = round(80 + 100*percentile)

        doc = self.session.structures['players'].copy()
        doc["username"] = username
        doc['info']['region'] = region
        doc['info']['platform'] = platform
        doc['info']['mmr'] = mmr
        doc['info']['team'] = teamIds[team.title()]
        doc['info']['league'] = league
        doc['info']['id'] = ids
        doc['info']['discord_id'] = discord_id
        doc['fantasy']['fantasy_value'] = fantasy_value

        # Add player to players collection
        self.session.players.insert_one(doc)

        # Add player to team in teams collection
        self.session.teams.find_one_and_update(
            {"_id": teamIds[team.title()]},
            {"$push": {"players": doc['_id']}}            
        )

    def download_ids(self):
        """
        Takes player IDs from the RLPC Sheet and adds them to the database

        Returns
        -------
        None.

        """
        logger.info("Downloading IDs...")
        print("IDS")
        sheetdata = self.p4sheet.to_df('Players!A1:AG')
        sheetdata['Unique IDs'] = sheetdata['Unique IDs'].map(
            lambda x: x.split(","))
        sheetdata = sheetdata.drop_duplicates(subset='Username')
        sheetdata = sheetdata.loc[sheetdata['Username'] != ""]
        sheetdata = sheetdata.loc[sheetdata['Departed'] == "FALSE"]

        for player in sheetdata['Username']:

            # Make sure to only care about active players
            if sheetdata.loc[sheetdata['Username'] == player, 'Team'].values[0] in ['Not Playing', 'Ineligible', 'Future Star', 'Departed', 'Banned', 'Waitlist', 'Below MMR']:
                continue

            # See if the player's username is in the database
            if self.session.players.count_documents({'username': player}) == 0:
                fixed = False

                # Look through ids on the sheet, see if it maches any in the database
                # Any matches indicate a name change
                for playerid in sheetdata.loc[sheetdata['Username']==player, 'Unique IDs']:
                    if playerid == '':
                        continue  # No ids are available, so just ignore
                    else:
                        doc = self.session.players.find_one_and_update(
                            {'info.id': playerid}, {'$set': {'username': player}})
                        if not doc:
                            continue  # There were no players in database with this id
                        old_username = doc['username']
                        fixed = True
                        logger.info(
                            f'{old_username} has changed their name to {player}')
                        break

                if not fixed:
                    # Can't find the id anywhere in db, so add a new player
                    playerinfo = sheetdata.loc[sheetdata['Username'] == player]
                    try:
                        self.add_player(player, playerinfo['Region'].values[0], playerinfo['Platform'].values[0], playerinfo['Sheet MMR'].values[0],
                                        playerinfo['Team'].values[0], playerinfo['League'].values[0], int(playerinfo['Discord ID'].values[0]), ids=playerinfo['Unique IDs'].tolist())
                        logger.info(f'{player} added')
                    except:
                        logger.info(f'{player} failed to add')

            else:  # Player's username is found in db
                doc = self.session.players.find_one({'username': player})
                try:
                    db_ids = set(doc['info']['id'])
                except TypeError:
                    db_ids = set(doc['info']['id'][0]) # Some players have weird id structures for some reason TODO: Look into this.
                sheet_ids = set(
                    sheetdata.loc[sheetdata['Username'] == player, 'Unique IDs'].values[0])

                # Check if database ids are a superset of sheet ids
                superset = db_ids.issuperset(sheet_ids)
                if not superset:
                    # Sheet has id(s) that aren't in db, so combine both sets to get updated list
                    ids = sheet_ids.union(db_ids)
                    doc['info']['ids'] = ids
                    self.session.players.update_one(
                        {"username": player}, {"$set": {"info.id": list(ids)}})
                    logger.info(f"{player} ids updated")

        logger.info("Done downloading ids.")

    def move_teams(self, id: str, old: str, new: str, join_method: JoinMethod = JoinMethod.OTHER, leave_method: LeaveMethod = LeaveMethod.OTHER):
        player_doc = self.session.all_players.find_one({"_id": id})
        old_doc = self.session.teams.find_one({"_id": old})
        new_doc = self.session.teams.find_one({"_id": new})
        if old_doc and new_doc:
            leave_method = LeaveMethod.TRADE
            join_method = JoinMethod.TRADE

        new_team = {
                    "name": new,
                    "league": self.identifier.find_league(new),
                    "join_season": current_season,
                    "join_method": join_method.value,
                    "leave_season": None,
                    "leave_method": None
                }
        new_player = {
                    "playerid": id,
                    "join_date": datetime.now(),
                    "join_method": join_method.value,
                    "leave_date": None,
                    "leave_method": None
                }

        # Update player
        self.session.all_players.find_one_and_update({"_id": id}, {
            "$set": {
                "current_team": new,
            }
        })
        if old_doc:
            self.session.all_players.find_one_and_update({"_id": id}, {
                "$set": {
                    f"team_history.{len(player_doc['team_history']) - 1}.leave_season": current_season,
                    f"team_history.{len(player_doc['team_history']) - 1}.leave_method": leave_method.value,
                    "seasons.$[season].teams.$[team].leave_season": current_season,
                    "seasons.$[season].teams.$[team].leave_method": leave_method.value,
                }}, array_filters = [{'season.season_num': current_season}, {"team.name": old, "team.leave_season": None}])
        if new_doc:
            self.session.all_players.find_one_and_update({"_id": id}, {
                "$push": {
                    "seasons.$[season].teams": new_team,
                    "team_history": new_team,
                }
            }, array_filters = [{'season.season_num': current_season}])
        
        # Update old team (assuming the old team isn't a non-playing team)
        if old_doc:
            self.session.teams.find_one_and_update({"_id": old}, {
                "$pull": {"current_players": id},
                "$push": {"previous_players": id},
                "$set": {
                    "seasons.$[season].players.$[player].leave_date": datetime.now(),
                    "seasons.$[season].players.$[player].leave_method": leave_method.value,
                }
            }, array_filters = [{'season.season_num': current_season}, {"player.playerid": id, "player.leave_date": None}])

        # Update new team (assuming the new team isn't a non_playing team)
        if new_doc:
            self.session.teams.find_one_and_update({"_id": new}, 
            {
                "$push": {
                    "current_players": id,
                    "seasons.$[season].players": new_player
                }
            }, array_filters = [{"season.season_num": current_season}])

    def check_players(self):
        """
        Compares the rlpc sheet to the database to ensure that all players are present and have accurate info

        Returns
        -------
        None.

        """

        logger.info("Checking players...")
        sheetdata = self.p4sheet.to_df("Players!A1:AG")
        sheetdata['Unique IDs'] = sheetdata['Unique IDs'].map(lambda x: x.split(","))
        sheetdata['Tracker'] = sheetdata['Tracker'].map(lambda x: x.split(', '))
        sheetdata['Sheet MMR'] = sheetdata['Sheet MMR'].map(lambda x: int(x))
        sheetdata['Tracker MMR'] = sheetdata['Tracker MMR'].map(lambda x: int(x))
        sheetdata = sheetdata.loc[sheetdata['Username'] != ""]
        sheetdata = sheetdata.loc[sheetdata['Team'] != "N/A"] # This should never happen unless sheets team puts it here, /shrug
        sheetdata = sheetdata.loc[sheetdata['Departed'] != "TRUE"]
        sheetdata = sheetdata.loc[sheetdata['Not Playing'] != "TRUE"]
        sheetdata = sheetdata.set_index('Discord ID')

        all_players = self.session.all_players
        teams = self.session.teams

        # NEW CHECKS
        for discord_id in sheetdata.index:
            player: str = sheetdata.loc[discord_id, 'Username']

            # First check if the player is already in the database
            doc = self.session.all_players.find_one({"_id": discord_id})

            # If the player is not in the database, add them as a player
            if doc == None:
                logger.debug(f"Adding {player} to database")
                data = Player(
                    _id = discord_id,
                    username = player,
                    date_joined = datetime.now(),
                    rl_id = sheetdata.loc[discord_id, 'Unique IDs'],
                    tracker_links = sheetdata.loc[discord_id, 'Tracker'],
                    region = Region.from_str(sheetdata.loc[discord_id, 'Region']),
                    platform = Platform.from_str(sheetdata.loc[discord_id, 'Platform']),
                    mmr = MMRData(sheetdata.loc[discord_id, 'Sheet MMR'], sheetdata.loc[discord_id, 'Tracker MMR'], {datetime.now().strftime("%m/%d/%y"): sheetdata.loc[discord_id, 'Tracker MMR']}), 
                    current_team = sheetdata.loc[discord_id, 'Team'],
                    team_history = None,
                    seasons = None              # Will be added later in this function if needed
                ).insert_new(self.session)
            
            # Otherwise, check fields to see if any of them changed
            else:
                data = Player.from_db(doc)

                # Username
                if data.username != player:
                    data.username = player
                    all_players.find_one_and_update({"_id": discord_id}, {"$set": {"username": player}})
                    logger.debug(f"{data.username} has changed their name to {player}")

                # rl ids
                for playerid in sheetdata.loc[discord_id, 'Unique IDs']:
                    if playerid == '':
                        continue # No ids are available, so just ignore
                    elif playerid not in data.rl_id:
                        data.rl_id.append(playerid)
                        all_players.find_one_and_update({"_id": discord_id}, {"$push": {"rl_id": playerid}})
                        logger.debug(f"Added id '{playerid}' for {player}")

                # tracker links
                for tracker in sheetdata.loc[discord_id, 'Tracker']:
                    if tracker == '':
                        continue # No trackers are available, so just ignore
                    elif tracker not in data.tracker_links:
                        data.tracker_links.append(tracker)
                        all_players.find_one_and_update({"_id": discord_id}, {"$push": {"tracker_links": tracker}})
                        logger.debug(f"Added tracker {tracker} for {player}")

                # Region
                if data.region != Region.from_str(sheetdata.loc[discord_id, 'Region']):
                    data.region = Region.from_str(sheetdata.loc[discord_id, 'Region'])
                    all_players.find_one_and_update({"_id": discord_id}, {"$set": {"region": sheetdata.loc[discord_id, 'Region']}})
                    logger.debug(f"Moved {player} to {data.region}")

                # Platform
                if data.platform != Platform.from_str(sheetdata.loc[discord_id, 'Platform']):
                    data.platform = Platform.from_str(sheetdata.loc[discord_id, 'Platform'])
                    all_players.find_one_and_update({"_id": discord_id}, {"$set": {"platform": sheetdata.loc[discord_id, 'Platform']}})
                    logger.debug(f"Switched {player} to {data.platform}")

                # MMR
                if data.mmr.current_official_mmr != sheetdata.loc[discord_id, 'Sheet MMR']:
                    data.mmr.current_official_mmr = sheetdata.loc[discord_id, 'Sheet MMR']
                    all_players.find_one_and_update({"_id": discord_id}, {"$set": {"mmr.current_official_mmr": sheetdata.loc[discord_id, 'Sheet MMR']}})
                    logger.debug(f"Updated {player}'s Sheet MMR to {data.mmr.current_official_mmr}")

                # Team
                if data.current_team != sheetdata.loc[discord_id, 'Team']:
                    old = data.current_team
                    new = sheetdata.loc[discord_id, 'Team']
                    data.current_team = new
                    self.move_teams(discord_id, old, new) # TODO: Figure out join/leave methods

        self.remove_not_playing()
        logger.info("Done checking players.")

    def remove_not_playing(self):
        """Changes team of anyone listed on the sheet as "Not Playing" or "Departed"

        Returns:
            None
        """
        sheetdata = self.p4sheet.to_df("Players!A1:AG")

        sheetdata = sheetdata.drop_duplicates(subset='Username')
        sheetdata = sheetdata.loc[sheetdata['Username'] != ""]
        sheetdata.set_index("Username", inplace=True)
        not_playing = sheetdata.loc[sheetdata['Not Playing'] == "TRUE"]
        departed = sheetdata.loc[sheetdata['Departed'] == "TRUE"]

        logger.info("NOT PLAYING")
        for player in not_playing.index:
            discord_id: str = not_playing.loc[player, 'Discord ID']
            doc = self.session.all_players.find_one({'_id': discord_id})
            if doc == None:
                continue
            if doc['current_team'] != "Not Playing":
                self.move_teams(discord_id, doc['current_team'], "Not Playing", JoinMethod.OTHER, LeaveMethod.NONPLAYING)
        
        logger.info("DEPARTED")
        for player in departed.index:
            discord_id: str = departed.loc[player, 'Discord ID']
            doc = self.session.players.find_one({'_id': discord_id})
            if doc == None:
                continue
            if doc['current_team'] != "Departed":
                self.move_teams(discord_id, doc['current_team'], "Departed", JoinMethod.OTHER, LeaveMethod.NONPLAYING)


class Identifier:
    def __init__(self, session: Session = None, p4sheet: Sheet = None):
        if not p4sheet:
            self.p4sheet = Sheet(sheet_p4)
        else:
            self.p4sheet = p4sheet
        if not session:
            self.session = Session()
        else:
            self.session = session
        self.ids = {}
        self.leagues = {}
        self.tracker_ids = {}

    def identify(self, id: str) -> str:
        """
        Determines which player matches a given ID

        Parameters
        ----------
        id : str
            The unique Rocket Leauge ID of any given player.

        Returns
        -------
        str
            The name of the player as spelled on the RLPC Spreadsheet.

        """
        if self.ids.get(id):
            return self.ids.get(id)

        player = self.session.players.find_one({'info.id': id})
        if not player:
            return None
        else:
            self.ids[id] = player['username']
            return player['username']

    def find_team(self, names: list, id_players: bool = False, choices: list = None) -> str:
        """
        Determines which team most likely matches a given set of three players

        Parameters
        ----------
        names : list
            List of player names (should be verified as the same on the sheet before using find_team()).
        id_players : bool
            Whether or not this function should identify players first (if given a list of ids rather than names)
        choices : list
            A list of possible teams that this can be. This is used to find the correct team in case of subs or call downs

        Returns
        -------
        str
            Team name.

        """

        if id_players:
            new_names = []
            for id in names:
                name = self.identify(id)
                if not name:
                    continue
                new_names.append(name)
            names = new_names

        found_teams = []
        teams = self.p4sheet.to_df("Teams!F1:P129")

        for player in names:
            doc = self.session.players.find_one({'username': player})
            teamId: ObjectId = doc['info']['team']
            if teamId in ['Free Agent', 'Not Playing', 'Departed', 'Waitlist']:
                continue
            try:
                team = self.session.teams.find_one({'_id': teamId})['team']
            except TypeError:
                continue

            if choices:
                choice_league = self.find_league(choices[0])
                team_league = self.find_league(team)
                affiliate_columns = {
                    'Major': 'Major Affiliate',
                    'AAA': 'AAA Affiliate',
                    'AA': 'AA Affiliate',
                    'A': 'A Affiliate',
                    'Independent': 'Major Affiliate',
                    'Maverick': 'AAA Affiliate',
                    'Renegade': 'AA Affiliate',
                    'Paladin': 'A Affiliate'
                }
                if teams.loc[teams['Team'] == team, affiliate_columns[choice_league]].values[0] != '': # This player is from a different league, so is likely a sub
                    team = teams.loc[teams['Team'] == team, affiliate_columns[choice_league]].values[0]

            found_teams.append(team)

        for team in found_teams:
            if found_teams.count(team) > (len(found_teams)/2):
                return team  # This will return if more than half of the players are on the same team

        return "Undetermined"  # If every player belongs to a different team

    def find_league(self, team: str) -> str:
        """
        Finds out what league a team plays in

        Parameters
        ----------
        team : str
            Name of the team.

        Returns
        -------
        str
            Name of the league.

        """

        team = team.title()

        if self.leagues.get(team):
            return self.leagues.get(team)

        if team in ['Not Playing', 'Departed', 'Waitlist', 'Free Agent']:
            return None

        doc = self.session.teams.find_one({"_id": team})
        self.leagues[team] = doc['league']
        return doc['league']

    def tracker_identify(self, name: str) -> str:
        """
        Finds a player's username based on the name used in-game by seeing if it matches any rltracker links

        Parameters
        ----------
        name : str
            The in-game name of a player.

        Returns
        -------
        str
            The name of the player as spelled on the RLPC Spreadsheet.

        """
        sheetdata = self.p4sheet.to_df('Players!A1:AE')
        player = sheetdata.loc[sheetdata['Tracker'].str.contains(name.replace(' ', '%20'), case=False), 'Username']
        try:
            return player.values[0]
        except:
            return None


class TeamsHandler: 
    def __init__(self, refresh_cooldown: int = 30, session: Session = None):
        self.cooldown = refresh_cooldown

        if not session:
            self.session = Session()
        else:
            self.session = session
        
        self.sheet = Sheet(sheet_p4, refresh_cooldown=self.cooldown)

    def get_data(self, team: str) -> pd.Series:
        data = self.sheet.to_df('Teams!A1:AD129') # ALL the team data, not really necessary but good to have
        data.set_index("Team", inplace=True)
        team = team.title()
        try:
            data = data.loc[team]
        except KeyError:
            raise TeamNotFoundError(team)

        return data

    def get_gm(self, data: pd.Series) -> str:
        return data.loc['GM']

    def get_agm(self, data: pd.Series) -> str:
        return data.loc['AGM']

    def get_captain(self, data: pd.Series) -> str:
        captain = data.loc['Captain']
        if captain == '':
            return None
        else:
            return captain

    def get_league(self, data: pd.Series) -> str:
        return data.loc['League']

    def get_org(self, data: pd.Series) -> dict:
        system = data['League System']

        org = {
            'System': system,
            'Teams': []
        }
        org['Teams'] = data.loc['Organization Name'].split('/')

        return org

    def get_logo_url(self, data: pd.Series) -> str:
        # path = '/'.join(os.getcwd().split('\\')) + f"/Image_templates/RLPC_Logos/{team.title()}.png"
        # return path

        return data.loc['Logo']

    def get_roster(self, team: str) -> list:
        players = self.sheet.to_df("Players!A1:AG")
        players = players[players['Departed'] == "FALSE"]
        players = players[players['Not Playing'] == "FALSE"]
        players = players[players['Team'] == team.title()]
        players.drop_duplicates(subset="Username", inplace=True)

        roster = list(players['Username'].values)
        return roster


if __name__ == "__main__":
    players = PlayersHandler()
    players.check_players()