from tools.mongo import Session

from settings import prefix, leagues

def create_account(username: str, discord_id: str, league: str = None) -> str:
    """

    Parameters
    ----------
    username : str
        Name of the account being created (discord username).
    discord_id : str
        Discord Id for the account.
    league : str
        Which league the account will be registered under.

    Returns
    -------
    str
        Creates an account for someone who wants to play, and sets their team of 5 all 
        to "Not Picked".

    """
    if league:
        league = leagues[league.lower()]
    
    with Session() as session:
        if session.fantasy.find_one({'discord_id': discord_id}):
            return "You already have an account!"
        else:
            doc = session.structures['fantasy']
            doc['username'] = username
            doc['discord_id'] = username
            if league:
                doc['account_league'] = league

            session.fantasy.insert_one(doc)

            return f"Success! Your account has been created. To add players, use {prefix}pick." 

        