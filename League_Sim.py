import numpy as np
from PIL import Image, ImageDraw, ImageFont

from rlpc import elo

from tools import sheet

# Get the wins and losses of all the teams in a dataframe from the sheet
gsheet = sheet.get_google_sheet("1Tlc_TgGMrY5aClFF-Pb5xvtKrJ1Hn2PJOLy2fUDDdFI","Team Wins!A1:AE17")
winloss = sheet.gsheet2df(gsheet)

major_records = winloss.iloc[:, 0:3].set_index("Major Teams").astype('int')
aaa_records = winloss.iloc[:, 4:7].set_index("AAA Teams").astype('int')
aa_records = winloss.iloc[:, 8:11].set_index("AA Teams").astype('int')
a_records = winloss.iloc[:, 12:15].set_index("A Teams").astype('int')
indy_records = winloss.iloc[:, 16:19].set_index("Indy Teams").astype('int')
mav_records = winloss.iloc[:, 20:23].set_index("Mav Teams").astype('int')
ren_records = winloss.iloc[:, 24:27].set_index("Renegade Teams").astype('int')
pal_records = winloss.iloc[:, 28:31].set_index("Paladin Teams").astype('int')

major_teams = list(major_records.index)
aaa_teams = list(aaa_records.index)
aa_teams = list(aa_records.index)
a_teams = list(a_records.index)
indy_teams = list(indy_records.index)
mav_teams = list(mav_records.index)
ren_teams = list(ren_records.index)
pal_teams = list(pal_records.index)

divisions = {'Sharks': 'Predator', 'Bulls': 'Predator', 'Panthers': 'Predator', 'Lions': 'Predator', 
             'Whitecaps': 'Elements', 'Storm': 'Elements', 'Flames': 'Elements', 'Ascension': 'Elements',
             'Eagles': 'Wild', 'Hawks': 'Wild', 'Ducks': 'Wild', 'Cobras': 'Wild',
             'Lumberjacks': 'Brawler', 'Kings': 'Brawler', 'Pirates': 'Brawler', 'Spartans': 'Brawler',
             'Bobcats': 'Predator', 'Bulldogs': 'Predator', 'Dolphins': 'Predator', 'Tigers': 'Predator',
             'Heat': 'Elements', 'Tundra': 'Elements', 'Entropy': 'Elements', 'Thunder': 'Elements',
             'Osprey': 'Wild', 'Vipers': 'Wild', 'Geese': 'Wild', 'Owls': 'Wild',
             'Knights': 'Brawler', 'Trojans': 'Brawler', 'Pioneers': 'Brawler', 'Raiders': 'Brawler',
             'Mustangs': 'Predator', 'Jaguars': 'Predator', 'Lynx': 'Predator', 'Barracuda': 'Predator',
             'Avalanche': 'Elements', 'Inferno': 'Elements', 'Lightning': 'Elements', 'Pulsars': 'Elements',
             'Herons': 'Wild', 'Pythons': 'Wild', 'Falcons': 'Wild', 'Vultures': 'Wild',
             'Warriors': 'Brawler', 'Voyagers': 'Brawler', 'Bandits': 'Brawler', 'Dukes': 'Brawler',
             'Stallions': 'Predator', 'Cougars': 'Predator', 'Leopards': 'Predator', 'Gulls': 'Predator',
             'Tempest': 'Elements', 'Embers': 'Elements', 'Eskimos': 'Elements', 'Genesis': 'Elements',
             'Ravens': 'Wild', 'Pelicans': 'Wild', 'Rattlers': 'Wild', 'Cardinals': 'Wild',
             'Titans': 'Brawler', 'Miners': 'Brawler', 'Jesters': 'Brawler', 'Wranglers': 'Brawler',
             'Beavers': 'Predator', 'Dragons': 'Predator', 'Cyclones': 'Predator', 'Admirals': 'Predator', 
             'Wolves': 'Elements', 'Wildcats': 'Elements', 'Rhinos': 'Elements', 'Sockeyes': 'Elements',
             'Galaxy': 'Wild', 'Centurions': 'Wild', 'Grizzlies': 'Wild', 'Yellow Jackets': 'Wild',
             'Scorpions': 'Brawler', 'Toucans': 'Brawler', 'Thrashers': 'Brawler', 'Wizards': 'Brawler',
             'Tides': 'Predator', 'Yetis': 'Predator', 'Otters': 'Predator', 'Captains': 'Predator',
             'Terriers': 'Elements', 'Jackrabbits': 'Elements', 'Zebras': 'Elements', 'Piranhas': 'Elements',
             'Samurai': 'Wild', 'Hornets': 'Wild', 'Solar': 'Wild', 'Pandas': 'Wild', 
             'Macaws': 'Brawler', 'Camels': 'Brawler', 'Raptors': 'Brawler', 'Mages': 'Brawler',
             'Pilots': 'Predator', 'Wolverines': 'Predator', 'Werewolves': 'Predator', 'Hurricanes': 'Predator',
             'Gorillas': 'Elements', 'Stingrays': 'Elements', 'Warthogs': 'Elements', 'Hounds': 'Elements',
             'Vikings': 'Wild', 'Koalas': 'Wild', 'Comets': 'Wild', 'Fireflies': 'Wild',
             'Harriers': 'Brawler', 'Coyotes': 'Brawler', 'Puffins': 'Brawler', 'Witches': 'Brawler',
             'Griffins': 'Predator', 'Quakes': 'Predator', 'Sailors': 'Predator', 'Badgers': 'Predator',
             'Wildebeests': 'Elements', 'Hammerheads': 'Elements', 'Jackals': 'Elements', 'Foxes': 'Elements',
             'Dragonflies': 'Wild', 'Cosmos': 'Wild', 'Ninjas': 'Wild', 'Cubs': 'Wild',
             'Roadrunners': 'Brawler', 'Penguins': 'Brawler', 'Buzzards': 'Brawler', 'Sorcerers': 'Brawler'}

