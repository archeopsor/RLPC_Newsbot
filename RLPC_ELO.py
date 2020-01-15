import pandas as pd

# Initial ELO for each team = 1000
def reset_elo(league=""):
    # Create a list of each team, to be added to a dictionary for each league
    major_league_teams = ["Synergy", "The Monstars", "Iced Out", "Solar Flare", "Pantheon", "Origin", "Galaxy", "Eden", "Fatal Strikers", "Comet", "Empire", "Dragon Acid Gaming", "H2O", "Distortion", "Wasted Potential", "Frosty", "Valiant", "Bread", "Helix", "Storm", "Evolution", "Ferocity", "Anarchy", "Allusion"]
    global majelo
    majelo = {}
    aaa_league_teams = ["X-Factor", "Alliance", "Hydra", "Reges", "Quantum Theory", "Titans", "Animosity", "CO2", "The Tune Squad", "Cosmos", "Clouded", "Orbit", "AfterShock", "Sun Spot", "Pure Talent", "The Snowmen", "Dauntless", "Dough Boys", "Azimuth", "Thunder", "Primal", "Lethal", "Royal", "Elusive"]
    global minelo
    minelo = {}
    indy_league_teams = ["The Godfathers", "Ace of Spades", "Insanity", "The Fruitcakes", "Genin", "Venganza", "Century", "Semi Intentional", "Mighty Wombats", "Lemonade", "Alphas", "High Volume", "Shell Shocked", "Barnstormers", "Motion", "K2", "Octane Airlines", "Eyes On Fire", "Tempest", "Flawless"]
    global indelo
    indelo = {}
    mav_league_teams = ["Mafia Esports", "Jack of Clubs", "Blizzard", "The Fruitcups", "The Academy", "Vortex", "Infinity", "Super Hopeful", "Crazy Hornets", "Apple Juice", "Kingsmen", "Rush", "Aerial Turtles", "The Aviators", "Velocity", "Broad Peak", "Scarab Speedway", "Nameless", "Spartans", "Legacy"]
    global mavelo
    mavelo = {}
    
    if league.casefold() == "major":
        for team in major_league_teams:
            majelo[team] = 1000
    elif league.casefold() == "aaa":
        for team in aaa_league_teams:
            minelo[team] = 1000
    elif league.casefold() == "aa" or league == "indy":
        for team in indy_league_teams:
            indelo[team] = 1000
    elif league.casefold() == "a" or league == "mav":
        for team in mav_league_teams:
            mavelo[team] = 1000
    else:
        for team in major_league_teams:
            majelo[team]=1000
        for team in aaa_league_teams:
            minelo[team]=1000
        for team in indy_league_teams:
            indelo[team]=1000
        for team in mav_league_teams:
            mavelo[team]=1000
            
reset_elo()

majelo = pd.DataFrame.from_dict(majelo,orient="index",columns = ['ELO'])
minelo = pd.DataFrame.from_dict(minelo,orient="index",columns = ['ELO'])
indelo = pd.DataFrame.from_dict(indelo,orient="index",columns = ['ELO'])
mavelo = pd.DataFrame.from_dict(mavelo,orient="index",columns = ['ELO'])

#Save data
def save_data(league=""):
    if league.casefold() == "major":
        majelo.to_pickle("./majelo.pkl")
    elif league.casefold() == "aaa":
        minelo.to_pickle("./minelo.pkl")
    elif league.casefold() == "aa" or league.casefold() == "indy":
        indelo.to_pickle("./indelo.pkl")
    elif league.casefold() == "a" or league.casefold() == "mav":
        mavelo.to_pickle("./mavelo.pkl")
    else:
        majelo.to_pickle("./majelo.pkl")
        minelo.to_pickle("./minelo.pkl")
        indelo.to_pickle("./indelo.pkl")
        mavelo.to_pickle("./mavelo.pkl")
    
def recall_data(league=""):
    global majelo
    global minelo
    global indelo
    global mavelo
    if league.casefold() == "major":
        majelo = pd.read_pickle("./majelo.pkl")
        print(majelo)
    elif league.casefold() == "aaa":
        minelo = pd.read_pickle("./minelo.pkl")
        print(minelo)
    elif league.casefold() == "aa" or league.casefold() == "indy":
        indelo = pd.read_pickle("./indelo.pkl")
        print(indelo)
    elif league.casefold() == "a" or league.casefold() == "mav":
        mavelo = pd.read_pickle("./mavelo.pkl")
        print(mavelo)
    else:
        majelo = pd.read_pickle("./majelo.pkl")
        minelo = pd.read_pickle("./minelo.pkl")
        indelo = pd.read_pickle("./indelo.pkl")
        mavelo = pd.read_pickle("./mavelo.pkl")
        
