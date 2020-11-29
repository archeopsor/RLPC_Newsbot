import pandas as pd
import Google_Sheets as sheet
from PIL import Image, ImageDraw, ImageFont

sheet_id = "1umoAxAcVLkE_XKlpTNNdc42rECU7-GtoDvUhEXja7XA"

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
    if len(league) > 1:
        league = league[0]
    statsheet = sheet.get_google_sheet(sheet_id, f"{league} League Stat Database!C3:R")    
    stats = sheet.gsheet2df(statsheet)
    if stat not in list(stats) and stat.casefold() != "all":
        return("That stat could not be understood.")
    stats = stats.loc[stats['Player']==player]
    if stat != "all":
        stats = stats[['Player',stat]]
    return(stats)

def forecast_image(league, forecast):
    
    template = Image.open(f"./Image_templates/{league.casefold()}_template.png")
    img = ImageDraw.Draw(template)
    bigfont = ImageFont.truetype('C:/Windows/Fonts/cambriab.ttf', size=25)
    smallfont = ImageFont.truetype('C:/Windows/Fonts/palab.ttf', size=18)
    
    results = forecast[0]
    predator = {}
    wild = {}
    elements = {}
    brawler = {}
    for team in list(results)[0:4]:
        predator[team] = results[team]
    for team in list(results)[4:8]:
        wild[team] = results[team]
    for team in list(results)[8:12]:
        elements[team] = results[team]
    for team in list(results)[12:]:
        brawler[team] = results[team]
     
    for i in range(4):
        team = max(predator, key=predator.get)
        w, h = img.textsize(team, font=bigfont)
        img.text((((198-w)/2)+108, ((40-h)/2)+141+46*i), team, font=bigfont, fill="black")
        
        wins = str(round(predator[team],1))
        w, h = img.textsize(wins, font=smallfont)
        img.text((((40-w)/2)+324, ((40-h)/2)+141+47*i), wins, font=smallfont, fill="black")
        
        losses = str(round(18-predator[team],1))
        w, h = img.textsize(losses, font=smallfont)
        img.text((((40-w)/2)+380, ((40-h)/2)+141+47*i), losses, font=smallfont, fill="black")
        
        predator.pop(team)
        
    for i in range(4):
        team = max(wild, key=wild.get)
        w, h = img.textsize(team, font=bigfont)
        img.text((((198-w)/2)+108, ((40-h)/2)+350+46*i), team, font=bigfont, fill="black")
        
        wins = str(round(wild[team],1))
        w, h = img.textsize(wins, font=smallfont)
        img.text((((40-w)/2)+324, ((40-h)/2)+350+47*i), wins, font=smallfont, fill="black")
        
        losses = str(round(18-wild[team],1))
        w, h = img.textsize(losses, font=smallfont)
        img.text((((40-w)/2)+380, ((40-h)/2)+350+47*i), losses, font=smallfont, fill="black")
        
        wild.pop(team)
    
    for i in range(4):
        team = max(elements, key=elements.get)
        w, h = img.textsize(team, font=bigfont)
        img.text((((198-w)/2)+628, ((40-h)/2)+141+47*i), team, font=bigfont, fill="black")
        
        wins = str(round(elements[team],1))
        w, h = img.textsize(wins, font=smallfont)
        img.text((((40-w)/2)+844, ((40-h)/2)+141+47*i), wins, font=smallfont, fill="black")
        
        losses = str(round(18-elements[team],1))
        w, h = img.textsize(losses, font=smallfont)
        img.text((((40-w)/2)+900, ((40-h)/2)+141+47*i), losses, font=smallfont, fill="black")
        
        elements.pop(team)
        
    for i in range(4):
        team = max(brawler, key=brawler.get)
        w, h = img.textsize(team, font=bigfont)
        img.text((((198-w)/2)+628, ((40-h)/2)+350+47*i), team, font=bigfont, fill="black")
        
        wins = str(round(brawler[team],1))
        w, h = img.textsize(wins, font=smallfont)
        img.text((((40-w)/2)+844, ((40-h)/2)+350+47*i), wins, font=smallfont, fill="black")
        
        losses = str(round(18-brawler[team],1))
        w, h = img.textsize(losses, font=smallfont)
        img.text((((40-w)/2)+900, ((40-h)/2)+350+47*i), losses, font=smallfont, fill="black")
        
        brawler.pop(team)
        
    template.save(f"{league.casefold()} forecast.png")
    
    
def power_rankings(league):
    leagues = {'major': "Major", 'aaa': 'AAA', 'aa': 'AA', 'a': 'A', 'indy': 'Independent', 'independent': 'Independent', 'mav': 'Maverick', 'maverick': 'Maverick', 'renegade': 'Renegade', 'ren': 'Renegade', 'paladin': 'Paladin', 'pal': 'Paladin'}
    try:
        league = leagues[league.casefold()]
    except:
        return "Could not understand league"
    
    start_rows = {'Major': 2, 'AAA': 21, 'AA': 40, 'A': 59, 'Independent': 78, 'Maverick': 97, 'Renegade': 116, 'Paladin': 135}
    data_range = f'Rankings History!A{start_rows[league]}:M{start_rows[league]+16}'
    #week = sheet.get_google_sheet("1Tlc_TgGMrY5aClFF-Pb5xvtKrJ1Hn2PJOLy2fUDDdFI", 'Sheet Resources!U14')['values'][0][0]
    data = sheet.gsheet2df(sheet.get_google_sheet('1Tlc_TgGMrY5aClFF-Pb5xvtKrJ1Hn2PJOLy2fUDDdFI', data_range)).set_index('')
    column = 1
    for i in range(12):
        if data.iloc[:, i].values[0] == '':
            column = i-1
            break
        else:
            continue
    data[f'Week {column}'] = data[f'Week {column}'].apply(lambda x: int(x))
    rankings = data.iloc[:,column]
    rankings = rankings.sort_values(ascending=False)
    return rankings