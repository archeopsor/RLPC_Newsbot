import pandas as pd
from datetime import datetime
import pytz
import re
from difflib import SequenceMatcher
import random

from tools.mongo import Session, teamIds

from settings import prefix, leagues


class FantasyHandler:
    def __init__(self, session: Session = None):
        if not session:
            self.session = Session()
        else:
            self.session = session

        self.SALARY_CAP = 700

    def fantasy_lb(self) -> pd.Series:
        """Gets a sorted series with all fantasy accounts and their points

        Returns:
            pd.Series: Series with username as index and points as value
        """
        fantasy = self.session.fantasy
        lb = pd.Series(dtype="float64")
        cursor = fantasy.find({"points": {"$gt": 0}}).sort(
            "points", -1)  # Get all accounts with more than 0 points

        for i in range(fantasy.count_documents({"points": {"$gt": 0}})):
            info = cursor.next()
            lb[info['username']] = info['points']

        return lb

    def pick_player(self, discord_id: str, player: str) -> str:
        """Adds an RLPC player to a fantasy account

        Args:
            discord_id (str): discord id of the account to which the player is being added
            player (str): Username of the player being picked

        Returns:
            str: Success or error message to send in discord.
        """

        # Ensure that it's a valid time to make transfers
        if datetime.now(tz=pytz.timezone("US/Eastern")).weekday() in [1, 3]:
            if datetime.now(tz=pytz.timezone("US/Eastern")).time().hour > 16:
                return "You're not allowed to make transfers right now, probably because there are games currently happening or the previous games have not yet been entered into the database. Please contact arco if you think this is an error."
        elif datetime.now(tz=pytz.timezone("US/Eastern")).weekday() in [2, 4]:
            if datetime.now(tz=pytz.timezone("US/Eastern")).time().hour < 10:
                return "You're not allowed to make transfers right now, probably because there are games currently happening or the previous games have not yet been entered into the database. Please contact arco if you think this is an error."

        fantasy = self.session.fantasy
        players = self.session.players
        account: dict = fantasy.find_one({"discord_id": discord_id})
        if not account:
            return f"You don't currently have an account! Use {prefix}new to make an account"

        # Try to get player (case insensitive), and return if player doesn't exist
        player_info = self.session.players.find_one(
            {'$text': {'$search': player}})
        if not player_info:
            return "That player couldn't be found in the database. Make sure you spelled their name correctly"

        # Make sure there are less than 5 players
        if len(account['players']) >= 5:
            return "You already have 5 players on your team. Please drop someone before picking your next player"

        # Make sure the player is allowed to be picked
        if not player_info['fantasy']['allowed']:
            return "This player is not available to be picked."

        # Make sure this doesn't exceed salary cap
        new_salary = account['salary'] + \
            player_info['fantasy']['fantasy_value']
        if new_salary > self.SALARY_CAP:
            return f"This player would cause you to exceed the salary cap of {self.SALARY_CAP}. Please choose a different player, or drop someone on your team."

        # Make sure this player isn't already on the fantasy team
        _id = player_info["_id"]
        if _id in account["players"]:
            return "You already have this player on your team!"

        # Add player to list
        self.session.fantasy.update_one({'_id': account['_id']}, {
                                        '$push': {'players': player_info['_id']}})

        # Add player to player_history (Even if there's an entry there for this player already)
        history = {
            "Player": player_info['_id'],
            "Date in": datetime.now(tz=pytz.timezone("US/Eastern")).date(),
            "Date out": None,
            "Points": 0,
        }
        self.session.fantasy.update_one({"_id": account['_id']}, {
                                        '$push': {'player_history': history}})

        # Add transaction to transaction_log
        transaction = {
            "Timestamp": datetime.now(tz=pytz.timezone("US/Eastern")),
            "Type": "in",
            "Player": {
                "id": player_info['_id'],
                "salary": player_info['fantasy']['salary'],
            },
        }
        self.session.fantasy.update_one({"_id": account['_id']}, {
                                        '$push': {'transfer_log': transaction}})

        # Change salary
        self.session.fantasy.update_one({'_id': account['_id']}, {
                                        '$set': {"salary": new_salary}})

        return f'Success! {player} has been added to your team. You have {self.SALARY_CAP - new_salary} left before you reach the salary cap.'

    def drop_player(self, discord_id: str, player: str):
        fantasy = self.session.fantasy
        players = self.session.players

        # Make sure account exists
        account: dict = fantasy.find_one({"discord_id": discord_id})
        if not account:
            return f"You don't currently have an account! Use {prefix}new to make an account"

        # Make sure player is actually on the team
        player_info = self.session.players.find_one(
            {'$text': {'$search': player}})
        if player_info['_id'] not in account['players']:
            return f"{player} isn't on your team!"
        else:
            points = [x for x in account['player_history']
                      if x['Player'] == player_info['_id']][-1]['Points']

        # Remove player from list
        self.session.fantasy.update_one({'_id': account['_id']}, {
                                        '$pull': {'players': player_info['_id']}})

        # Add transaction to transaction_log
        transaction = {
            "Timestamp": datetime.now(tz=pytz.timezone("US/Eastern")),
            "Type": "out",
            "Player": {
                "id": player_info['_id'],
                "salary": player_info['fantasy']['salary'],
                "points": points
            },
        }
        self.session.fantasy.update_one({"_id": account['_id']}, {
                                        '$push': {'transfer_log': transaction}})

        # Update player's info in player_history
        updates = {
            '$set': {
                'player_history.Date out': datetime.now(tz=pytz.timezone("US/Eastern")).date()
            }
        }
        self.session.fantasy.find_one_and_update(
            {'_id': account['_id'], 'player_history.Player': player_info['_id']}, updates)

        # Change salary
        new_salary = self.SALARY_CAP - player_info['fantasy']['fantasy_value']
        self.session.fantasy.find_one_and_update(
            {'_id': account['_id']}, {'$set': {'salary': new_salary}})

        return f'Success! {player} has been dropped from your team. You have {self.SALARY_CAP - new_salary} left before you reach the salary cap.'

    def show_team(self, discord_id: str) -> dict:
        """Gets a person's fantasy account for use by the discord bot. This is a useless function.

        Args:
            discord_id (str): player's discord id

        Returns:
            dict: document containing info for player's fantasy account
        """
        doc = self.session.fantasy.find_one({'discord_id': discord_id})
        return doc

    def info(self, player: str, pg: bool = False) -> dict:
        """Gets info about an RLPC player. This is also a useless function except for pg.

        Args:
            player (str): player's username
            pg (bool, optional): Whether or not to divide points by series played. Defaults to False.

        Returns:
            dict: player info
        """
        doc = self.session.players.find_one({'$text': {'$search': player}})
        if not doc:
            return

        if pg:
            doc['fantasy']['fantasy_points'] = round(
                doc['fantasy']['fantasy_points'] / doc['stats']['general']['Series Played'], 1)

        return doc

    def search(self, minsalary: int = 0, maxsalary: int = 800, league: str = "all", team: str = "all", name: str = "none", maxdistance: float = 0.75) -> list:
        """Returns up to 5 players matching a set of parameters

        Args:
            minsalary (int, optional): Minimum Salary. Defaults to 0.
            maxsalary (int, optional): Maximum Salary. Defaults to 800.
            league (str, optional): Which league, if any, to limit to. Defaults to "all".
            team (str, optional): Which team, if any, to limit to. Defaults to "all".
            name (str, optional): Looking for a specific name. Defaults to "none".
            maxdistance (float, optional): How close the name needs to be to the specified name. Defaults to 0.75.

        Returns:
            list: List of dictionaries with player information
        """
        if team.casefold() in ["all", "none", "no", "idc"]:
            team = "all"
        if league.casefold() in ["all", "none", "no", "idc"]:
            league = "all"
        if league.casefold() not in ['major', 'aaa', 'aa', 'a', 'independent', 'maverick', 'indy', 'mav', 'all']:
            return("League could not be understood")
        else:
            league = leagues[league.lower()]

        filter = {
            "fantasy.fantasy_value": {'$gte': minsalary, '$lte': maxsalary}
        }

        if league != "all":
            filter['info.league'] = league
        if team != "all":
            filter['info.team'] = teamIds[team.title()]
        if name != "none":
            filter['username'] = name

        # Get 5 (or fewer) random players from the query
        count = self.session.players.count_documents(filter)
        cursor = self.session.players.find(filter)
        players = []
        for i in range(5 if count >= 5 else count):
            players.append(cursor.skip(round(random.random()*count)).next())
            cursor.rewind()

        return players

    def player_lb(self, league: str = None, sortby: str = "fantasy_points", num: int = 10, pergame: bool = False) -> pd.Series:
        """Returns rlpc players sorted by a stat, usually fantasy points

        Args:
            league (str, optional): Which league to include players from.. Defaults to None.
            sortby (str, optional): Which field to sort by. Defaults to "fantasy_points".
            num (int, optional): How many players to return. Defaults to 10.
            pergame (bool, optional): Whether to divide by the number of games played. Defaults to False.

        Returns:
            pd.Series: Sorted series with Username: value pairs.
        """
        filter = {}
        if league:
            filter['info.league'] = leagues[league.lower()]

        players = self.session.players.find(filter)
        count = self.session.players.count_documents(filter)
        lb = pd.Series(dtype="float64")
        for i in range(count):
            player = players.next()

            if sortby.lower() in ['fantasy_points', 'fantasy points']:
                doc = player['fantasy']
            else:
                doc = player['stats']

            if pergame:
                stat = round(doc[sortby] / player['stats']['Games Played'], 1)
            else:
                stat = doc[sortby]

            lb[player['username']] = stat

        lb.sort_values(ascending=False, inplace=True)
        return lb.head(num)
