import RLPC_ELO as elo
import random
import numpy as np
import pandas as pd
import Google_Sheets as sheet
from RLPC_Stats import forecast_image

# All the major teams
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

# Schedule for all the games in each league
major_schedule = ['Bulls - Lions', 'Panthers - Sharks', 'Cobras - Ducks', 'Eagles - Hawks', 'Ascension - Flames', 'Storm - Whitecaps', 'Kings - Lumberjacks', 'Pirates - Spartans', 'Bulls - Panthers', 'Lions - Sharks', 'Cobras - Eagles', 'Ducks - Hawks', 'Ascension - Storm', 'Flames - Whitecaps', 'Kings - Pirates', 'Lumberjacks - Spartans', 'Bulls - Sharks', 'Lions - Panthers', 'Cobras - Hawks', 'Ducks - Eagles', 'Ascension - Whitecaps', 'Flames - Storm', 'Kings - Spartans', 'Lumberjacks - Pirates']
aaa_schedule = ['Bulldogs - Tigers', 'Bobcats - Dolphins', 'Vipers - Geese', 'Osprey - Owls', 'Entropy - Heat', 'Thunder - Tundra', 'Knights - Pioneers', 'Raiders - Trojans', 'Bulldogs - Bobcats', 'Tigers - Dolphins', 'Vipers - Osprey', 'Geese - Owls', 'Entropy - Thunder', 'Heat - Tundra', 'Knights - Raiders', 'Pioneers - Trojans', 'Bulldogs - Dolphins', 'Tigers - Bobcats', 'Vipers - Owls', 'Geese - Osprey', 'Entropy - Tundra', 'Heat - Thunder', 'Knights - Trojans', 'Pioneers - Raiders']
aa_schedule = ['Mustangs - Lynx', 'Jaguars - Barracuda', 'Pythons - Herons', 'Falcons - Vultures', 'Pulsars - Inferno', 'Lightning - Avalanche', 'Dukes - Voyagers', 'Bandits - Warriors', 'Mustangs - Jaguars', 'Lynx - Barracuda', 'Pythons - Falcons', 'Herons - Vultures', 'Pulsars - Lightning', 'Inferno - Avalanche', 'Dukes - Bandits', 'Voyagers - Warriors', 'Mustangs - Barracuda', 'Lynx - Jaguars', 'Pythons - Vultures', 'Herons - Falcons', 'Pulsars - Avalanche', 'Inferno - Lightning', 'Dukes - Warriors', 'Voyagers - Bandits']
a_schedule = ['Stallions - Cougars', 'Leopards - Gulls', 'Rattlers - Pelicans', 'Ravens - Cardinals', 'Genesis - Embers', 'Tempest - Eskimos', 'Jesters - Miners', 'Wranglers - Titans', 'Stallions - Leopards', 'Cougars - Gulls', 'Rattlers - Ravens', 'Pelicans - Cardinals', 'Genesis - Tempest', 'Embers - Eskimos', 'Jesters - Wranglers', 'Miners - Titans', 'Stallions - Gulls', 'Cougars - Leopards', 'Rattlers - Cardinals', 'Pelicans - Ravens', 'Genesis - Eskimos', 'Embers - Tempest', 'Jesters - Titans', 'Miners - Wranglers']

# Get the wins and losses of all the teams in a dataframe from the sheet
gsheet = sheet.get_google_sheet("1Tlc_TgGMrY5aClFF-Pb5xvtKrJ1Hn2PJOLy2fUDDdFI","Team Wins!A1:O17")
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


# Current record for each team
major_records = {"Team": major_teams, "Wins": major_wins, "Losses": major_losses}
major_records = pd.DataFrame.from_dict(major_records).set_index("Team")
aaa_records = {"Team": aaa_teams, "Wins": aaa_wins, "Losses": aaa_losses}
aaa_records = pd.DataFrame.from_dict(aaa_records).set_index("Team")
aa_records = {"Team": aa_teams, "Wins": aa_wins, "Losses": aa_losses}
aa_records = pd.DataFrame.from_dict(aa_records).set_index("Team")
a_records = {"Team": a_teams, "Wins": a_wins, "Losses": a_losses}
a_records = pd.DataFrame.from_dict(a_records).set_index("Team")

def randomize_dict(dict):
    keys = list(dict.keys())
    random.shuffle(keys)
    answer = {}
    for key in keys:
        answer[key] = dict[key]
    return(answer)

