from tools.database import engine, select

from settings import prefix

def create_account(person: str, league: str = "none") -> None:
    """

    Parameters
    ----------
    person : str
        Name of the account being created (discord username).
    league : str
        Which league the account will be registered under.

    Returns
    -------
    None
        Creates an account for someone who wants to play, and sets their team of 5 all 
        to "Not Picked".

    """
    if league.casefold() not in ["major","aaa","aa","a","independent", "indy", "maverick", "mav", "none"]:
        return f"{league} could not be understood"
    
    if league.casefold() == "indy":
        league = "independent"
    elif league.casefold() == "mav":
        league = "maverick"
    
    if league.casefold() in ["major", "independent", "maverick", "none"]:
        league = league.title()
    else:
        league = league.upper()
    
    players = select("fantasy_players")
    
    player_check = players[players['username']==person].index.values
    
    if len(player_check)!=0:
        return "You already have an account!"
    
    command = "insert into fantasy_players (username, account_league, players, points, transfers_left, salary, total_points)"
    values = f"""values ('{person}', '{league}', '{{Not Picked, Not Picked, Not Picked, Not Picked, Not Picked}}', '{{0, 0, 0, 0, 0}}', 2, 0, 0)"""
    engine.execute(f"{command} {values}")
    
    return f"Success! Your account has been created, with an ID of {person}. To add players, use {prefix}pick" 