def predict_season(league, times, image=False, official=False):
    
    if league.casefold() not in ['major', 'aaa', 'aa', 'a', 'independent', 'maverick', 'renegade', 'paladin']:
        print('Please use a valid league')
        return
    
    schedule = []
    if league.casefold() in ['major', 'aaa', 'aa', 'a']:
        sheet_schedule = sheet.gsheet2df(sheet.get_google_sheet("1umoAxAcVLkE_XKlpTNNdc42rECU7-GtoDvUhEXja7XA", f'{league} Schedule!N4:V'))
    elif league.casefold() in ['independent', 'maverick', 'renegade', 'paladin']:
        sheet_schedule = sheet.gsheet2df(sheet.get_google_sheet("10cLowvKoG5tAtLNS9NEk808vROULHl5KMU0LduBNqbI", f'{league} Schedule!N4:V'))
    for row in sheet_schedule.index:
        if sheet_schedule.loc[row, "Winner"] == '':
            game = f'{sheet_schedule.iloc[row, 2]} - {sheet_schedule.iloc[row, 4]}'
            schedule.append(game)
    
    # Make a series of the ELO for the league so it can be used repeatedly
    ratings = elo.recall_data(league).set_index('Team')['elo'].astype(int)

    # Make a list of all the teams that make it to each stage of success
    playoffs_teams = []
    playoff_probabilities = {}
    semi_teams = []
    semi_probabilities = {}
    finals_teams = []
    finals_probabilities = {}
    champ_teams = []
    champ_probabilities = {}
    
    if league.casefold() == "major":
        records = major_records.copy()
        teams = major_teams.copy()
    elif league.casefold() == "aaa":
        records = aaa_records.copy()
        teams = aaa_teams.copy()
    elif league.casefold() == "aa":
        records = aa_records.copy()
        teams = aa_teams.copy()
    elif league.casefold() == "a":
        records = a_records.copy()
        teams = a_teams.copy()
    elif league.casefold() == "independent":
        records = indy_records.copy()
        teams = indy_teams.copy()
    elif league.casefold() == "maverick":
        records = mav_records.copy()
        teams = mav_teams.copy()
    elif league.casefold() == "renegade":
        records = ren_records.copy()
        teams = ren_teams.copy()
    elif league.casefold() == "paladin":
        records = pal_records.copy()
        teams = pal_teams.copy()        
    
    # Make a dictionary to track all the wins the teams get in the simulations
    predicted_records = {}
    for team in records.index:
        predicted_records[team] = 0
    
    for i in range(1,times+1):
        print(f"Simulation #{i}     {league}")
        temp_ratings = ratings.copy().sample(frac=1)
        temp_records = records.copy().sample(frac=1)
        temp_schedule = schedule.copy()
        
        # Start simulating the games    
        while len(temp_schedule) > 0:
            # Find the probability of either team winning based on ELO
            game = temp_schedule[0]
            game = game.split(' - ')

            # Find the probability of either team winning based on ELO
            team1 = game[0].title()
            team2 = game[-1].title()
            team1elo = temp_ratings[team1]
            team2elo = temp_ratings[team2]
            
            Q1 = 10**(team1elo/400)
            Q2 = 10**(team2elo/400)
            team1_win_prob = Q1/(Q1+Q2)
            team2_win_prob = Q2/(Q1+Q2)
            
            # Randomly pick a winner based on the probabilities found just above, then pick a random score
            winner = np.random.choice([team1, team2], replace = True, p = [team1_win_prob, team2_win_prob])
            loser = team1 if winner == team2 else team2
            team1_score = 3 if winner == team1 else np.random.choice([0,1,2])
            team2_score = 3 if winner == team2 else np.random.choice([0,1,2])
            
            # Update temporary records and elo
            k = 60
            Qa = 10**(temp_ratings[team1]/600)
            Qb = 10**(temp_ratings[team2]/600)
            
            Ea = Qa/(Qa+Qb)  # Expected Score
            Eb = Qb/(Qa+Qb)
            
            Sa = team1_score/(team1_score + team2_score) # Actual Score
            Sb = team2_score/(team1_score + team2_score)
            
            temp_ratings[team1] += k*(Sa-Ea)
            temp_ratings[team2] += k*(Sb-Eb)
            temp_records.loc[winner, 'Wins'] += 1
            temp_records.loc[loser, 'Losses'] += 1
                        
            temp_schedule = temp_schedule[1:]
            
        # Figure out which teams made the playoffs in this sim, and add them to a list
        playoffs = [] # Teams making it to playoffs
        quarter_games = [] # Games to be played in quarters (based on seeding)
        conf1_teams = {} # Playoff teams in Conference 1 (for seeding)
        conf2_teams = {} # Playoff teams in Conference 2 (for seeding)
        
        predator = {}
        wild = {}
        elements = {}
        brawler= {}
        
        for team in teams:
            if divisions[team] == 'Predator':
                predator[team] = temp_records.loc[team, 'Wins']
            elif divisions[team] == 'Elements':
                elements[team] = temp_records.loc[team, 'Wins']
            elif divisions[team] == 'Wild':
                wild[team] = temp_records.loc[team, 'Wins']
            elif divisions[team] == 'Brawler':
                brawler[team] = temp_records.loc[team, 'Wins']
        
        # Shuffle divisions to "simulate" tiebreakers
        l = list(predator.items())
        np.random.shuffle(l)
        predator = dict(l)
        l = list(wild.items())
        np.random.shuffle(l)
        wild = dict(l)
        l = list(elements.items())
        np.random.shuffle(l)
        elements = dict(l)
        l = list(brawler.items())
        np.random.shuffle(l)
        brawler = dict(l)        
        
        # Add playoff teams to their list, and determine games/seeding for quarters
        playoffs.append(max(predator, key=predator.get))
        conf1_teams[max(predator, key=predator.get)] = predator[max(predator, key=predator.get)]
        predator.pop(max(predator, key=predator.get))
        playoffs.append(max(wild, key=wild.get))
        conf1_teams[max(wild, key=wild.get)] = wild[max(wild, key=wild.get)]
        wild.pop(max(wild, key=wild.get))
        playoffs.append(max(elements, key=elements.get))
        conf2_teams[max(elements, key=elements.get)] = elements[max(elements, key=elements.get)]
        elements.pop(max(elements, key=elements.get))
        playoffs.append(max(brawler, key=brawler.get))
        conf2_teams[max(brawler, key=brawler.get)] = brawler[max(brawler, key=brawler.get)]
        brawler.pop(max(brawler, key=brawler.get))        
        conf1 = {}
        conf1.update(predator)
        conf1.update(wild)
        l = list(conf1.items())
        np.random.shuffle(l)
        conf1 = dict(l)  
        playoffs.append(max(conf1, key=conf1.get))
        conf1_teams[max(conf1, key=conf1.get)] = conf1[max(conf1, key=conf1.get)]
        conf1.pop(max(conf1, key=conf1.get))
        playoffs.append(max(conf1, key=conf1.get))
        conf1_teams[max(conf1, key=conf1.get)] = conf1[max(conf1, key=conf1.get)]
        conf1_teams = sorted(conf1_teams, key=conf1_teams.get, reverse=True)
        quarter_games.append(f"{conf1_teams[0]} - {conf1_teams[3]}")
        quarter_games.append(f"{conf1_teams[1]} - {conf1_teams[2]}")
        conf2 = {}
        conf2.update(elements)
        conf2.update(brawler)
        l = list(conf2.items())
        np.random.shuffle(l)
        conf2 = dict(l)  
        playoffs.append(max(conf2, key=conf2.get))
        conf2_teams[max(conf2, key=conf2.get)] = conf2[max(conf2, key=conf2.get)]
        conf2.pop(max(conf2, key=conf2.get))
        playoffs.append(max(conf2, key=conf2.get))
        conf2_teams[max(conf2, key=conf2.get)] = conf2[max(conf2, key=conf2.get)]
        conf2_teams = sorted(conf2_teams, key=conf2_teams.get, reverse=True)
        quarter_games.append(f"{conf2_teams[0]} - {conf2_teams[3]}")
        quarter_games.append(f"{conf2_teams[1]} - {conf2_teams[2]}")
        
        # Simulate the Quarter-finals of the playoffs, add the winners to the semifinals list
        semifinals = []
        for game in quarter_games:
            game = game.split(' - ')
            team1 = game[0].title()
            team2 = game[-1].title()
            team1elo = temp_ratings[team1]
            team2elo = temp_ratings[team2]
            Q1 = 10**(team1elo/400)
            Q2 = 10**(team2elo/400)
            team1_win_prob = Q1/(Q1+Q2)
            team2_win_prob = Q2/(Q1+Q2)
            
            # Randomly pick a winner based on the probabilities found just above
            winner = np.random.choice([team1, team2], replace = True, p = [team1_win_prob, team2_win_prob])
            semifinals.append(winner)

        # Simulate the Semi-finals of the playoffs, add the winners to the Finals list
        finals = []
        semi_games = []
        semi_games.append(f"{semifinals[0]} - {semifinals[1]}")
        semi_games.append(f"{semifinals[2]} - {semifinals[3]}")
        for game in semi_games:
            game = game.split(' - ')
            team1 = game[0].title()
            team2 = game[-1].title()
            team1elo = temp_ratings[team1]
            team2elo = temp_ratings[team2]
            Q1 = 10**(team1elo/400)
            Q2 = 10**(team2elo/400)
            team1_win_prob = Q1/(Q1+Q2)
            team2_win_prob = Q2/(Q1+Q2)
            
            # Randomly pick a winner based on the probabilities found just above
            winner = np.random.choice([team1, team2], replace = True, p = [team1_win_prob, team2_win_prob])
            finals.append(winner)
        
        # Simulate the finals, make the champion the winner of this match
        champion = None
        game = f"{finals[0]} - {finals[1]}"
        game = game.split(' - ')
        team1 = game[0].title()
        team2 = game[-1].title()
        team1elo = temp_ratings[team1]
        team2elo = temp_ratings[team2]
        Q1 = 10**(team1elo/400)
        Q2 = 10**(team2elo/400)
        team1_win_prob = Q1/(Q1+Q2)
        team2_win_prob = Q2/(Q1+Q2)
        
        champion = np.random.choice([team1, team2], replace = True, p = [team1_win_prob, team2_win_prob])
        
        # Keep track of all the wins accumulated over the seasons
        for team in temp_records.index:
            predicted_records[team] += temp_records.loc[team,'Wins']
            
        # Keep track of all the playoff teams accumulated over the seasons
        playoffs_teams.extend(playoffs)
        semi_teams.extend(semifinals)
        finals_teams.extend(finals)
        champ_teams.append(champion)        
    
    predictions = {}
    for team in predicted_records:
        predictions[team] = predicted_records[team]/times
        playoff_probabilities[team] = playoffs_teams.count(team)/times
        semi_probabilities[team] = semi_teams.count(team)/times
        finals_probabilities[team] = finals_teams.count(team)/times
        champ_probabilities[team] = champ_teams.count(team)/times
        
    forecast = (predictions, playoff_probabilities, semi_probabilities, finals_probabilities, champ_probabilities)
        
    if image:
        forecast_image(league, forecast)
        
    if official:
        rows = {"major": 3, "aaa": 22, "aa": 41, "a": 60, "independent": 79, "maverick": 98, "renegade": 117, "paladin": 136}
        row = rows[league.casefold()]
        
        sheet_id = "1GEFufHK5xt0WqThYC7xaK2gz3cwjinO43KOsb7HogQQ"
        
        values = []
        for column in forecast:
            col_values = list(column.values())
            values.append(col_values)
            
        body = {'majorDimension': "COLUMNS", 'values': values}
        range_name = f"Most Recent!B{row}:F{row+15}"
        
        sheet.clear(sheet_id, range_name)
        sheet.append_data(sheet_id, range_name, body, insertDataOption = 'OVERWRITE')
    
    return forecast

def full_forecast(times=10000, images=False):
    print("STARTING MAJOR")
    predict_season("major", times, official=True, image=images)
    print("STARTING AAA")
    predict_season("aaa", times, official=True, image=images)
    print("STARTING AA")
    predict_season("aa", times, official=True, image=images)
    print("STARTING A")
    predict_season("a", times, official=True, image=images)
    print("STARTING INDEPENDENT")
    predict_season("independent", times, official=True, image=images)
    print("STARTING MAVERICK")
    predict_season("maverick", times, official=True, image=images)
    print("STARTING RENEGADE")
    predict_season("renegade", times, official=True, image=images)
    print("STARTING PALADIN")
    predict_season("paladin", times, official=True, image=images)

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
    for team in list(results):
        if divisions[team] == 'Predator':
            predator[team] = results[team]
        elif divisions[team] == 'Elements':
            elements[team] = results[team]
        elif divisions[team] == 'Wild':
            wild[team] = results[team]
        elif divisions[team] == 'Brawler':
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
        
    template.save(f"C:/Users/Simi/Pictures/RLPC Forecasts/{league.casefold()} forecast.png")