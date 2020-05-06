from database import engine, select
import Google_Sheets as sheet
import pandas as pd

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
    data.to_sql("players", con=engine, if_exists = 'relpace')

def push_sql_to_sheet():
    data = get_database()
    sheet.df_to_sheet('1rmJVnfWvVe3tSnFrXpExv4XGbIN3syZO12dGBeoAf-w','Player Info!A1:I', data)

def check() -> bool:
    # Returns True if the database matches the sheet
    fantasy = get_fantasy()
    db = get_database()
    check = fantasy == db
    return not False in check.values

def add_player(username, region, platform, mmr, team, league):
    fantasy_value = 100 # TODO: Create new Fantasy Value Formula
    row = get_database().shape[0]+2
    fantasy_value_formula = f"=if(isblank(A{row}) = False,round(100+100*PERCENTRANK(FILTER($D$2:$D,$F$2:$F=F{row}),D{row},2)-percentrank(FILTER('Player Info'!D$2:D,'Player Info'!E$2:E=FILTER('Player Info'!E$2:E,'Player Info'!A$2:A=A{row})),FILTER('Player Info'!D$2:D,'Player Info'!A$2:A=A{row}))*10),"")"
    # Update google sheet first
    values = [[username], [region], [platform], [mmr], [team], [league], [fantasy_value_formula], ["Yes"], [0]]
    body = {"majorDimension": "COLUMNS", 'values': values}
    sheet.append_data('1rmJVnfWvVe3tSnFrXpExv4XGbIN3syZO12dGBeoAf-w','A1:I', body)
    
    # Now update SQL database
    command = f'insert into players ("Username", "Region", "Platform", "MMR", "Team", "League", "Fantasy Value", "Allowed?", "Fantasy Points")'
    values = f"('{username}', '{region}', '{platform}', {mmr}, '{team}', '{league}', {fantasy_value}, 'Yes', 0)"
    
    engine.execute(f"{command} values {values}")
    
def update_player(username, region, platform, mmr, team, league):
    pass