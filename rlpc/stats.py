import pandas as pd

from tools import sheet
from tools.database import select

from settings import valid_stats, leagues

sheet_id = "1AJoBYkYGMIrpe8HkkJcB25DbLP2Z-eV7P6Tk9R6265I"

def get_player_stats(player,stat="all"):
    # Make sure the program understands the specified stat if it's mis-capitalized or whatever
    if stat.lower() in ["sp","series","series_played","series-played","splayed","seris","sieries","seiries"]:
        stat = "Series Played"
    elif stat.lower() in ["gp","games","games_played","games-played","gplayed"]:
        stat = "Games Played"
    elif stat.lower() in ["goals","goal","scores"]:
        stat = "Goals"
    elif stat.lower() in ['assists','assist','passes']:
        stat = "Assists"
    elif stat.lower() in ['saves','save']:
        stat = "Saves"
    elif stat.lower() in ['shots','shot']:
        stat = "Shots"
    elif stat.lower() in ['points','point','goals+assists','goals + assists','goals and assists']:
        stat = "Points (Goals+Assists)"
    elif stat.lower() in ['gpg','goals per game','goals pg','goals per']:
        stat = "Goals per game"
    elif stat.lower() in ['apg','assists per game','assists pg','assists per']:
        stat = "Assists per game"
    elif stat.lower() in ['spg','sapg','saves per game','saves pg','saves per']:
        stat = "Saves per game"
    elif stat.lower() in ['shot rate','shooting percent','shooting percentage','shot accuracy','shooting accuracy','shooting %','shot %']:
        stat = "Shooting %"
    elif stat.lower() in ['win rate','winning rate','winning percent','winning percentage']:
        stat = "Winning %"
    elif stat.lower() in ['wins','win']:
        stat = "Wins"
    elif stat.lower() in ['ppg','points per game','points pg','points per']:
        stat = "Points per Game"
    elif stat.lower() in ['shpg','shots per game',' shots pg', 'shots per']:
        stat = "Shots Per Game"
    
    playersheet = sheet.get_google_sheet(sheet_id, 'Players!A1:I')
    players = sheet.gsheet2df(playersheet)
    lower_players = players['Username'].str.lower()
    if player.lower() in lower_players.values:
        pindex = lower_players[lower_players == player.lower()].index[0]
        player = players.loc[pindex][0]
    players = players.set_index("Username")
    league = players.loc[player, "League"]
    if type(league) == pd.core.series.Series:
        league = league[0]
    statsheet = sheet.get_google_sheet(sheet_id, f"{league} League Stat Database!C3:R")    
    stats = sheet.gsheet2df(statsheet)
    if stat not in list(stats) and stat.lower() != "all":
        return("That stat could not be understood.")
    stats = stats.loc[stats['Player']==player]
    if stat != "all":
        stats = stats[['Player',stat]]
    return(stats)   
    
def power_rankings(league):
    try:
        league = leagues[league.lower()]
    except:
        return "Could not understand league"
    
    start_rows = {'Major': 2, 'AAA': 21, 'AA': 40, 'A': 59, 'Independent': 78, 'Maverick': 97, 'Renegade': 116, 'Paladin': 135}
    data_range = f'Rankings History!A{start_rows[league]}:M{start_rows[league]+16}'
    # week = sheet.get_google_sheet("1Tlc_TgGMrY5aClFF-Pb5xvtKrJ1Hn2PJOLy2fUDDdFI", 'Sheet Resources!U14')['values'][0][0]
    data = sheet.gsheet2df(sheet.get_google_sheet('1Tlc_TgGMrY5aClFF-Pb5xvtKrJ1Hn2PJOLy2fUDDdFI', data_range)).set_index('')
    column = 1
    for i in range(12):
        if data.iloc[:, i].values[0] == '':
            column = i-1
            break
        else:
            continue
    data.iloc[:, column] = data.iloc[:, column].apply(lambda x: int(x))
    rankings = data.iloc[:, column]
    rankings = rankings.sort_values(ascending=False)
    return rankings