def reset_schedule(league):
    if league.casefold() == "major":
        major_schedule.clear()
    elif league.casefold() == "aaa":
        aaa_schedule.clear()
    elif league.casefold() == "aa":
        aa_schedule.clear()
    elif league.casefold() == "a":
        a_schedule.clear()

def gen_schedule(league):
    reset_schedule(league)
    data = input("Please input schedule as copied from the spreadsheet: \n")
    data = data.replace("\t","\n")
    data = data.split("\n")
    
    if league.casefold() == "major":    
        while len(data) > 0:
            major_schedule.append(f"{data[0]} - {data[2]}")
            data = data[3:]
    elif league.casefold() == "aaa":
        while len(data) > 0:
            aaa_schedule.append(f"{data[0]} - {data[2]}")
            data = data[3:]
    elif league.casefold() == "aa":
        while len(data) > 0:
            aa_schedule.append(f"{data[0]} - {data[2]}")
            data = data[3:]
    elif league.casefold() == "a":
        while len(data) > 0:
            a_schedule.append(f"{data[0]} - {data[2]}")
            data = data[3:]

def recall_data():
    global major_elo
    global aaa_elo
    global aa_elo
    global a_elo
    major_elo = elo.recall_data("Major")
    aaa_elo = elo.recall_data("AAA")
    aa_elo = elo.recall_data("AA")
    a_elo = elo.recall_data("A")

recall_data()

def update_elo(league,team1,team2,winner,score):
    loser = team1
    if winner == team1:
        loser = team2
    score = list(score)
    score = f"{score[0]} - {score[-1]}"
    team1 = team1.title()
    team2 = team2.title()
    Qa = 0
    Qb = 0
    if league.casefold() == "major":
        Qa = 10**(int(major_elo.loc[major_elo['teams']==team1,'ELO'])/400)
        Qb = 10**(int(major_elo.loc[major_elo['teams']==team2,'ELO'])/400)
    elif league.casefold() == "aaa":
        Qa = 10**(int(aaa_elo.loc[aaa_elo['teams']==team1,'ELO'])/400)
        Qb = 10**(int(aaa_elo.loc[aaa_elo['teams']==team2,'ELO'])/400)
    elif league.casefold() == "aa":
        Qa = 10**(int(aa_elo.loc[aa_elo['teams']==team1,'ELO'])/400)
        Qb = 10**(int(aa_elo.loc[aa_elo['teams']==team2,'ELO'])/400)
    elif league.casefold() == "a":
        Qa = 10**(int(a_elo.loc[a_elo['teams']==team1,'ELO'])/400)
        Qb = 10**(int(a_elo.loc[a_elo['teams']==team2,'ELO'])/400)
    Ea = Qa/(Qa+Qb)
    Eb = Qb/(Qa+Qb)
    Sa = 0
    Sb = 0
    scparts = score.split()
    score1 = int(scparts[0])
    score2 = int(scparts[2])
    if winner == team1 and score1 > score2:
        Sa = score1/(score1+score2)
        Sb = score2/(score1+score2)
    elif winner == team1 and score2 > score1:
        Sb = score1/(score1+score2)
        Sa = score2/(score1+score2)
    elif winner == team2 and score1 > score2:
        Sa = score1/(score1+score2)
        Sb = score2/(score1+score2)
    elif winner == team2 and score2 > score1:
        Sb = score1/(score1+score2)
        Sa = score2/(score1+score2)
    if league.casefold() == "major":
        major_elo.loc[major_elo['teams']==team1,'ELO'] = round(int(major_elo.loc[major_elo['teams']==team1,'ELO']) + 100*(Sa - Ea))
        major_elo.loc[major_elo['teams']==team2,'ELO'] = round(int(major_elo.loc[major_elo['teams']==team2,'ELO']) + 100*(Sb - Eb))
        major_records.loc[winner][0] = major_records.loc[winner][0] + 1
        major_records.loc[loser][1] = major_records.loc[loser][1] + 1
    if league.casefold() == "aaa":
        aaa_elo.loc[aaa_elo['teams']==team1,'ELO'] = round(int(aaa_elo.loc[aaa_elo['teams']==team1,'ELO']) + 100*(Sa - Ea))
        aaa_elo.loc[aaa_elo['teams']==team2,'ELO'] = round(int(aaa_elo.loc[aaa_elo['teams']==team2,'ELO']) + 100*(Sb - Eb))
        aaa_records.loc[winner][0] = aaa_records.loc[winner][0] + 1
        aaa_records.loc[loser][1] = aaa_records.loc[loser][1] + 1
    if league.casefold() == "aa":
        aa_elo.loc[aa_elo['teams']==team1,'ELO'] = round(int(aa_elo.loc[aa_elo['teams']==team1,'ELO']) + 100*(Sa - Ea))
        aa_elo.loc[aa_elo['teams']==team2,'ELO'] = round(int(aa_elo.loc[aa_elo['teams']==team2,'ELO']) + 100*(Sb - Eb))
        aa_records.loc[winner][0] = aa_records.loc[winner][0] + 1
        aa_records.loc[loser][1] = aa_records.loc[loser][1] + 1
    if league.casefold() == "a":
        a_elo.loc[a_elo['teams']==team1,'ELO'] = round(int(a_elo.loc[a_elo['teams']==team1,'ELO']) + 100*(Sa - Ea))
        a_elo.loc[a_elo['teams']==team2,'ELO'] = round(int(a_elo.loc[a_elo['teams']==team2,'ELO']) + 100*(Sb - Eb))
        a_records.loc[winner][0] = a_records.loc[winner][0] + 1
        a_records.loc[loser][1] = a_records.loc[loser][1] + 1
        
