import pandas as pd
from datetime import datetime
import pytz
from difflib import SequenceMatcher

from tools.database import engine, select, Session, Fantasy_players, Players, Transfer_log
from tools.sheet import Sheet

from settings import prefix

session = Session().session

def fantasy_lb() -> pd.DataFrame:
    """

    Returns DataFrame
    -------
    Dataframe with all fantasy accounts, sorted by number of points.

    """
    fantasy_players = select("fantasy_players")
    fantasy_players = fantasy_players[['username','total_points']]
    fantasy_players['total_points'] = fantasy_players['total_points'].map(lambda a: int(a))
    lb = fantasy_players.sort_values(by=['total_points'],ascending=False).rename(columns={"total_points": "Total Points", "username": "Username"})
    lb = lb.reset_index(drop=True)
    lb = lb.loc[lb['Total Points'] != 0]
    return(lb)
 
def pick_player(person: str , player: str, slot: int=0) -> str:
    """
    Adds an RLPC player to a fantasy account

    Parameters
    ----------
    person : str
        Name of the account to which the player is being added.
    player : str
        Username (as shown on the sheet) of the player being picked.
    slot : int, optional
        Which player slot to put the player in. The default is 0.

    Returns
    -------
    str
        Either a success message or an error message.

    """
    
    if slot not in [0, 1, 2, 3, 4, 5]:
        return "Please pick a slot between 1 and 5."
    
    # Don't allow transfers if admin table says it's not ready yet
    # admin = select("admin_things").set_index("row_id")
    # if admin.loc[1, 'allow_transfers'] == False:
    #     return "You're not allowed to make transfers right now, probably because there are games currently happening or the previous games have not yet been entered into the database. Please contact arco if you think this is an error."
    
    if datetime.now(tz=pytz.timezone("US/Eastern")).weekday() in [1, 3]:
        if datetime.now(tz=pytz.timezone("US/Eastern")).time().hour > 16:
            return "You're not allowed to make transfers right now, probably because there are games currently happening or the previous games have not yet been entered into the database. Please contact arco if you think this is an error."
    elif datetime.now(tz=pytz.timezone("US/Eastern")).weekday() in [2, 4]:
        if datetime.now(tz=pytz.timezone("US/Eastern")).time().hour < 10:
            return "You're not allowed to make transfers right now, probably because there are games currently happening or the previous games have not yet been entered into the database. Please contact arco if you think this is an error."
    
    # Get dataframes with all the player and fantasy data in them
    fantasy_players = select("fantasy_players").set_index('username')
    rlpc_players = select("players")
    lower_players = rlpc_players['Username'].str.lower()
    
    row = session.query(Fantasy_players).get(person)
    if row == None:
        return(f"You don't currently have an account! Use {prefix}new to make an account")
    
    if slot == 0:
        if fantasy_players.loc[person, "players"][0] == "Not Picked":
            slot = 1
        elif fantasy_players.loc[person, "players"][1] == "Not Picked":
            slot = 2
        elif fantasy_players.loc[person, "players"][2] == "Not Picked":
            slot = 3
        elif fantasy_players.loc[person, "players"][3] == "Not Picked":
            slot = 4
        elif fantasy_players.loc[person, "players"][4] == "Not Picked":
            slot = 5
        else: return("Please pick a slot to replace, your team is full")
    
    # If "None" is chosen, drop the player in the selected slot
    drop = False
    if player.casefold() in ["none","not picked","nobody","drop","empty"]:
        drop = True
    
    # Make it not case sensitive, and return if the player doesn't exist
    if player.casefold() in lower_players.values and drop == False:
        pindex = lower_players[lower_players == player.casefold()].index[0]
        player = rlpc_players.loc[pindex][0]
    elif drop == False:
        return("That player couldn't be found in the database. Make sure you spelled their name correctly")
    
    account_check = fantasy_players.loc[person].index
    current_occupant = fantasy_players.loc[person,"players"][slot-1]
    
    if drop == False:
        player_check = rlpc_players[rlpc_players['Username']==player]
        permission_check = rlpc_players.loc[rlpc_players['Username']==player,'Allowed?'].values
        cap_check = rlpc_players.loc[rlpc_players['Username']==player,'Fantasy Value'].values
        cap_check = int(cap_check) + int(fantasy_players.loc[person,'salary'])
    elif drop == True:
        player_check = []
        permission_check = "Yes"
        cap_check = 0
    
    # Check if this is a transfer
    transfer = False
    transfers_left = 0
    if current_occupant != "Not Picked":
        transfer = True
        transfers_left = fantasy_players.loc[person,'transfers_left']
        transfers_left = int(transfers_left)
        
    if (transfer == True or drop == True) and transfers_left == 0:
        return("You have already used your two transfers for this week!")
    
    # Check to make sure the account exists, the specified player exists, and they are allowed to be picked
    if len(account_check) == 0:
        return("You don't currently have an account! Use {prefix}new to create an account")
    else:
        pass
    
    if len(player_check) == 0 and drop != True:
        return("That player isn't in the database! Make sure to enter the name exactly as spelled on the sheet. If you think this is an error, please contact @arco.")
    else:
        pass
    
    if permission_check != "Yes" and drop != True:
        return("This player has requested to be excluded from the fantasy league")
    else:
        pass
    
    # Check to make sure this player isn't already on the fantasy team
    existing_check = fantasy_players.loc[person, "players"]
    if player in existing_check:
        return("You already have this player on your team!")
    else:
        pass
    
    # Check to make sure it doesn't break the salary cap
    salary_cap = 700
    if cap_check > salary_cap and transfer == False:
        return(f"This player would cause you to exceed the salary cap of {salary_cap}. Please choose a different player, or drop a player by picking 'None' in the desired slot")
    elif transfer == True:
        old_player_salary = rlpc_players.loc[rlpc_players['Username']==current_occupant,'Fantasy Value'].values[0]
        cap_check = cap_check - int(old_player_salary)
        if cap_check > salary_cap:
            return(f"This player would cause you to exceed the salary cap of {salary_cap}.")
    
    if transfer == True and transfers_left > 0:
        row.transfers_left = (transfers_left - 1)
        # engine.execute(f"update fantasy_players set transfers_left = {transfers_left - 1} where username = '{person}'")
    
    # Log the changes just in case
    timestamp = str(datetime.now())
    player_in = player
    if drop == True:
        player_in = "DROP"
        player_out = current_occupant
    else:
        player_out = current_occupant    
    # command = """insert into transfer_log ("Timestamp", "Account", "Player_in", "Player_out")"""
    # values = f"values ('{timestamp}', '{person}', '{player_in}', '{player_out}')"
    # engine.execute(f"{command} {values}")
    session.add(Transfer_log(timestamp, person, player_in, player_out))
    
    if drop == True:
        # engine.execute(f"""update fantasy_players set players[{slot}] = 'Not Picked' where "username" = '{person}'""")
        row.players[slot] = "Not Picked"
        new_salary = fantasy_players.loc[person, 'salary'] - rlpc_players.loc[rlpc_players['Username']==player_out,'Fantasy Value'].values[0]
        # engine.execute(f"""update fantasy_players set "salary" = {new_salary} where "username" = '{person}'""")
        row.salary = new_salary
        return(f'You have dropped {current_occupant}')
    else:
        row.players[slot] = player
        row.salary = cap_check
        # engine.execute(f"""update fantasy_players set players[{slot}] = '{player}' where "username" = '{person}'""")
        # engine.execute(f"""update fantasy_players set "salary" = {cap_check} where "username" = '{person}'""")
    
    session.commit()
    
    # Check to make sure the player isn't in the same league as the account
    # if rlpc_players.loc[rlpc_players['Username']==player,'League'].values[0] == fantasy_players.loc[fantasy_players['Username']==person,'Account League'].values[0]:
    #     return("You must select a player in a league other than your own")
    # else:
    #     pass
    
    # Check to make sure the specified slot is empty, otherwise say a player was replaced
    if current_occupant == "Not Picked":
        return(f'Success! {player} has been added to your team')
    elif current_occupant != "Not Picked":
        return(f'Success! {current_occupant} has been replaced with {player}')
    else:
        return(f"You already have {fantasy_players.loc[person,'players'][slot-1]} in this slot. They have been replaced by {player}.")
    
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