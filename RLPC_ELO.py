import Google_Sheets as sheet
from database import engine, select

def recall_data(league=""):
    leagues = {'major': "Major", 'aaa': 'AAA', 'aa': 'AA', 'a': 'A', 'indy': 'Independent', 'independent': 'Independent', 'mav': 'Maverick', 'maverick': 'Maverick', '': ''}
    try:
        league = leagues[league.casefold()]
    except: 
        print(f'Could not understand league {league}')
        return
    
    elo = select('elo')
    if league == '':
        return elo
    
    elo = elo.loc[elo['League']==league]
    return elo


def add_games_manual(league,team1,team2,winner,score):
    data = recall_data(league).set_index('Team')
    Ra = data.loc[team1, 'elo'] # Team 1 rating
    Rb = data.loc[team2, 'elo'] # Team 2 rating
    k = 60
    score = list(score.strip())
    score = f"{score[0]} - {score[-1]}"
    team1 = team1.title()
    team2 = team2.title()
    Qa = 10**(Ra/400)
    Qb = 10**(Rb/400)
    Ea = Qa/(Qa+Qb) # Team 1 expected score (percentage of games)
    Eb = Qb/(Qa+Qb) # Team 2 expected score (percentage of games)
    Sa = 0 # Team 1 actual score
    Sb = 0 # Team 2 actual score
    scparts = score.split()
    score1 = int(scparts[0])
    score2 = int(scparts[2])
    if score.casefold() != "ff":
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
        elif winner.casefold() == "double ff":
            Sa = Ea
            Sb = Eb
        else:
            Sa = Ea
            Sb = Eb
    elif score.casefold() == "ff":
        Sa = Ea
        Sb = Eb
    else:
        Sa = Ea
        Sb = Eb
        
    team1_rating = Ra + k*(Sa-Ea)
    team2_rating = Rb + k*(Sb-Eb)
    
    engine.execute(f"""update elo set "Previous" = {Ra} where "Team" = '{team1}'""")
    engine.execute(f"""update elo set "Previous" = {Rb} where "Team" = '{team2}'""")
    engine.execute(f"""update elo set "elo" = {team1_rating} where "Team" = '{team1}'""")
    engine.execute(f"""update elo set "elo" = {team2_rating} where "Team" = '{team2}'""")


# Get the expected score and winner of a matchup
def exp_score(league,team1,team2,bestof=100):
    elo = recall_data(league).set_index('Team')
    team1 = team1.title()
    team2 = team2.title()
    Ra = elo.loc[team1, 'elo'] # Team 1 Ratings
    Rb = elo.loc[team2, 'elo'] # Team 2 Ratings
    Qa = 10**(Ra/400)
    Qb = 10**(Rb/400)
    exp_score_1 = Qa/(Qa+Qb)
    exp_score_2 = Qb/(Qa+Qb)
    if exp_score_1 > exp_score_2:
        return(f'''Winner: {team1}
Score: {str(int(round(exp_score_1*bestof)))} - {str(int(round(exp_score_2*bestof)))}''')
    elif exp_score_2 > exp_score_1:
        return(f'''Winner: {team2}
Score: {str(int(round(exp_score_2*bestof)))} - {str(int(round(exp_score_1*bestof)))}''')
    else:
        return('''Winner: Pure toss up
Score: Pure toss up''')

        
def rank_teams(league, previous=False):
    elo = recall_data(league)
    lb = elo.sort_values(by=['elo'], ascending=False)
    lb = lb.reset_index(drop=True)
    if not previous:
        lb = lb.drop(columns=['League', 'Previous'])
    else:
        lb = lb.drop(columns=['League'])
    return lb


def autoparse(games: str):
    elo = recall_data().set_index("Team")
    games = games.split("\n")
    for game in games:
        team1 = game.split()[0].title()
        if team1 == "Yellow":
            team1 = "Yellow Jackets"
        team2 = game.split()[-1].title()
        if team2 == "Jackets":
            team2 = "Yellow Jackets"
        score = ""
        if team1 != "Yellow Jackets":
            score = game.split()[1]
        else:
            score = game.split()[2]
        league = elo.loc[team1, 'League']
        if league != elo.loc[team2, 'League']:
            return f"{game} failed: Not same league"
        try:
            add_games_manual(league, team1, team2, team1, score)
        except:
            return f"{game} failed"