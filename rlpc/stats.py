import pandas as pd

from tools import sheet

sheet_id = "1AJoBYkYGMIrpe8HkkJcB25DbLP2Z-eV7P6Tk9R6265I"

def get_player_stats(player,stat="all"):
    # Make sure the program understands the specified stat if it's mis-capitalized or whatever
    if stat.casefold() in ["sp","series","series_played","series-played","splayed","seris","sieries","seiries"]:
        stat = "Series Played"
    elif stat.casefold() in ["gp","games","games_played","games-played","gplayed"]:
        stat = "Games Played"
    elif stat.casefold() in ["goals","goal","scores"]:
        stat = "Goals"
    elif stat.casefold() in ['assists','assist','passes']:
        stat = "Assists"
    elif stat.casefold() in ['saves','save']:
        stat = "Saves"
    elif stat.casefold() in ['shots','shot']:
        stat = "Shots"
    elif stat.casefold() in ['points','point','goals+assists','goals + assists','goals and assists']:
        stat = "Points (Goals+Assists)"
    elif stat.casefold() in ['gpg','goals per game','goals pg','goals per']:
        stat = "Goals per game"
    elif stat.casefold() in ['apg','assists per game','assists pg','assists per']:
        stat = "Assists per game"
    elif stat.casefold() in ['spg','sapg','saves per game','saves pg','saves per']:
        stat = "Saves per game"
    elif stat.casefold() in ['shot rate','shooting percent','shooting percentage','shot accuracy','shooting accuracy','shooting %','shot %']:
        stat = "Shooting %"
    elif stat.casefold() in ['win rate','winning rate','winning percent','winning percentage']:
        stat = "Winning %"
    elif stat.casefold() in ['wins','win']:
        stat = "Wins"
    elif stat.casefold() in ['ppg','points per game','points pg','points per']:
        stat = "Points per Game"
    elif stat.casefold() in ['shpg','shots per game',' shots pg', 'shots per']:
        stat = "Shots Per Game"
    
    playersheet = sheet.get_google_sheet(sheet_id, 'Players!A1:I')
    players = sheet.gsheet2df(playersheet)
    lower_players = players['Username'].str.lower()
    if player.casefold() in lower_players.values:
        pindex = lower_players[lower_players == player.casefold()].index[0]
        player = players.loc[pindex][0]
    players = players.set_index("Username")
    league = players.loc[player, "League"]
    if type(league) == pd.core.series.Series:
        league = league[0]
    statsheet = sheet.get_google_sheet(sheet_id, f"{league} League Stat Database!C3:R")    
    stats = sheet.gsheet2df(statsheet)
    if stat not in list(stats) and stat.casefold() != "all":
        return("That stat could not be understood.")
    stats = stats.loc[stats['Player']==player]
    if stat != "all":
        stats = stats[['Player',stat]]
    return(stats)   
    
def power_rankings(league):
    leagues = {'major': "Major", 'aaa': 'AAA', 'aa': 'AA', 'a': 'A', 'indy': 'Independent', 'independent': 'Independent', 'mav': 'Maverick', 'maverick': 'Maverick', 'renegade': 'Renegade', 'ren': 'Renegade', 'paladin': 'Paladin', 'pal': 'Paladin'}
    try:
        league = leagues[league.casefold()]
    except:
        return "Could not understand league"
    
    start_rows = {'Major': 2, 'AAA': 21, 'AA': 40, 'A': 59, 'Independent': 78, 'Maverick': 97, 'Renegade': 116, 'Paladin': 135}
    data_range = f'Rankings History!A{start_rows[league]}:M{start_rows[league]+16}'
    week = sheet.get_google_sheet("1Tlc_TgGMrY5aClFF-Pb5xvtKrJ1Hn2PJOLy2fUDDdFI", 'Sheet Resources!U14')['values'][0][0]
    data = sheet.gsheet2df(sheet.get_google_sheet('1Tlc_TgGMrY5aClFF-Pb5xvtKrJ1Hn2PJOLy2fUDDdFI', data_range)).set_index('')
    # column = 1
    # return data
    # for i in range(12):
    #     if data.iloc[:, i].values[0] == '':
    #         column = i-1
    #         break
    #     else:
    #         continue
    data[week] = data[week].apply(lambda x: int(x))
    rankings = data[week]
    rankings = rankings.sort_values(ascending=False)
    return rankings