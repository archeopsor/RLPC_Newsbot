import pandas as pd
import Google_Sheets as sheet
from PIL import Image, ImageDraw, ImageFont

sheet_id = "1CM0cojzf-j-rZ-4H5fsfx1yelIKDLUW9eVGckIDy_nE"

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
    statsheet = sheet.get_google_sheet(sheet_id, f"{league} League Stat Database!C3:R")    
    stats = sheet.gsheet2df(statsheet)
    if stat not in list(stats) and stat.casefold() != "all":
        return("That stat could not be understood.")
    stats = stats.loc[stats['Player']==player]
    if stat != "all":
        stats = stats[['Player',stat]]
    return(stats)

def forecast_image(league, forecast):
    
    if league.casefold() == "major":  
        template = Image.open("./Image_templates/major_template.png")
        img = ImageDraw.Draw(template)
        bigfont = ImageFont.truetype('C:/Windows/Fonts/cambriab.ttf', size=25)
        smallfont = ImageFont.truetype('C:/Windows/Fonts/palab.ttf', size=15)
        
        predator = {"Bulls": forecast[0]['Bulls'], "Lions": forecast[0]['Lions'], "Panthers": forecast[0]['Panthers'], "Sharks": forecast[0]['Sharks']}
        wild = {"Cobras": forecast[0]['Cobras'], "Ducks": forecast[0]['Ducks'], "Eagles": forecast[0]['Eagles'], "Hawks": forecast[0]['Hawks']}
        elements = {"Ascension": forecast[0]['Ascension'], "Flames": forecast[0]['Flames'], "Storm": forecast[0]['Storm'], "Whitecaps": forecast[0]['Whitecaps']}
        brawler = {"Kings": forecast[0]['Kings'], "Lumberjacks": forecast[0]['Lumberjacks'], "Pirates": forecast[0]['Pirates'], "Spartans": forecast[0]['Spartans']}
        
    for i in range(4):
        team = max(predator, key=predator.get)
        img.text((90, 107+(37*i)), team, font=bigfont, fill="black")
        img.text((249, 117+(37*i)), str(round(predator[team],1)), font=smallfont, fill="black")
        img.text((293, 117+(37*i)), str(round(18-predator[team],1)), font=smallfont, fill="black")
        predator.pop(team)
        
    for i in range(4):
        team = max(wild, key=wild.get)
        img.text((90, 267+(36*i)), team, font=bigfont, fill="black")
        img.text((249, 277+(36*i)), str(round(wild[team],1)), font=smallfont, fill="black")
        img.text((293, 277+(36*i)), str(round(18-wild[team],1)), font=smallfont, fill="black")
        wild.pop(team)
    
    for i in range(4):
        team = max(elements, key=elements.get)
        img.text((480, 107+(37*i)), team, font=bigfont, fill="black")
        img.text((646, 117+(37*i)), str(round(elements[team],1)), font=smallfont, fill="black")
        img.text((689, 117+(37*i)), str(round(18-elements[team],1)), font=smallfont, fill="black")
        elements.pop(team)
        
    for i in range(4):
        team = max(brawler, key=brawler.get)
        img.text((480, 267+(36*i)), team, font=bigfont, fill="black")
        img.text((646, 277+(36*i)), str(round(brawler[team],1)), font=smallfont, fill="black")
        img.text((689, 277+(36*i)), str(round(18-brawler[team],1)), font=smallfont, fill="black")
        brawler.pop(team)
        
    template.save(f"{league} forecast.png")
    
    
    
    
    
    
    