def play_game(league, game):
    # Find the probability of either team winning based on ELO
    team1 = game[0].title()
    team2 = game[2].title()
    if league.casefold() == "major":
        team1elo = int(major_elo.loc[major_elo['teams']==team1,'ELO'].values[0])
        team2elo = int(major_elo.loc[major_elo['teams']==team2,'ELO'].values[0])
    elif league.casefold() == "aaa":
        team1elo = int(aaa_elo.loc[aaa_elo['teams']==team1,'ELO'].values[0])
        team2elo = int(aaa_elo.loc[aaa_elo['teams']==team2,'ELO'].values[0])
    elif league.casefold() == "aa" or league.casefold() == "indy":
        team1elo = int(aa_elo.loc[aa_elo['teams']==team1,'ELO'].values[0])
        team2elo = int(aa_elo.loc[aa_elo['teams']==team2,'ELO'].values[0])
    elif league.casefold() == "a" or league.casefold() == "mav":
        team1elo = int(a_elo.loc[a_elo['teams']==team1,'ELO'].values[0])
        team2elo = int(a_elo.loc[a_elo['teams']==team2,'ELO'].values[0])
    Q1 = 10**(team1elo/400)
    Q2 = 10**(team2elo/400)
    team1_win_prob = Q1/(Q1+Q2)
    team2_win_prob = Q2/(Q1+Q2)
    
    # Randomly pick a winner based on the probabilities found just above, then pick a random score
    winner = np.random.choice([team1, team2], replace = True, p = [team1_win_prob, team2_win_prob])
    score = f"3 - {random.choice([0,1,2])}"
    
    # Update records and ELO
    update_elo(league, team1, team2, winner, score)
        
