import pandas as pd

from tools.database import engine, select
from tools import sheet

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
    items = [i for i in items if i != '']
    return items


global teams
teams = sheet.gsheet2df(sheet.get_google_sheet('1AJoBYkYGMIrpe8HkkJcB25DbLP2Z-eV7P6Tk9R6265I', 'Teams!F1:P129'))


def add_player(username, region, platform, mmr, team, league, ids=[]):
    players = sheet.gsheet2df(sheet.get_google_sheet('1AJoBYkYGMIrpe8HkkJcB25DbLP2Z-eV7P6Tk9R6265I', 'Players!A1:W'))
    players['Sheet MMR'] = players['Sheet MMR'].apply(lambda x: int(x) if x != '' else x)
    players['Tracker MMR'] = players['Tracker MMR'].apply(lambda x: int(x) if x != '' else x)
    data = players.loc[(players['League']==league) & ~(players['Team'].isin(['Not Playing', 'Waitlist', 'Future Star']))].reset_index(drop=True) # Get valid players from correct league
    mmr = int(mmr)
    num_greater = data[data['Tracker MMR'] > mmr]['Tracker MMR'].count()
    num_less = data[data['Tracker MMR'] < mmr]['Tracker MMR'].count()
    percentile = num_less/(num_greater+num_less)
    fantasy_value = round(80 + 100*percentile)
    
    # Now update SQL database
    username = username.replace("'", "''")
    command = 'insert into players ("Username", "Region", "Platform", "MMR", "Team", "League", "Fantasy Value", "Allowed?", "Fantasy Points")'
    values = f"""('{username}', '{region}', '{platform}', {mmr}, '{team}', '{league}', {fantasy_value}, 'Yes', 0)"""
    try:
        ids = ids.reset_index(drop=True) # Not really sure why this is needed, but it is
    except:
        pass

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
    gsheet = sheet.get_google_sheet("1AJoBYkYGMIrpe8HkkJcB25DbLP2Z-eV7P6Tk9R6265I", 'Players!A1:AE')
    sheetdata = sheet.gsheet2df(gsheet) 
    sheetdata['Unique IDs'] = sheetdata['Unique IDs'].map(lambda x: x.split(","))
    sheetdata = sheetdata.drop_duplicates(subset='Username')
    sheetdata = sheetdata.loc[sheetdata['Username']!=""]
    
    dbdata = select('players')
    
    for player in sheetdata['Username']:
        if sheetdata.loc[sheetdata['Username']==player, 'Team'].values[0] in ['Not Playing', 'Ineligible', 'Future Star', 'Departed', 'Banned', 'Waitlist']:
            continue
        try:
            superset = set(dbdata.loc[dbdata['Username']==player, 'id'].values[0]).issuperset(set(sheetdata.loc[sheetdata['Username']==player, 'Unique IDs'].values[0]))
        except:
            print(player)
            continue
        if player not in dbdata['Username'].values: # If the player isn't in the database at all
            fixed = False
            # Check to make sure there are no similar IDs, indicating a name change
            for playerid in sheetdata.loc[player, 'Unique IDs']:
                if playerid == '':
                    continue
                if playerid in flatten([dbdata.loc[x, 'id'] for x in dbdata.index if dbdata.loc[x, 'id'] != None]):
                    for index in dbdata.index:
                        if playerid in dbdata.loc[index, 'id']: # Change player's name in database if true
                            username = dbdata.loc[index, 'Username']
                            engine.execute(f"""update players set "Username" = '{username}' where '{playerid}' = any("id")""")
                            print(f'{player} has changed their name to {username}')
                            fixed = True
            if not fixed:
                playerinfo = sheetdata.loc[sheetdata['Username']==player]
                add_player(player, playerinfo['Region'].values[0], playerinfo['Platform'].values[0], playerinfo['Sheet MMR'].values[0], playerinfo['Team'].values[0], playerinfo['League'].values[0], ids = playerinfo['Unique IDs'])
                print(f'{player} added')
        elif not superset:
            # Above is false if database contains all ids on sheet
            sheet_ids = set(sheetdata.loc[sheetdata['Username']==player, 'Unique IDs'].values[0])
            db_ids = set(dbdata.loc[dbdata['Username']==player, 'id'].values[0])
            ids = sheet_ids.union(db_ids)
            try:
                engine.execute(f"""update players set "id" = array[{str(ids)[1:-1]}] where "Username" = '{player}'""")
            except:
                pass
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
        
