from database import engine, select
import Google_Sheets as sheet
import pandas as pd
from random import choice

def get_fantasy():
    gsheet = sheet.get_google_sheet('1rmJVnfWvVe3tSnFrXpExv4XGbIN3syZO12dGBeoAf-w','Player Info!A1:I')
    players = sheet.gsheet2df(gsheet)
    players[['MMR', 'Fantasy Value', 'Fantasy Points']] = players[['MMR', 'Fantasy Value', 'Fantasy Points']].apply(pd.to_numeric)
    return(players)

def get_database():
    players = select('select * from players')
    return players

def push_sheet_to_sql(): # Temporary
    data = get_fantasy()
    data.to_sql("players", con=engine, if_exists='relpace')

def push_sql_to_sheet():
    data = get_database()
    sheet.df_to_sheet('1rmJVnfWvVe3tSnFrXpExv4XGbIN3syZO12dGBeoAf-w','Player Info!A1:I', data)

def check() -> bool:
    # Returns True if the database matches the sheet
    fantasy = get_fantasy()
    db = get_database()
    check = fantasy == db
    return not False in check.values

def flatten(items, seqtypes=(list, tuple)):
    for i, x in enumerate(items):
        while i < len(items) and isinstance(items[i], seqtypes):
            items[i:i+1] = items[i]
    return items

global players
players = sheet.gsheet2df(sheet.get_google_sheet('1umoAxAcVLkE_XKlpTNNdc42rECU7-GtoDvUhEXja7XA', 'Players!A1:I'))
players['Sheet MMR'] = players['Sheet MMR'].apply(lambda x: int(x))
players['Tracker MMR'] = players['Tracker MMR'].apply(lambda x: int(x))

def add_player(username, region, platform, mmr, team, league, ids=[]):
    data = players.loc[(players['League']==league) & ~(players['Team'].isin(['Not Playing', 'Waitlist', 'Future Star']))].reset_index(drop=True) # Get valid players from correct league
    mmr = int(mmr)
    num_greater = data[data['Tracker MMR'] > mmr]['Tracker MMR'].count()
    num_less = data[data['Tracker MMR'] < mmr]['Tracker MMR'].count()
    percentile = num_less/(num_greater+num_less)
    fantasy_value = round(80 + 100*percentile)
    
    # Now update SQL database
    username = username.replace("'", "''")
    command = f'insert into players ("Username", "Region", "Platform", "MMR", "Team", "League", "Fantasy Value", "Allowed?", "Fantasy Points")'
    values = f"""('{username}', '{region}', '{platform}', {mmr}, '{team}', '{league}', {fantasy_value}, 'Yes', 0)"""
    ids = ids.reset_index(drop=True) # Not really sure why this is needed, but it is

    if len(ids) > 0:
        if ids.values[0] != None:
            ids = "','".join(ids.values[0])
            command = command[:-1] + ', "id")'
            values = values[:-1] + f", array['{ids}'])"
    
    engine.execute(f"{command} values {values}")
    
def update_player(username, region, platform, mmr, team, league):
    pass

def download_ids():
    """
    Takes player IDs from the RLPC Sheet and adds them to the database

    Returns
    -------
    None.

    """
    print('Downloading IDs...')
    gsheet = sheet.get_google_sheet("1umoAxAcVLkE_XKlpTNNdc42rECU7-GtoDvUhEXja7XA", 'Players!A1:AE')
    sheetdata = sheet.gsheet2df(gsheet) 
    sheetdata['Unique IDs'] = sheetdata['Unique IDs'].map(lambda x: x.split(","))
    sheetdata = sheetdata.drop_duplicates(subset='Username')
    sheetdata = sheetdata.loc[sheetdata['Username']!=""]
    
    dbdata = select('players')
    
    for player in sheetdata['Username']:
        if sheetdata.loc[sheetdata['Username']==player, 'Team'].values[0] in ['Not Playing', 'Ineligible', 'Future Star', 'Departed', 'Banned', 'Waitlist']:
            continue
        if player not in dbdata['Username'].values: # If the player isn't in the database at all
            # Check to make sure there are no similar IDs, indicating a name change
            for id in sheetdata.loc[sheetdata['Username']==player, 'Unique IDs']:
                index = len([i for i, s in enumerate(sheetdata['Unique IDs'].values) if id in s])
                if index > 0: # This will be true if the ID already exists
                    # Update player's name
                    engine.execute(f'''update players set "id" = {sheetdata.loc[index, 'Unique IDs']} where "Username" = {sheetdata.loc[index, 'Username']}''')
                    break
            playerinfo = sheetdata.loc[sheetdata['Username']==player]
            add_player(player, playerinfo['Region'].values[0], playerinfo['Platform'].values[0], playerinfo['Sheet MMR'].values[0], playerinfo['Team'].values[0], playerinfo['League'].values[0], ids = playerinfo['Unique IDs'])
            print(f'{player} added')
        elif sheetdata.loc[sheetdata['Username']==player, 'Unique IDs'].values != dbdata.loc[dbdata['Username']==player, 'id'].values:
            try: engine.execute(f"""update players set "id" = array[{str(sheetdata.loc[sheetdata['Username']==player, 'Unique IDs'].values[0])[1:-1]}] where "Username" = '{player}'""")
            except: pass
            print(f"{player} updated")
    print('Done downloading IDs.')

