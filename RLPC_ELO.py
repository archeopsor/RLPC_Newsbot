import Google_Sheets as sheet
from database import engine, select
import numpy as np
from RLPC_Players import find_league

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
def exp_score(team1,team2,bestof=5):
    players = select('players')
    team1 = team1.title()
    team2 = team2.title()
    try:
        league = find_league(team1, players)
    except:
        return "Could not find that team"
    if league != find_league(team2, players):
        return "Teams must be from the same league"
    elo = recall_data(league).set_index('Team')
    Ra = elo.loc[team1, 'elo'] # Team 1 Ratings
    Rb = elo.loc[team2, 'elo'] # Team 2 Ratings
    Qa = 10**(Ra/400)
    Qb = 10**(Rb/400)
    exp_score_1 = Qa/(Qa+Qb)
    exp_score_2 = Qb/(Qa+Qb)
    firstto = round((bestof/2) + 0.51)
    wins1 = [0]
    wins2 = [0]
    for i in range(1000):
        while wins1[i] < firstto and wins2[i] < firstto:
            winner = np.random.choice([team1, team2], replace=True, p=[exp_score_1, exp_score_2])
            if winner == team1:
                wins1[i] += 1
            elif winner == team2:
                wins2[i] += 1
            else:
                return f"Something went catastrophically wrong, game {wins1+wins2+1} didn't have a winner."
      
        wins1.append(0)
        wins2.append(0)
        
    wins1 = wins1[:-1]
    wins2 = wins2[:-1]
    print(np.mean(wins1), np.mean(wins2))
    wins1 = np.mean(wins1)
    wins2 = np.mean(wins2)
    
    residual = (bestof-(wins1+wins2))
    
    wins1 = int(round(wins1+(residual*exp_score_1)))
    wins2 = int(round(wins2+(residual*exp_score_2)))
    
    if wins1 >= firstto:
        wins1 = firstto
        return f'Winner: {team1}\nScore: {wins1} - {wins2}'
    elif wins2 >= firstto:
        wins2 = firstto
        return f'Winner: {team2}\nScore: {wins2} - {wins1}'
    elif wins1 == wins2:
        winner = np.random.choice([team1, team2], replace=True, p=[exp_score_1, exp_score_2])
        if winner == team1:
            wins1 += 1
        elif winner == team2:
            wins2 += 1
        else:
            return "Something went catastrophically wrong with the tiebreaker game."
        if wins1 == firstto:
            return f'Winner: {team1}\nScore: {wins1} - {wins2}'
        elif wins2 == firstto:
            return f'Winner: {team2}\nScore: {wins2} - {wins1}'
    else:
        print(wins1, wins2, firstto)
        return "Something went catastrophically wrong, nothing seems to exist."

        
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