# TODO: Add option to reverse lb order for statlb
# TODO: Add boost ratio, shot %, win %, etc as stats
def statlb(useSheet = False, league = "all", stat = "Goals", limit = 10, pergame=False):
    if useSheet == True and league == "all":
        return "Must choose a specific league to use sheet stats"
    if league != "all":
        try:
            league = leagues[league.lower()]
        except:
            return f"Could not understand league {league}."
    
    # Make sure the program understands the specified stat if it's mis-capitalized or whatever
    # SHEETS-UNDERSTANDABLE STATS
    if useSheet == True:
        if stat.lower() in ["sp","series","series_played","series-played","splayed","seris","sieries","seiries"]:
            stat = "Series Played"
        elif stat.lower() in ["gp","games","games_played","games-played","gplayed"]:
            stat = "Games Played"
        elif stat.lower() in ["goals","goal","scores"]:
            stat = "Goals"
        elif stat.lower() in ['assists','assist','passes']:
            stat = "Assists"
        elif stat.lower() in ['saves','save']:
            stat = "Saves"
        elif stat.lower() in ['shots','shot']:
            stat = "Shots"
        elif stat.lower() in ['points','point','goals+assists','goals + assists','goals and assists']:
            stat = "Points (Goals+Assists)"
        elif stat.lower() in ['gpg','goals per game','goals pg','goals per']:
            stat = "Goals per game"
        elif stat.lower() in ['apg','assists per game','assists pg','assists per']:
            stat = "Assists per game"
        elif stat.lower() in ['spg','sapg','saves per game','saves pg','saves per']:
            stat = "Saves per game"
        elif stat.lower() in ['shot rate','shooting percent','shooting percentage','shot accuracy','shooting accuracy','shooting %','shot %']:
            stat = "Shooting %"
        elif stat.lower() in ['win rate','winning rate','winning percent','winning percentage']:
            stat = "Winning %"
        elif stat.lower() in ['wins','win']:
            stat = "Wins"
        elif stat.lower() in ['ppg','points per game','points pg','points per']:
            stat = "Points per Game"
        elif stat.lower() in ['shpg','shots per game',' shots pg', 'shots per']:
            stat = "Shots Per Game"
        else:
            return f'Could not understand stat {stat.title()}. Try using "$help stats" for a list of available stats, or include "db" in your command to use advanced stats rather than sheet stats.'
    # DATABASE STATS
    # I got lazy and people will have to type these in accurately for it to work
    else:
        if stat.title() not in valid_stats:
            return f'Could not understand stat {stat.title()}. Try using "$help stats" for a list of available stats, or include "db" in your command to use advanced stats rather than sheet stats.'
        else:
            stat = stat.title()
    
    if useSheet == False:
        data = select("players")
        data.fillna(value=0, inplace=True)
        data.set_index("Username", inplace=True)
        if league != "all":
            data = data.loc[data['League'] == league]
    else: 
        # This is redundant for now but sheet ids can be different just in case something changes in the future
        if league.lower() in ['major', 'aaa', 'aa', 'a']: 
            data = sheet.gsheet2df(sheet.get_google_sheet('1AJoBYkYGMIrpe8HkkJcB25DbLP2Z-eV7P6Tk9R6265I', '{league} League Stat Database!C3:R'))
        elif league.lower() in ['independent', 'maverick', 'renegade', 'paladin']:
            data = sheet.gsheet2df(sheet.get_google_sheet('1AJoBYkYGMIrpe8HkkJcB25DbLP2Z-eV7P6Tk9R6265I', '{league} League Stat Database!C3:R'))
        data.set_index("Player", inplace=True)
        data.replace(to_replace='', value='0', inplace=True)        
        # Turn number strings into ints and floats
        for col in data.columns:
            try:
                data[col] = data[col].astype(int)
            except:
                try:
                    data[col] = data[col].astype(float)
                except:
                    data[col] = data[col].str.rstrip('%').astype(float)
    
    lb = data[stat.title()]
    games_played = data['Games Played']
    
    if pergame:
        if stat in ['Goals Per Game', 'Assists per game', 'Saves per game', 'Points per Game', 'Shots per Game', 'Winning %', 'Shooting %']:
            pass # These stats are already per game
        else:
            lb = round(lb/games_played, 2)
            
    
    return lb.sort_values(ascending=False).head(limit)
    
    
    
    