import pandas as pd
from datetime import datetime
import pytz
import re
from difflib import SequenceMatcher
import random

from tools.mongo import Session, teamIds

from settings import prefix, leagues
from errors.fantasy_errors import *


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

    def pick_player(self, discord_id: int, player: str) -> str:
        """Adds an RLPC player to a fantasy account

        Args:
            discord_id (str): discord id of the account to which the player is being added
            player (str): Username of the player being picked

        Returns:
            str: Success or error message to send in discord.
        """

        # Ensure that it's a valid time to make transfers
        if datetime.now(tz=pytz.timezone("US/Eastern")).weekday() in [1, 3]:
            if datetime.now(tz=pytz.timezone("US/Eastern")).time().hour > 18:
                raise TimeError()
        elif datetime.now(tz=pytz.timezone("US/Eastern")).weekday() in [2, 4]:
            if datetime.now(tz=pytz.timezone("US/Eastern")).time().hour < 10:
                raise TimeError()

        fantasy = self.session.fantasy
        account: dict = fantasy.find_one({"discord_id": discord_id})
        if not account:
            raise AccountNotFoundError(discord_id)

        # Try to get player (case insensitive), and return if player doesn't exist
        player_info = self.session.players.find_one(
            {'$text': {'$search': f"\"{player}\""}})
        if not player_info:
            raise PlayerNotFoundError(player)

        # Make sure there are less than 5 players
        if len(account['players']) >= 5:
            raise TeamFullError()

        # Make sure the player is allowed to be picked
        if not player_info['fantasy']['allowed']:
            raise IllegalPlayerError(player)

        # Make sure this doesn't exceed salary cap
        new_salary = account['salary'] + \
            player_info['fantasy']['fantasy_value']
        if new_salary > self.SALARY_CAP:
            raise SalaryError(new_salary - self.SALARY_CAP, self.SALARY_CAP, player)

        # Make sure this player isn't already on the fantasy team
        _id = player_info["_id"]
        if _id in account["players"]:
            raise AlreadyPickedError(player)

        # Add player to list
        self.session.fantasy.update_one({'_id': account['_id']}, {
                                        '$push': {'players': player_info['_id']}})

        # Add player to player_history (Even if there's an entry there for this player already)
        history = {
            "Player": player_info['_id'],
            "Date in": datetime.now(tz=pytz.timezone("US/Eastern")),
            "Date out": None,
            "Points": 0,
        }
        self.session.fantasy.update_one({"_id": account['_id']}, {
                                        '$push': {'player_history': history}})

        # Change salary
        self.session.fantasy.update_one({'_id': account['_id']}, {
                                        '$set': {"salary": new_salary}})

        # Add transaction to transaction_log
        transaction = {
            "Timestamp": datetime.now(tz=pytz.timezone("US/Eastern")),
            "Type": "in",
            "Player": {
                "id": player_info['_id'],
                "username": player_info['username'],
                "salary": player_info['fantasy']['fantasy_value'],
            },
        }
        self.session.fantasy.update_one({"_id": account['_id']}, {
                                        '$push': {'transfer_log': transaction}})

        return f'Success! {player} has been added to your team. You have {self.SALARY_CAP - new_salary} left before you reach the salary cap.'

    def drop_player(self, discord_id: str, player: str):
        fantasy = self.session.fantasy
        players = self.session.players

        # Make sure account exists
        account: dict = fantasy.find_one({"discord_id": discord_id})
        if not account:
            raise AccountNotFoundError(discord_id)

        # Make sure there's at least one transaction left
        transfers_left = account['transfers_left']
        if transfers_left < 1:
            raise NoTransactionError()

        # Make sure player is actually on the team
        player_info = self.session.players.find_one(
            {'$text': {'$search': f'\"player\"''}})

        if player_info == None:
            raise PlayerNotFoundError(player)
        elif player_info['_id'] not in account['players']:
            raise IllegalPlayerError(player)
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
                "username": player_info['username'],
                "salary": player_info['fantasy']['fantasy_value'],
                "points": points
            },
        }
        self.session.fantasy.update_one({"_id": account['_id']}, {
                                        '$push': {'transfer_log': transaction}})

        # Update player's info in player_history
        updates = {
            '$set': {
                'player_history.$.Date out': datetime.now(tz=pytz.timezone("US/Eastern"))
            }
        }
        self.session.fantasy.find_one_and_update(
            {'_id': account['_id'], 'player_history.Player': player_info['_id']}, updates)

        # Change salary
        new_salary = account['salary'] - player_info['fantasy']['fantasy_value']
        self.session.fantasy.find_one_and_update(
            {'_id': account['_id']}, {'$set': {'salary': new_salary}})

        # Remove one transaction
        self.session.fantasy.find_one_and_update(
            {'_id': account['_id']}, {'$set': {'transfers_left': transfers_left - 1}})

        return f'Success! {player} has been dropped from your team. You have {self.SALARY_CAP - new_salary} left before you reach the salary cap.'

    def show_team(self, discord_id: str) -> dict:
        """Gets a person's fantasy account for use by the discord bot. This is a useless function.

        Args:
            discord_id (str): player's discord id

        Returns:
            dict: document containing info for player's fantasy account
        """
        doc = self.session.fantasy.find_one({'discord_id': discord_id})
        if doc == None:
            raise AccountNotFoundError(discord_id)
        else:
            return doc

    def info(self, player: str, pg: bool = False) -> dict:
        """Gets info about an RLPC player. This is also a useless function except for pg.

        Args:
            player (str): player's username
            pg (bool, optional): Whether or not to divide points by series played. Defaults to False.

        Returns:
            dict: player info
        """
        doc = self.session.players.find_one(
            {'$text': {'$search': f"\"{player}\""}})
        if not doc:
            raise PlayerNotFoundError(player)

        if pg:
            try:
                doc['fantasy']['fantasy_points'] = round(
                    doc['fantasy']['fantasy_points'] / doc['stats']['general']['Series Played'], 1)
            except:
                pass  # Avoid dividing by zero

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
        if team.lower() in ["all", "none", "no", "idc"]:
            team = "all"
        if team.lower() in ['signed', 'team', 'playing']:
            team = "signed"
        if league.casefold() in ["all", "none", "no", "idc"]:
            league = "all"
        if league.lower() not in ['major', 'aaa', 'aa', 'a', 'independent', 'maverick', 'indy', 'mav', 'all']:
            return("League could not be understood")
        elif league.lower() != "all":
            league = leagues[league.lower()]
        else:
            league = "all"

        filter = {
            "fantasy.fantasy_value": {'$gte': minsalary, '$lte': maxsalary},
            "info.team": {"$nin": ["Not Playing", "Departed"]}
        }

        if league != "all":
            filter['info.league'] = league
        if team != "all" and team != "signed":
            filter['info.team'] = teamIds[team.title()]
        elif team == "signed":
            filter['info.team']['$nin'].append("Free Agent")
            filter['info.team']['$nin'].append("Waitlist") # Shouldn't be in database, but just in case
            filter['info.team']['$nin'].append("Draftee") # Shouldn't be in database, but just in case
        if name != "none":
            filter['username'] = name

        # Get 5 (or fewer) random players from the query
        count = self.session.players.count_documents(filter)
        cursor = self.session.players.find(filter)
        players = []
        if count < 5:
            while cursor.alive:
                players.append(cursor.next())
        else:
            for i in range(5):
                players.append(cursor.skip(
                    round(random.random()*count)).next())
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
                try:
                    stat = round(doc[sortby] / player['stats']
                                 ['Games Played'], 1)
                except:
                    stat = doc[sortby]  # Avoid dividing by 0
            else:
                stat = doc[sortby]

            lb[player['username']] = stat

        lb.sort_values(ascending=False, inplace=True)
        return lb.head(num)