recall_data()
        
# Adding games via copy/paste from the sheet
def add_games_auto(league):
    data=input("Copy/paste data from spreadsheet: ")
    game_data = []
    game_data = data.split("	")
    team1 = ""
    team2 = ""
    winner = ""
    score = ""
    # Update elo
    for game in range(0,int(((len(game_data))-1)/7)):
        team1 = game_data[game*7]
        team1 = team1.lstrip()
        team1 = team1.title()
        team2 = game_data[game*7+2]
        team2 = team2.title()
        winner = game_data[game*7+3]
        score = game_data[game*7+4]
        Qa = 0
        Qb = 0
        if league.casefold() == "major":
            Qa = 10**(majelo['ELO'][team1]/400)
            Qb = 10**(majelo['ELO'][team2]/400)
        elif league.casefold() == "aaa":
            Qa = 10**(minelo['ELO'][team1]/400)
            Qb = 10**(minelo['ELO'][team2]/400)
        elif league.casefold() == "aa" or league.casefold() == "indy":
            Qa = 10**(indelo['ELO'][team1]/400)
            Qb = 10**(indelo['ELO'][team2]/400)
        elif league.casefold() == "a" or league.casefold() == "mav":
            Qa = 10**(mavelo['ELO'][team1]/400)
            Qb = 10**(mavelo['ELO'][team2]/400)
        Ea = Qa/(Qa+Qb)
        Eb = Qb/(Qa+Qb)
        Sa = 0
        Sb = 0
        if score != "FF":
            if winner == team1:
                scparts = score.split()
                Sa = int(scparts[0])/(int(scparts[0])+int(scparts[2]))
                Sb = int(scparts[2])/(int(scparts[0])+int(scparts[2]))
            elif winner == team2:
                scparts = score.split()
                Sb = int(scparts[0])/(int(scparts[0])+int(scparts[2]))
                Sa = int(scparts[2])/(int(scparts[0])+int(scparts[2]))
            elif winner == "Double FF":
                Sa = Ea
                Sb = Eb
            else:
                Sa = Ea
                Sb = Eb
        elif score == "FF":
            Sa = Ea
            Sb = Eb
        else:
            Sa = Ea
            Sb = Eb
        if league == "major":
            majelo['ELO'][team1] = majelo['ELO'][team1] + 100*(Sa - Ea)
            majelo['ELO'][team2] = majelo['ELO'][team2] + 100*(Sb - Eb)
            majelo['ELO'][team1] = round(majelo['ELO'][team1])
            majelo['ELO'][team2] = round(majelo['ELO'][team2])
        if league == "aaa":
            minelo['ELO'][team1] = minelo['ELO'][team1] + 100*(Sa - Ea)
            minelo['ELO'][team2] = minelo['ELO'][team2] + 100*(Sb - Eb)
            minelo['ELO'][team1] = round(minelo['ELO'][team1])
            minelo['ELO'][team2] = round(minelo['ELO'][team2])
        if league == "aa" or league == "indy":
            indelo['ELO'][team1] = indelo['ELO'][team1] + 100*(Sa - Ea)
            indelo['ELO'][team2] = indelo['ELO'][team2] + 100*(Sb - Eb)
            indelo['ELO'][team1] = round(indelo['ELO'][team1])
            indelo['ELO'][team2] = round(indelo['ELO'][team2])
        if league == "a" or league == "mav":
            mavelo['ELO'][team1] = mavelo['ELO'][team1] + 100*(Sa - Ea)
            mavelo['ELO'][team2] = mavelo['ELO'][team2] + 100*(Sb - Eb)
            mavelo['ELO'][team1] = round(mavelo['ELO'][team1])
            mavelo['ELO'][team2] = round(mavelo['ELO'][team2])
    
    save_data()
        
