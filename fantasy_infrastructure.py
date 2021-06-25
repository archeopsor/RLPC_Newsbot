import pandas as pd
from datetime import datetime
import pytz
import re
from difflib import SequenceMatcher

#from tools.database import engine, select, Session, Fantasy_players, Players, Transfer_log
from tools.mongo import Session, ObjectId

from settings import prefix


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
        cursor = fantasy.find({"points": {"$gt": 0}}).sort("points", -1) # Get all accounts with more than 0 points

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
        player_info = self.session.players.find_one({'username': re.compile("^"+re.escape(player)+"$", re.IGNORECASE)})
        if not player_info:
            return "That player couldn't be found in the database. Make sure you spelled their name correctly"

        # Make sure there are less than 5 players
        if len(account['players']) >= 5:
            return "You already have 5 players on your team. Please drop someone before picking your next player"

        # Make sure the player is allowed to be picked
        if not player_info['fantasy']['allowed']:
            return "This player is not available to be picked."

        # Make sure this doesn't exceed salary cap
        new_salary = account['salary'] + player_info['fantasy']['fantasy_value']
        if new_salary > self.SALARY_CAP:
            return f"This player would cause you to exceed the salary cap of {self.SALARY_CAP}. Please choose a different player, or drop someone on your team."

        # Make sure this player isn't already on the fantasy team
        _id = player_info["_id"]
        if _id in account["players"]:
            return "You already have this player on your team!"

        # Add player to list
        self.session.fantasy.update_one({'_id': account['_id']}, {'$push': {'players': player_info['_id']}})
    
        # Add player to player_history (Even if there's an entry there for this player already)
        history = {
            "Player": player_info['_id'],    
            "Date in": datetime.now(tz=pytz.timezone("US/Eastern")).date(),
            "Date out": None,
            "Points": 0,
        }
        self.session.fantasy.update_one({"_id": account['_id']}, {'$push': {'player_history': history}})

        # Add transaction to transaction_log
        transaction = {
            "Timestamp": datetime.now(tz=pytz.timezone("US/Eastern")),
            "Type": "in", 
            "Player": {
                "id": player_info['_id'],
                "salary": player_info['fantasy']['salary'],
            },
        }
        self.session.fantasy.update_one({"_id": account['_id']}, {'$push': {'transfer_log': transaction}})
        
        # Change salary
        self.session.fantasy.update_one({'_id': account['_id']}, {'$set': {"salary": new_salary}})

        return f'Success! {player} has been added to your team. You have {self.SALARY_CAP - new_salary} left before you reach the salary cap.'

    def drop_player(self, discord_id: str, player: str):
        fantasy = self.session.fantasy
        players = self.session.players

        # Make sure account exists
        account: dict = fantasy.find_one({"discord_id": discord_id})
        if not account: 
            return f"You don't currently have an account! Use {prefix}new to make an account"

        # Make sure player is actually on the team
        player_info = self.session.players.find_one({'username': re.compile("^"+re.escape(player)+"$", re.IGNORECASE)})
        if player_info['_id'] not in account['players']:
            return f"{player} isn't on your team!"
        else:
            points = [x for x in account['player_history'] if x['Player'] == player_info['_id']][-1]['Points']

        # Remove player from list
        self.session.fantasy.update_one({'_id': account['_id']}, {'$pull': {'players': player_info['_id']}})

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
        self.session.fantasy.update_one({"_id": account['_id']}, {'$push': {'transfer_log': transaction}})

        # Update player's info in player_history
        updates = {
            '$set': {
                'player_history.Date out': datetime.now(tz=pytz.timezone("US/Eastern")).date()
            }
        }
        self.session.fantasy.find_one_and_update({'_id': account['_id'], 'player_history.Player': player_info['_id']}, updates)

        # Change salary
        new_salary = self.SALARY_CAP - player_info['fantasy']['fantasy_value']
        self.session.fantasy.find_one_and_update({'_id': account['_id']}, {'$set': {'salary': new_salary}})

        return f'Success! {player} has been dropped from your team. You have {self.SALARY_CAP - new_salary} left before you reach the salary cap.'

    
# Display a player's team
def show_team(person: str) -> pd.Series:
    """
    Gets a person's fantasy team

    Parameters
    ----------
    person : str
        Name of the person's account (discord username).

    Returns
    -------
    Series containing info about the person's team, for use by the discord bot.

    """
    fantasy_teams = select("fantasy_players")
    fantasy_teams['username'] = fantasy_teams['username'].str.upper()
    person = person.upper()
    fantasy_teams = fantasy_teams.set_index("username")
    return(fantasy_teams.loc[person])

