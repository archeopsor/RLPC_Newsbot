import pandas as pd
import logging
import time
from bson import ObjectId

from tools.mongo import Session, teamIds
from tools.sheet import Sheet

from settings import sheet_p4

logger = logging.getLogger(__name__)


class Players:
    def __init__(self, session: Session = None, p4sheet: Sheet = None):
        if not p4sheet:
            self.p4sheet = Sheet(sheet_p4)
        else:
            self.p4sheet = p4sheet
        if not session:
            self.session = Session()
        else:
            self.session = session

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

        self.session.refresh()
        return self.session.client['rlpc-news'].players.insert_one(doc)

    def download_ids(self):
        """
        Takes player IDs from the RLPC Sheet and adds them to the database

        Returns
        -------
        None.

        """
        logger.info("Downloading IDs...")
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
                for playerid in sheetdata.loc[player, 'Unique IDs']:
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
                    self.add_player(player, playerinfo['Region'].values[0], playerinfo['Platform'].values[0], playerinfo['Sheet MMR'].values[0],
                                    playerinfo['Team'].values[0], playerinfo['League'].values[0], int(playerinfo['Discord ID'].values[0]), ids=playerinfo['Unique IDs'].tolist())
                    logger.info(f'{player} added')

            else:  # Player's username is found in db
                doc = self.session.players.find_one({'username': player})
                db_ids = set(doc['info']['id'])
                sheet_ids = set(
                    sheetdata.loc[sheetdata['Username'] == player, 'Unique IDs'].values[0])

                # Check if database ids are a superset of sheet ids
                superset = db_ids.issuperset(sheet_ids)
                if not superset:
                    # Sheet has id(s) that aren't in db, so combine both sets to get updated list
                    ids = sheet_ids.union(db_ids)
                    doc['info']['ids'] = ids
                    self.session.players.update_one(
                        {"username": player}, {"$set": {"info.id": ids}})
                    logger.info(f"{player} ids updated")

        logger.info("Done downloading ids.")

    def check_players(self):
        """
        Compares the rlpc sheet to the database to ensure that all players are present and have accurate info

        Returns
        -------
        None.

        """

        logger.info("Checking players...")
        sheetdata = self.p4sheet.to_df("Players!A1:AG")
        sheetdata['Unique IDs'] = sheetdata['Unique IDs'].map(
            lambda x: x.split(","))
        sheetdata = sheetdata.drop_duplicates(subset='Username')
        sheetdata = sheetdata.loc[sheetdata['Username'] != ""]
        sheetdata = sheetdata.loc[sheetdata['Departed'] == "FALSE"]
        sheetdata = sheetdata.set_index('Username')

        players = self.session.players

        for player in sheetdata.index:
            if sheetdata.loc[player, 'Team'] in ['Not Playing', 'Ineligible', 'Future Star', 'Departed', 'Banned', 'Waitlist', 'Below MMR']:
                # See if player's document exists and/or needs to be updated
                players.find_one_and_update(
                    {'username': player}, {"$set": {"info.team": sheetdata.loc[player, 'Team']}})
                continue

            # Player's username doesn't appear in the database
            if not players.find_one({'username': player}):
                fixed = False

                # Look through ids on the sheet, see if it maches any in the database
                # Any matches indicate a name change
                for playerid in sheetdata.loc[player, 'Unique IDs']:
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
                    playerinfo = sheetdata.loc[player]
                    self.add_player(player, playerinfo['Region'], playerinfo['Platform'], playerinfo['Sheet MMR'],
                                    playerinfo['Team'], playerinfo['League'], playerinfo['Discord ID'], ids=playerinfo['Unique IDs'])
                    logger.info(f'{player} added')

            info = players.find_one({'username': player})['info']
            if info['region'] != sheetdata.loc[player, 'Region']:
                players.update_one({'username': player}, {
                                   "$set": {'info.region': sheetdata.loc[player, 'Region']}})
                logger.info(f"{player} updated")
            if info['platform'] != sheetdata.loc[player, 'Platform']:
                players.update_one({'username': player}, {
                                   "$set": {'info.platform': sheetdata.loc[player, 'Platform']}})
                logger.info(f"{player} updated")
            if info['mmr'] != int(sheetdata.loc[player, 'Sheet MMR']):
                players.update_one({'username': player}, {
                                   "$set": {'info.mmr': int(sheetdata.loc[player, 'Sheet MMR'])}})
                logger.info(f"{player} updated")
            if info['team'] != teamIds[sheetdata.loc[player, 'Team']]:
                players.update_one({'username': player}, {
                                   "$set": {'info.team': teamIds[sheetdata.loc[player, 'Team']]}})
                logger.info(f"{player} updated")
            if info['league'] != sheetdata.loc[player, 'League']:
                players.update_one({'username': player}, {
                                   "$set": {'info.league': sheetdata.loc[player, 'League']}})
                logger.info(f"{player} updated")
            if info['discord_id'] != sheetdata.loc[player, 'Discord ID']:
                players.update_one({'username': player}, {
                                   "$set": {'info.discord_id': sheetdata.loc[player, 'Discord ID']}})
                logger.info(f"{player} updated")

        logger.info("Done checking players.")


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
            team = self.session.teams.find_one({'_id': teamId})['team']

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
                team = teams.loc[teams['Team'] == team_league,
                                 affiliate_columns[choice_league]]

            found_teams.append(team)

        for team in found_teams:
            if found_teams.count(team) > 1:
                return team  # This will return if any two players are on the same team

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

        doc = self.session.teams.find_one({"team": team})
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
        player = sheetdata.loc[sheetdata['Tracker'].str.contains(name.split()[
                                                                 0]), 'Username']
        try:
            return player.values[0]
        except:
            return None

if __name__ == "__main__":
    Identifier().find_team(['SpadL', 'Computer', 'Zero'])