def sim_schedule(league):
    
    global major_records
    global aaa_records
    global aa_records
    global a_records
    if league.casefold() == "major":
        major_records = {"Team": major_teams, "Wins": major_wins, "Losses": major_losses}
        major_records = pd.DataFrame.from_dict(major_records).set_index("Team")
        major_records = major_records.sample(frac=1)
    elif league.casefold() == "aaa":
        aaa_records = {"Team": aaa_teams, "Wins": aaa_wins, "Losses": aaa_losses}
        aaa_records = pd.DataFrame.from_dict(aaa_records).set_index("Team")
        aaa_records = aaa_records.sample(frac=1)
    elif league.casefold() == "aa":
        aa_records = {"Team": aa_teams, "Wins": aa_wins, "Losses": aa_losses}
        aa_records = pd.DataFrame.from_dict(aa_records).set_index("Team")
        aa_records = aa_records.sample(frac=1)
    elif league.casefold() == "a":
        a_records = {"Team": a_teams, "Wins": a_wins, "Losses": a_losses}
        a_records = pd.DataFrame.from_dict(a_records).set_index("Team")
        a_records = a_records.sample(frac=1)    
    
    if league.casefold() == "major":
        tempschedule = major_schedule
    elif league.casefold() == "aaa":
        tempschedule = aaa_schedule
    elif league.casefold() == "aa":
        tempschedule = aa_schedule
    elif league.casefold() == "a":
        tempschedule = a_schedule
        
    global major_elo
    global aaa_elo
    global aa_elo
    global a_elo
    tempmajor = major_elo.copy()
    tempaaa = aaa_elo.copy()
    tempaa = aa_elo.copy()
    tempa = a_elo.copy()
    
    if league.casefold() == "major":
        major_elo = major_elo.sample(frac=1)
    elif league.casefold() == "aaa":
        aaa_elo = aaa_elo.sample(frac=1)
    elif league.casefold() == "aa":
        aa_elo = aa_elo.sample(frac=1)
    elif league.casefold() == "a":
        a_elo = a_elo.sample(frac=1)
    
    # Randomize the order of each set of 8 games (each gameday)
    schedule = []
    while len(tempschedule) > 0:
        gameday = tempschedule[:8]
        random.shuffle(gameday)
        schedule.extend(gameday)
        tempschedule = tempschedule[8:]

    # Start simulating the games    
    while len(schedule) > 0:
        # Find the probability of either team winning based on ELO
        game = schedule[0].split()
        play_game(league, game)
        
        schedule = schedule[1:]
    
    # Figure out which teams made the playoffs in this sim, and add them to a list
    playoffs = []
    quarter_games = []
    conf1_teams = {}
    conf2_teams = {}
    
    if league.casefold() == "major":
        predator = {"Bulls": major_records.loc["Bulls","Wins"], "Lions": major_records.loc["Lions","Wins"], "Panthers": major_records.loc["Panthers","Wins"], "Sharks": major_records.loc["Sharks","Wins"]}
        predator = randomize_dict(predator)
        playoffs.append(max(predator, key=predator.get))
        conf1_teams[max(predator, key=predator.get)] = predator[max(predator, key=predator.get)]
        predator.pop(max(predator, key=predator.get))
        wild = {"Cobras": major_records.loc["Cobras","Wins"], "Ducks": major_records.loc["Ducks","Wins"], "Eagles": major_records.loc["Eagles","Wins"], "Hawks": major_records.loc["Hawks","Wins"]}
        wild = randomize_dict(wild)
        playoffs.append(max(wild, key=wild.get))
        conf1_teams[max(wild, key=wild.get)] = wild[max(wild, key=wild.get)]
        wild.pop(max(wild, key=wild.get))
        elements = {"Ascension": major_records.loc["Ascension","Wins"], "Flames": major_records.loc["Flames","Wins"], "Storm": major_records.loc["Storm","Wins"], "Whitecaps": major_records.loc["Whitecaps","Wins"]}
        elements = randomize_dict(elements)
        playoffs.append(max(elements, key=elements.get))
        conf2_teams[max(elements, key=elements.get)] = elements[max(elements, key=elements.get)]
        elements.pop(max(elements, key=elements.get))
        brawler = {"Kings": major_records.loc["Kings","Wins"], "Lumberjacks": major_records.loc["Lumberjacks","Wins"], "Pirates": major_records.loc["Pirates","Wins"], "Spartans": major_records.loc["Spartans","Wins"]}
        brawler = randomize_dict(brawler)
        playoffs.append(max(brawler, key=brawler.get))
        conf2_teams[max(brawler, key=brawler.get)] = brawler[max(brawler, key=brawler.get)]
        brawler.pop(max(brawler, key=brawler.get))
    elif league.casefold() == "aaa":
        predator = {"Bulldogs": aaa_records.loc["Bulldogs","Wins"], "Tigers": aaa_records.loc["Tigers","Wins"], "Bobcats": aaa_records.loc["Bobcats","Wins"], "Dolphins": aaa_records.loc["Dolphins","Wins"]}
        predator = randomize_dict(predator)
        playoffs.append(max(predator, key=predator.get))
        conf1_teams[max(predator, key=predator.get)] = predator[max(predator, key=predator.get)]
        predator.pop(max(predator, key=predator.get))
        wild = {"Vipers": aaa_records.loc["Vipers","Wins"], "Geese": aaa_records.loc["Geese","Wins"], "Osprey": aaa_records.loc["Osprey","Wins"], "Owls": aaa_records.loc["Owls","Wins"]}
        wild = randomize_dict(wild)
        playoffs.append(max(wild, key=wild.get))
        conf1_teams[max(wild, key=wild.get)] = wild[max(wild, key=wild.get)]
        wild.pop(max(wild, key=wild.get))
        elements = {"Entropy": aaa_records.loc["Entropy","Wins"], "Heat": aaa_records.loc["Heat","Wins"], "Thunder": aaa_records.loc["Thunder","Wins"], "Tundra": aaa_records.loc["Tundra","Wins"]}
        elements = randomize_dict(elements)
        playoffs.append(max(elements, key=elements.get))
        conf2_teams[max(elements, key=elements.get)] = elements[max(elements, key=elements.get)]
        elements.pop(max(elements, key=elements.get))
        brawler = {"Knights": aaa_records.loc["Knights","Wins"], "Pioneers": aaa_records.loc["Pioneers","Wins"], "Raiders": aaa_records.loc["Raiders","Wins"], "Trojans": aaa_records.loc["Trojans","Wins"]}
        brawler = randomize_dict(brawler)
        playoffs.append(max(brawler, key=brawler.get))
        conf2_teams[max(brawler, key=brawler.get)] = brawler[max(brawler, key=brawler.get)]
        brawler.pop(max(brawler, key=brawler.get))
    elif league.casefold() == "aa":
        predator = {"Mustangs": aa_records.loc["Mustangs","Wins"], "Lynx": aa_records.loc["Lynx","Wins"], "Jaguars": aa_records.loc["Jaguars","Wins"], "Barracuda": aa_records.loc["Barracuda","Wins"]}
        predator = randomize_dict(predator)
        playoffs.append(max(predator, key=predator.get))
        conf1_teams[max(predator, key=predator.get)] = predator[max(predator, key=predator.get)]
        predator.pop(max(predator, key=predator.get))
        wild = {"Pythons": aa_records.loc["Pythons","Wins"], "Herons": aa_records.loc["Herons","Wins"], "Falcons": aa_records.loc["Falcons","Wins"], "Vultures": aa_records.loc["Vultures","Wins"]}
        predator = randomize_dict(predator)
        playoffs.append(max(wild, key=wild.get))
        conf1_teams[max(wild, key=wild.get)] = wild[max(wild, key=wild.get)]
        wild.pop(max(wild, key=wild.get))
        elements = {"Pulsars": aa_records.loc["Pulsars","Wins"], "Inferno": aa_records.loc["Inferno","Wins"], "Lightning": aa_records.loc["Lightning","Wins"], "Avalanche": aa_records.loc["Avalanche","Wins"]}
        elements = randomize_dict(elements)
        playoffs.append(max(elements, key=elements.get))
        conf2_teams[max(elements, key=elements.get)] = elements[max(elements, key=elements.get)]
        elements.pop(max(elements, key=elements.get))
        brawler = {"Dukes": aa_records.loc["Dukes","Wins"], "Voyagers": aa_records.loc["Voyagers","Wins"], "Bandits": aa_records.loc["Bandits","Wins"], "Warriors": aa_records.loc["Warriors","Wins"]}
        brawler = randomize_dict(brawler)
        playoffs.append(max(brawler, key=brawler.get))
        conf2_teams[max(brawler, key=brawler.get)] = brawler[max(brawler, key=brawler.get)]
        brawler.pop(max(brawler, key=brawler.get))
    elif league.casefold() == "a":
        predator = {"Stallions": a_records.loc["Stallions","Wins"], "Cougars": a_records.loc["Cougars","Wins"], "Leopards": a_records.loc["Leopards","Wins"], "Gulls": a_records.loc["Gulls","Wins"]}
        predator = randomize_dict(predator)
        playoffs.append(max(predator, key=predator.get))
        conf1_teams[max(predator, key=predator.get)] = predator[max(predator, key=predator.get)]
        predator.pop(max(predator, key=predator.get))
        wild = {"Rattlers": a_records.loc["Rattlers","Wins"], "Pelicans": a_records.loc["Pelicans","Wins"], "Ravens": a_records.loc["Ravens","Wins"], "Cardinals": a_records.loc["Cardinals","Wins"]}
        wild = randomize_dict(wild)
        playoffs.append(max(wild, key=wild.get))
        conf1_teams[max(wild, key=wild.get)] = wild[max(wild, key=wild.get)]
        wild.pop(max(wild, key=wild.get))
        elements = {"Genesis": a_records.loc["Genesis","Wins"], "Embers": a_records.loc["Embers","Wins"], "Tempest": a_records.loc["Tempest","Wins"], "Eskimos": a_records.loc["Eskimos","Wins"]}
        elements = randomize_dict(elements)
        playoffs.append(max(elements, key=elements.get))
        conf2_teams[max(elements, key=elements.get)] = elements[max(elements, key=elements.get)]
        elements.pop(max(elements, key=elements.get))
        brawler = {"Jesters": a_records.loc["Jesters","Wins"], "Miners": a_records.loc["Miners","Wins"], "Wranglers": a_records.loc["Wranglers","Wins"], "Titans": a_records.loc["Titans","Wins"]}
        brawler = randomize_dict(brawler)
        playoffs.append(max(brawler, key=brawler.get))
        conf2_teams[max(brawler, key=brawler.get)] = brawler[max(brawler, key=brawler.get)]
        brawler.pop(max(brawler, key=brawler.get))
    conf1 = {}
    conf1.update(predator)
    conf1.update(wild)
    conf1 = randomize_dict(conf1)
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
    conf2 = randomize_dict(conf2)
    playoffs.append(max(conf2, key=conf2.get))
    conf2_teams[max(conf2, key=conf2.get)] = conf2[max(conf2, key=conf2.get)]
    conf2.pop(max(conf2, key=conf2.get))
    playoffs.append(max(conf2, key=conf2.get))
    conf2_teams[max(conf2, key=conf2.get)] = conf2[max(conf2, key=conf2.get)]
    conf2_teams = sorted(conf2_teams, key=conf2_teams.get, reverse=True)
    quarter_games.append(f"{conf2_teams[0]} - {conf2_teams[3]}")
    quarter_games.append(f"{conf2_teams[1]} - {conf2_teams[2]}")

    # Reset the ELO because it's messed up for some reason
    major_elo = tempmajor.copy()
    aaa_elo = tempaaa.copy()
    aa_elo = tempaa.copy()
    a_elo = tempa.copy()
    
    # Simulate the Quarter-finals of the playoffs, add the winners to the semifinals list
    semifinals = []
    for game in quarter_games:
        game = game.split()
        team1 = game[0].title()
        team2 = game[2].title()
        if league.casefold() == "major":
            team1elo = int(major_elo.loc[major_elo['teams']==team1,'ELO'].values[0])
            team2elo = int(major_elo.loc[major_elo['teams']==team2,'ELO'].values[0])
        elif league.casefold() == "aaa":
            team1elo = int(aaa_elo.loc[aaa_elo['teams']==team1,'ELO'].values[0])
            team2elo = int(aaa_elo.loc[aaa_elo['teams']==team2,'ELO'].values[0])
        elif league.casefold() == "aa" or league.casefold() == "indy":
            team1elo = int(aa_elo.loc[aa_elo['teams']==team1,'ELO'].values[0])
            team2elo = int(aa_elo.loc[aa_elo['teams']==team2,'ELO'].values[0])
        elif league.casefold() == "a" or league.casefold() == "mav":
            team1elo = int(a_elo.loc[a_elo['teams']==team1,'ELO'].values[0])
            team2elo = int(a_elo.loc[a_elo['teams']==team2,'ELO'].values[0])
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
        game = game.split()
        team1 = game[0].title()
        team2 = game[2].title()
        if league.casefold() == "major":
            team1elo = int(major_elo.loc[major_elo['teams']==team1,'ELO'].values[0])
            team2elo = int(major_elo.loc[major_elo['teams']==team2,'ELO'].values[0])
        elif league.casefold() == "aaa":
            team1elo = int(aaa_elo.loc[aaa_elo['teams']==team1,'ELO'].values[0])
            team2elo = int(aaa_elo.loc[aaa_elo['teams']==team2,'ELO'].values[0])
        elif league.casefold() == "aa" or league.casefold() == "indy":
            team1elo = int(aa_elo.loc[aa_elo['teams']==team1,'ELO'].values[0])
            team2elo = int(aa_elo.loc[aa_elo['teams']==team2,'ELO'].values[0])
        elif league.casefold() == "a" or league.casefold() == "mav":
            team1elo = int(a_elo.loc[a_elo['teams']==team1,'ELO'].values[0])
            team2elo = int(a_elo.loc[a_elo['teams']==team2,'ELO'].values[0])
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
    game = game.split()
    team1 = game[0].title()
    team2 = game[2].title()
    if league.casefold() == "major":
        team1elo = int(major_elo.loc[major_elo['teams']==team1,'ELO'].values[0])
        team2elo = int(major_elo.loc[major_elo['teams']==team2,'ELO'].values[0])
    elif league.casefold() == "aaa":
        team1elo = int(aaa_elo.loc[aaa_elo['teams']==team1,'ELO'].values[0])
        team2elo = int(aaa_elo.loc[aaa_elo['teams']==team2,'ELO'].values[0])
    elif league.casefold() == "aa" or league.casefold() == "indy":
        team1elo = int(aa_elo.loc[aa_elo['teams']==team1,'ELO'].values[0])
        team2elo = int(aa_elo.loc[aa_elo['teams']==team2,'ELO'].values[0])
    elif league.casefold() == "a" or league.casefold() == "mav":
        team1elo = int(a_elo.loc[a_elo['teams']==team1,'ELO'].values[0])
        team2elo = int(a_elo.loc[a_elo['teams']==team2,'ELO'].values[0])
    Q1 = 10**(team1elo/400)
    Q2 = 10**(team2elo/400)
    team1_win_prob = Q1/(Q1+Q2)
    team2_win_prob = Q2/(Q1+Q2)
    Q1 = 10**(team1elo/400)
    Q2 = 10**(team2elo/400)
    team1_win_prob = Q1/(Q1+Q2)
    team2_win_prob = Q2/(Q1+Q2)
    
    winner = np.random.choice([team1, team2], replace = True, p = [team1_win_prob, team2_win_prob])
    
    champion = winner

    major_elo = tempmajor.copy()
    aaa_elo = tempaaa.copy()
    aa_elo = tempaa.copy()
    a_elo = tempa.copy()
    
    # Return records for each team
    if league.casefold() == "major":
        return(major_records, playoffs, semifinals, finals, champion)
    elif league.casefold() == "aaa":
        return(aaa_records, playoffs, semifinals, finals, champion)
    elif league.casefold() == "aa":
        return(aa_records, playoffs, semifinals, finals, champion)
    elif league.casefold() == "a":
        return(a_records, playoffs, semifinals, finals, champion)
        
        
