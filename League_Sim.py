import RLPC_ELO as elo
import numpy as np
import pandas as pd
import Google_Sheets as sheet
from RLPC_Stats import forecast_image


# All the teams
major_teams = ['Bulls', 'Lions', 'Panthers', 'Sharks', 'Cobras', 'Ducks', 'Eagles', 'Hawks', 'Ascension', 'Flames', 'Storm', 'Whitecaps', 'Kings', 'Lumberjacks', 'Pirates', 'Spartans']
major_wins = []
major_losses = []
aaa_teams = ['Bulldogs', 'Tigers', 'Bobcats', 'Dolphins', 'Vipers', 'Geese', 'Osprey', 'Owls', 'Entropy', 'Heat', 'Thunder', 'Tundra', 'Knights', 'Pioneers', 'Raiders', 'Trojans']
aaa_wins = []
aaa_losses = []
aa_teams = ['Mustangs', 'Lynx', 'Jaguars', 'Barracuda', 'Pythons', 'Herons', 'Falcons', 'Vultures', 'Pulsars', 'Inferno', 'Lightning', 'Avalanche', 'Dukes', 'Voyagers', 'Bandits', 'Warriors']
aa_wins = []
aa_losses = []
a_teams = ['Stallions', 'Cougars', 'Leopards', 'Gulls', 'Rattlers', 'Pelicans', 'Ravens', 'Cardinals', 'Genesis', 'Embers', 'Tempest', 'Eskimos', 'Jesters', 'Miners', 'Wranglers', 'Titans']
a_wins = []
a_losses = []
indy_teams = ['Admirals', 'Dragons', 'Beavers', 'Cyclones', 'Grizzlies', 'Centurions', 'Yellow Jackets', 'Galaxy', 'Sockeyes', 'Wolves', 'Wildcats', 'Rhinos', 'Scorpions', 'Thrashers', 'Toucans', 'Wizards']
indy_wins = []
indy_losses = []
mav_teams = ['Captains', 'Yetis', 'Otters', 'Tides', 'Pandas', 'Samurai', 'Hornets', 'Solar', 'Piranhas', 'Terriers', 'Jackrabbits', 'Zebras', 'Camels', 'Raptors', 'Macaws', 'Mages']
mav_wins = []
mav_losses = []
ren_teams = ['Pilots', 'Werewolves', 'Wolverines', 'Hurricanes', 'Koalas', 'Vikings', 'Fireflies', 'Comets', 'Stingrays', 'Hounds', 'Warthogs', 'Gorillas', 'Coyotes', 'Harriers', 'Puffins', 'Witches']
ren_wins = []
ren_losses = []
pal_teams = ['Sailors', 'Griffins', 'Badgers', 'Quakes', 'Cubs', 'Ninjas', 'Dragonflies', 'Cosmos', 'Hammerheads', 'Foxes', 'Jackals', 'Wildebeests', 'Roadrunners', 'Buzzards', 'Penguins', 'Sorcerers']
pal_wins = []
pal_losses = []

# Get the wins and losses of all the teams in a dataframe from the sheet
gsheet = sheet.get_google_sheet("1Tlc_TgGMrY5aClFF-Pb5xvtKrJ1Hn2PJOLy2fUDDdFI","Team Wins!A1:AE17")
winloss = sheet.gsheet2df(gsheet)
for i in range(0,16):
    major_wins.append(int(winloss.iloc[i,1]))
    major_losses.append(int(winloss.iloc[i,2]))
    aaa_wins.append(int(winloss.iloc[i,5]))
    aaa_losses.append(int(winloss.iloc[i,6]))
    aa_wins.append(int(winloss.iloc[i,9]))
    aa_losses.append(int(winloss.iloc[i,10]))
    a_wins.append(int(winloss.iloc[i,13]))
    a_losses.append(int(winloss.iloc[i,14]))
    indy_wins.append(int(winloss.iloc[i,17]))
    indy_losses.append(int(winloss.iloc[i,18]))
    mav_wins.append(int(winloss.iloc[i,21]))
    mav_losses.append(int(winloss.iloc[i,22]))
    ren_wins.append(int(winloss.iloc[i,25]))
    ren_losses.append(int(winloss.iloc[i,26]))
    pal_wins.append(int(winloss.iloc[i,29]))
    pal_losses.append(int(winloss.iloc[i,30]))

# Current record for each team
major_records = {"Team": major_teams, "Wins": major_wins, "Losses": major_losses}
major_records = pd.DataFrame.from_dict(major_records).set_index("Team")
aaa_records = {"Team": aaa_teams, "Wins": aaa_wins, "Losses": aaa_losses}
aaa_records = pd.DataFrame.from_dict(aaa_records).set_index("Team")
aa_records = {"Team": aa_teams, "Wins": aa_wins, "Losses": aa_losses}
aa_records = pd.DataFrame.from_dict(aa_records).set_index("Team")
a_records = {"Team": a_teams, "Wins": a_wins, "Losses": a_losses}
a_records = pd.DataFrame.from_dict(a_records).set_index("Team")
indy_records = {"Team": indy_teams, "Wins": indy_wins, "Losses": indy_losses}
indy_records = pd.DataFrame.from_dict(indy_records).set_index("Team")
mav_records = {"Team": mav_teams, "Wins": mav_wins, "Losses": mav_losses}
mav_records = pd.DataFrame.from_dict(mav_records).set_index("Team")
ren_records = {"Team": ren_teams, 'Wins': ren_wins, 'Losses': ren_losses}
ren_records = pd.DataFrame.from_dict(ren_records).set_index("Team")
pal_records = {"Team": pal_teams, 'Wins': pal_wins, 'Losses': pal_losses}
pal_records = pd.DataFrame.from_dict(pal_records).set_index("Team")


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
        print(f"Simulation #{i}")
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
        
        for i in range(4):
            predator[teams[i]] = temp_records.loc[teams[i], 'Wins']
            wild[teams[i+4]] = temp_records.loc[teams[i+4], 'Wins']
            elements[teams[i+8]] = temp_records.loc[teams[i+8], 'Wins']
            brawler[teams[i+12]] = temp_records.loc[teams[i+12], 'Wins']
        
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
        
        sheet.append_data(sheet_id, f"Most Recent!B{row}:F{row+15}", body, insertDataOption = 'OVERWRITE')
    
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