def info(player: str, pg: bool = False) -> pd.Series:
    """
    Gets info about an RLPC player

    Parameters
    ----------
    player : str
        The player's name.

    Returns
    -------
    Series containing info about the player, for use by the discord bot.

    """
    players = select("players")
    lower_players = players['Username'].str.lower()
    if player.casefold() in lower_players.values:
        pindex = lower_players[lower_players == player.casefold()].index[0]
        player = players.loc[pindex][0]
    for row in players.index:
        players.loc[row,'Username'] = players.loc[row,'Username'].upper()
    if pg:
        players['Fantasy Points'] = round(players['Fantasy Points']/players['Series Played'], 1).fillna(value=0)
    player = player.upper()
    players = players.set_index("Username")
    return(players.loc[player])

def search(minsalary: int=0, maxsalary: int=800, league: str="all", team: str="all", name: str="none", maxdistance: float=0.75) -> pd.DataFrame:
    """
    Searches through all RLPC players to find five that meet the specified parameters

    Parameters
    ----------
    minsalary : int, optional
        Minimum desired salary. The default is 0.
    maxsalary : int, optional
        Maximum desired salary. The default is 800.
    league : str, optional
        Specified desired league. The default is "all".
    team : str, optional
        Specified desired team. The default is "all".
    name : str, optional
        Approximate name of the player. The default is "none".
    maxdistance : float, optional
        How specific the name parameter should be. The default is 0.75.

    Returns
    -------
    Dataframe with info for five players meeting all of those parameters.

    """
    players = select("players")
    players = players.sort_values(by='Username')
    players = players.reset_index(drop=True)
    
    if team.casefold() in ["all","none","no","idc"]:
        team = "all"
    if league.casefold() in ["all","none","no","idc"]:
        league = "all"
    if league.casefold() not in ['major','aaa','aa','a','independent', 'maverick', 'indy', 'mav', 'all']:
        return("League could not be understood")
    if league.casefold() == "indy":
        league = "Independent"
    elif league.casefold() == "mav":
        league = "Maverick"
    elif league.casefold() in ['major', 'independent', 'maverick']:
        league = league.title()
    elif league.casefold() in ['aaa','aa','a']:
        league = league.upper()
    
    for row in players.index:
        salary = int(players.loc[row,'Fantasy Value'])
        players.loc[row,'Fantasy Value'] = salary
    
    players = players.loc[players['Fantasy Value'] >= minsalary]
    players = players.loc[players['Fantasy Value'] <= maxsalary]
    if league != "all":
        players = players.loc[players['League'].str.lower() == league.casefold()]
    if team != "all":
        players = players.loc[players['Team'].str.lower() == team.casefold()]
        
    if len(players.index) == 0:
        return("There were no players that matched those parameters")
    
    if name == "none":
        if len(players.index) > 4:
            return(players.sample(5))
        else:
            num = len(players.index)
            return(players.sample(num))
    
    # Search names by assigning an editdistance value 
    players['editdistance'] = 0
    for row in players.index:
        username = players.loc[row,'Username']
        username = username.casefold()
        name = name.casefold()
        distance = SequenceMatcher(a=name, b=username).ratio()
        length = abs(len(name)-len(username))
        players.loc[row,'editdistance'] = (distance-length)/2
    
    if name != "none":
        players = players.sort_values(by='editdistance', ascending=False)
        players = players.loc[players['editdistance'] <= maxdistance]
        players = players.drop('editdistance',axis=1)
        return(players.head(5))
    
def player_lb(league: str = None, sortby: str="Fantasy Points", num: int=10, pergame: bool=False) -> pd.DataFrame:
    """
    Sorts the list of rlpc players

    Parameters
    ----------
    league : str, optional
        Which league to include players from. The default is None.
    sortby : str, optional
        Which column to sort by. The default is "Fantasy Points".
    num : int, optional
        How many players to return. The default is 10.

    Returns
    -------
    Sorted dataframe of RLPC players.

    """
    players = select("players").set_index("Username")
    
    if league != None:
        players = players[players['League'].str.lower() == league.casefold()]
    
    if pergame:
        players['Fantasy Points'] = round(players['Fantasy Points']/players['Series Played'], 1).fillna(value=0)
    lb = players['Fantasy Points'].sort_values(ascending=False)
        
    return lb.head(num)