def predict_season(league, times, image=False):
    
    # Make a copy of the ELO for the league so it can be used repeatedly
    global major_elo
    global aaa_elo
    global aa_elo
    global a_elo
    majelo = major_elo.copy()
    aaaelo = aaa_elo.copy()
    aaelo = aa_elo.copy()
    aelo = a_elo.copy()
    
    # Make a list of all the teams that make playoffs
    playoffs_teams = []
    playoff_probabilities = {}
    semi_teams = []
    semi_probabilities = {}
    finals_teams = []
    finals_probabilities = {}
    champ_teams = []
    champ_probabilities = {}
    
    # Make a dictionary to track all the wins the teams get in the simulations
    predicted_records = {}
    if league.casefold() == "major":
        for team in major_teams:
            predicted_records[team] = 0
            playoff_probabilities[team] = 0
    elif league.casefold() == "aaa":
        for team in aaa_teams:
            predicted_records[team] = 0
            playoff_probabilities[team] = 0
    elif league.casefold() == "aa":
        for team in aa_teams:
            predicted_records[team] = 0
            playoff_probabilities[team] = 0
    elif league.casefold() == "a":
        for team in a_teams:
            predicted_records[team] = 0
            playoff_probabilities[team] = 0
            
    for i in range(1,times+1):
        print(f"Simulation #{i}")
        major_elo = majelo.copy()
        aaa_elo = aaaelo.copy()
        aa_elo = aaelo.copy()
        a_elo = aelo.copy()

        output = sim_schedule(league)
        sim_results = output[0]
        playoffs = output[1]
        semis = output[2]
        finals = output[3]
        champ = output[4]
        
        # Keep track of all the wins accumulated over the seasons
        for team in sim_results.index:
            predicted_records[team] += sim_results.loc[team,'Wins']
            
        # Keep track of all the playoff teams accumulated over the seasons
        playoffs_teams.extend(playoffs)
        semi_teams.extend(semis)
        finals_teams.extend(finals)
        champ_teams.append(champ)        
    
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
    
    return forecast