def identify(id: str, players: pd.DataFrame) -> str:
    """
    Determines which player matches a given ID

    Parameters
    ----------
    id : str
        The unique Rocket Leauge ID of any given player.
        
    players:
        Dataframe with all players and IDs, retrieved using select('players').

    Returns
    -------
    str
        The name of the player as spelled on the RLPC Spreadsheet.

    """
    
    for player in players['Username']:
        try:
            if id in players.loc[players['Username']==player, 'id'].values[0]:
                return player
        except: pass
        
def find_team(names: list, players: pd.DataFrame, id_players: bool = False) -> str:
    """
    Determines which team most likely matches a given set of three players

    Parameters
    ----------
    names : list
        List of player names (should be verified as the same on the sheet before using find_team()).
    players : pd.DataFrame
        Dataframe with all players and IDs, retrieved using select('players').
    id_players : bool
        Whether or not this function should identify players first (if given a list of ids rather than names)

    Returns
    -------
    str
        Team name.

    """
        
    if id_players:
        new_names = []
        for id in names:
            name = identify(id, players)
            if name == None:
                continue
            new_names.append(name)
        names = new_names
    
    teams = []
    players = players.set_index('Username')
    for player in names:
        teams.append(players.loc[player, 'Team'])
    
    for team in teams:
        if teams.count(team) > 1:
            return team # This will return if any two players are on the same team
    
    return "Undetermined" # If every player belongs to a different team
                         
def find_league(team: str, players: pd.DataFrame) -> str:
    """
    Finds out what league a team plays in

    Parameters
    ----------
    team : str
        Name of the team.
    players : TYPE, optional
        Dataframe with all player info. Found using select('players').

    Returns
    -------
    str
        Name of the league.

    """
    
    return players.loc[players['Team']==team, 'League'].values[0]

def check_players():
    print("Checking players...")
    players = select('players')
    gsheet = sheet.get_google_sheet("1umoAxAcVLkE_XKlpTNNdc42rECU7-GtoDvUhEXja7XA", 'Players!A1:O')
    sheetdata = sheet.gsheet2df(gsheet)
    sheetdata = sheetdata.drop_duplicates(subset='Username')
    sheetdata = sheetdata.loc[sheetdata['Username']!=""]
    
    # Replace instances of apostrophe
    sheetdata['Username'] = sheetdata['Username'].map(lambda x: x.replace("'", "''"))
    sheetdata = sheetdata.set_index('Username')
    players['Username'] = players['Username'].map(lambda x: x.replace("'", "''"))
    players = players.set_index('Username')
    
    for player in sheetdata.index:
        if sheetdata.loc[player, 'Team'] in ['Not Playing', 'Ineligible', 'Future Star', 'Departed', 'Banned', 'Waitlist']:
            continue
        if player not in players.index: # If they don't appear in the database
            # Check if players IDs are in the database
            sheetdata.loc[player, 'Unique IDs'] = sheetdata.loc[player, 'Unique IDs'].split(',') # Format IDs correctly
            for playerid in sheetdata.loc[player, 'Unique IDs']:
                if playerid in flatten([players.loc[x, 'id'] for x in players.index if players.loc[x, 'id'] != None]):
                    # TODO: Update this in the database
                    break
            add_player(player, sheetdata.loc[player, 'Region'], sheetdata.loc[player, 'Platform'], sheetdata.loc[player, 'Sheet MMR'], sheetdata.loc[player, 'Team'], sheetdata.loc[player, 'League'])            
            print(f'{player} added')
        
        else: # If they do appear in the database, check Region, Platform, MMR, Team, and League
            if sheetdata.loc[player, 'Region'] != players.loc[player, 'Region']:
                engine.execute(f"""update players set "Region" = '{sheetdata.loc[player, 'Region']}' where "Username" = '{player}'""")
                print(f'{player} updated')
            if sheetdata.loc[player, 'Platform'] != players.loc[player, 'Platform']:
                engine.execute(f"""update players set "Platform" = '{sheetdata.loc[player, 'Platform']}' where "Username" = '{player}'""")
                print(f'{player} updated')
            if int(sheetdata.loc[player, 'Sheet MMR']) != players.loc[player, 'MMR']:
                engine.execute(f"""update players set "MMR" = '{sheetdata.loc[player, 'Sheet MMR']}' where "Username" = '{player}'""")
                print(f'{player} updated')
            if sheetdata.loc[player, 'Team'] != players.loc[player, 'Team']:
                engine.execute(f"""update players set "Team" = '{sheetdata.loc[player, 'Team']}' where "Username" = '{player}'""")
                print(f'{player} updated')
            if sheetdata.loc[player, 'League'] != players.loc[player, 'League']:
                engine.execute(f"""update players set "League" = '{sheetdata.loc[player, 'League']}' where "Username" = '{player}'""")
                print(f'{player} updated')
    print("Done checking players.")