def find_team(names: list, players: pd.DataFrame, id_players: bool = False, choices: list = None) -> str:
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
            name = identify(id, players)
            if name == None:
                continue
            new_names.append(name)
        names = new_names
    
    found_teams = []
    players = players.set_index('Username')
    for player in names:
        
        team = players.loc[player, 'Team']
        
        if choices != None:
            choice_league = find_league(choices[0], players.reset_index())
            team_league = find_league(team, players.reset_index())
            affiliate_columns = {'Major': 'Major Affiliate', 'AAA': 'AAA Affiliate', 'AA': 'AA Affiliate', 'A': 'A Affiliate', 'Independent': 'Major Affiliate', 'Maverick': 'AAA Affiliate', 'Renegade': 'AA Affiliate', 'Paladin': 'A Affiliate'}
            team = teams.loc[teams["Team"]==team_league, affiliate_columns[choice_league]]
        
        teams.append(team)
    
    for team in found_teams:
        if found_teams.count(team) > 1:
            
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
    gsheet = sheet.get_google_sheet("1AJoBYkYGMIrpe8HkkJcB25DbLP2Z-eV7P6Tk9R6265I", 'Players!A1:W')
    sheetdata = sheet.gsheet2df(gsheet)
    sheetdata['Unique IDs'] = sheetdata['Unique IDs'].map(lambda x: x.split(","))
    sheetdata = sheetdata.drop_duplicates(subset='Username')
    sheetdata = sheetdata.loc[sheetdata['Username']!=""]
    
    # Replace instances of apostrophe
    sheetdata['Username'] = sheetdata['Username'].map(lambda x: x.replace("'", "''"))
    sheetdata = sheetdata.set_index('Username')
    players['Username'] = players['Username'].map(lambda x: x.replace("'", "''"))
    players = players.set_index('Username')
    
    for player in sheetdata.index:
        if sheetdata.loc[player, 'Team'] in ['Not Playing', 'Ineligible', 'Future Star', 'Departed', 'Banned', 'Waitlist']:
            try:
                if players.loc[player, 'Team'] != sheetdata.loc[player, 'Team']:
                    engine.execute(f"""update players set "Team" = '{sheetdata.loc[player, 'Team']}' where "Username" = '{player}'""")
            except:
                pass
            continue
        if player not in players.index: # If they don't appear in the database
            fixed = False
            # Check if players IDs are in the database
            for playerid in sheetdata.loc[player, 'Unique IDs']:
                if playerid == '':
                    continue
                if playerid in flatten([players.loc[x, 'id'] for x in players.index if players.loc[x, 'id'] != None]):
                    for username in players.index:
                        if playerid in players.loc[username, 'id']: # Change player's name in database
                            change_name(username, player, playerid)
                            print(f'{username} has changed their name to {player}')
                            fixed = True
                            break
                    break
            if not fixed:
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
    
def change_name(old, new, playerid):
    # Change name in players database
    engine.execute(f"""update players set "Username" = '{new}' where '{playerid}' = any("id")""")
    
    # Change name on fantasy teams
    engine.execute(f"""update fantasy_players set players = array_replace("players", '{old}', '{new}')""")
    
def tracker_identify(name):
    sheetdata = sheet.gsheet2df(sheet.get_google_sheet('1AJoBYkYGMIrpe8HkkJcB25DbLP2Z-eV7P6Tk9R6265I', 'Players!A1:AE'))
    player = sheetdata.loc[sheetdata['Tracker'].str.contains(name.split()[0]), 'Username']
    try:
        player = player.values[0]
        return player
    except:
        return None