def add_games_manual(league,team1,team2,winner,score):
    score = list(score)
    score = f"{score[0]} - {score[-1]}"
    team1 = team1.title()
    team2 = team2.title()
    Qa = 0
    Qb = 0
    if league.casefold() == "major":
        Qa = 10**(majelo['ELO'][team1]/400)
        Qb = 10**(majelo['ELO'][team2]/400)
    elif league.casefold() == "aaa":
        Qa = 10**(minelo['ELO'][team1]/400)
        Qb = 10**(minelo['ELO'][team2]/400)
    elif league.casefold() == "aa" or league.casefold() == "indy":
        Qa = 10**(indelo['ELO'][team1]/400)
        Qb = 10**(indelo['ELO'][team2]/400)
    elif league.casefold() == "a" or league.casefold() == "mav":
        Qa = 10**(mavelo['ELO'][team1]/400)
        Qb = 10**(mavelo['ELO'][team2]/400)
    Ea = Qa/(Qa+Qb)
    Eb = Qb/(Qa+Qb)
    Sa = 0
    Sb = 0
    scparts = score.split()
    score1 = int(scparts[0])
    score2 = int(scparts[2])
    if score != "FF":
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
        elif winner == "Double FF":
            Sa = Ea
            Sb = Eb
        else:
            Sa = Ea
            Sb = Eb
    elif score == "FF":
        Sa = Ea
        Sb = Eb
    else:
        Sa = Ea
        Sb = Eb
    if league.casefold() == "major":
        majelo['ELO'][team1] = majelo['ELO'][team1] + 100*(Sa - Ea)
        majelo['ELO'][team2] = majelo['ELO'][team2] + 100*(Sb - Eb)
        majelo['ELO'][team1] = round(majelo['ELO'][team1])
        majelo['ELO'][team2] = round(majelo['ELO'][team2])
    if league.casefold() == "aaa":
        minelo['ELO'][team1] = minelo['ELO'][team1] + 100*(Sa - Ea)
        minelo['ELO'][team2] = minelo['ELO'][team2] + 100*(Sb - Eb)
        minelo['ELO'][team1] = round(minelo['ELO'][team1])
        minelo['ELO'][team2] = round(minelo['ELO'][team2])
    if league.casefold() == "aa" or league.casefold() == "indy":
        indelo['ELO'][team1] = indelo['ELO'][team1] + 100*(Sa - Ea)
        indelo['ELO'][team2] = indelo['ELO'][team2] + 100*(Sb - Eb)
        indelo['ELO'][team1] = round(indelo['ELO'][team1])
        indelo['ELO'][team2] = round(indelo['ELO'][team2])
    if league.casefold() == "a" or league.casefold() == "mav":
        mavelo['ELO'][team1] = mavelo['ELO'][team1] + 100*(Sa - Ea)
        mavelo['ELO'][team2] = mavelo['ELO'][team2] + 100*(Sb - Eb)
        mavelo['ELO'][team1] = round(mavelo['ELO'][team1])
        mavelo['ELO'][team2] = round(mavelo['ELO'][team2])
        
    save_data()

#Get the expected score and winner of a matchup
def exp_score(league,team1,team2,bestof=100):
    team1 = team1.title()
    team2 = team2.title()
    if league.casefold() == "major":
        team1elo = majelo['ELO'][team1]
        team2elo = majelo['ELO'][team2]
    elif league.casefold() == "aaa":
        if team1 == "Co2":
            team1 = "CO2"
        elif team2 == "Co2":
            team2 = "CO2"
        team1elo = minelo['ELO'][team1]
        team2elo = minelo['ELO'][team2]
    elif league.casefold() == "aa" or league.casefold() == "indy":
        team1elo = indelo['ELO'][team1]
        team2elo = indelo['ELO'][team2]
    elif league.casefold() == "a" or league.casefold() == "mav":
        team1elo = mavelo['ELO'][team1]
        team2elo = mavelo['ELO'][team2]
    Q1 = 10**(team1elo/400)
    Q2 = 10**(team2elo/400)
    exp_score_1 = Q1/(Q1+Q2)
    exp_score_2 = Q2/(Q1+Q2)
    if exp_score_1 > exp_score_2:
        return(f'''Winner: {team1}
Score: {str(int(round(exp_score_1*bestof)))} - {str(int(round(exp_score_2*bestof)))}''')
    elif exp_score_2 > exp_score_1:
        return(f'''Winner: {team2}
Score: {str(int(round(exp_score_2*bestof)))} - {str(int(round(exp_score_1*bestof)))}''')
    else:
        return(f'''Winner: Pure toss up)
Score: Pure toss up''')
        
def rank_teams(league):
    if league.casefold() == "major":
        return majelo.sort_values(by=['ELO'], ascending=False)
    if league.casefold() == "aaa":
        return minelo.sort_values(by=['ELO'], ascending=False)
    if league.casefold() == "aa" or league.casefold() == "indy":
        return indelo.sort_values(by=['ELO'], ascending=False)
    if league.casefold() == "a" or league.casefold() == "mav":
        return mavelo.sort_values(by=['ELO'], ascending=False)