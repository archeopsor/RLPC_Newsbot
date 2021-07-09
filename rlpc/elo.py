import numpy as np
import pandas as pd

from rlpc.players import Identifier
from tools.mongo import Session, teamIds
from settings import k, leagues

from errors.elo_errors import *


class EloHandler:
    def __init__(self, session: Session = None, identifier: Identifier = None):
        if not session:
            self.session = Session()
        else:
            self.session = session
        if not identifier:
            self.identifier = Identifier()
        else:
            self.identifier = identifier

    def get_elo(self, team: str) -> int:
        doc = self.session.teams.find_one({'team': team.title()})
        return doc['elo']['elo']

    def set_elo(self, team: str, elo: int) -> None:
        doc = self.session.teams.find_one({'team': team.title()})
        self.session.teams.find_one_and_update({"_id": doc['_id']}, {'elo.elo': elo, 'elo.previous': doc['elo']['elo']})

    def add_game_manual(self, league: str, team1: str, team2: str, winner: str, score: str) -> None:
        if 'ff' in score:
            return

        league = leagues[league.lower()]
        team1 = team1.title()
        team2 = team2.title()

        Ra = self.get_elo(team1) # Team 1 rating
        Rb = self.get_elo(team2) # Team 2 rating
        score = list(score.strip())
        score = f"{score[0]} - {score[-1]}" # Putting it in the right format
        Qa = 10**(Ra/400)
        Qb = 10**(Rb/400)
        Ea = Qa/(Qa+Qb)  # Team 1 expected score (percentage of games)
        Eb = Qb/(Qa+Qb)  # Team 2 expected score (percentage of games)
        Sa = 0  # Team 1 actual score
        Sb = 0  # Team 2 actual score
        scparts = score.split()
        score1 = int(scparts[0])
        score2 = int(scparts[2])
        if score.lower() != "ff":
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
            elif winner.lower() == "double ff":
                Sa = Ea
                Sb = Eb
            else:
                Sa = Ea
                Sb = Eb
        elif score.lower() == "ff":
            Sa = Ea
            Sb = Eb
        else:
            Sa = Ea
            Sb = Eb

        team1_rating = Ra + k*(Sa-Ea)
        team2_rating = Rb + k*(Sb-Eb)

        self.set_elo(team1, team1_rating)
        self.set_elo(team2, team2_rating)

    def predict(self, team1: str, team2: str, bestof: int = 5) -> str:
        team1 = team1.title()
        team2 = team2.title()
        try:
            league = self.identifier.find_league(team1)
        except:
            return "Could not find that team"

        if league != self.identifier.find_league(team2):
            return "Teams must be from the same league"
        
        Ra = self.get_elo(team1) # Team 1 rating
        Rb = self.get_elo(team2) # Team 2 rating
        Qa = 10**(Ra/250)
        Qb = 10**(Rb/250)
        exp_score_1 = Qa/(Qa+Qb)
        exp_score_2 = Qb/(Qa+Qb)
        firstto = round((bestof/2) + 0.51)

        wins1 = round(exp_score_1*bestof)
        wins2 = round(exp_score_2*bestof)

        if wins1 >= firstto:
            wins1 = firstto
            return f'Winner: {team1}\nScore: {wins1} - {int(wins2)}'
        elif wins2 >= firstto:
            wins2 = firstto
            return f'Winner: {team2}\nScore: {wins2} - {int(wins1)}'
        elif wins1 == wins2:
            winner = np.random.choice([team1, team2], replace=True, p=[
                                    exp_score_1, exp_score_2])
            if winner == team1:
                wins1 += 1
            elif winner == team2:
                wins2 += 1
            else:
                return "Something went catastrophically wrong with the tiebreaker game."
            if wins1 == firstto:
                return f'Winner: {team1}\nScore: {wins1} - {int(wins2)}\nSettled with a tiebreaker game'
            elif wins2 == firstto:
                return f'Winner: {team2}\nScore: {wins2} - {int(wins1)}\nSettled with a tiebreaker game'
        else:
            print(wins1, wins2, firstto)
            return "Something went catastrophically wrong, nothing seems to exist."

    def rank_teams(self, league: str) -> pd.DataFrame:
        league = leagues[league.lower()]
        lb = pd.DataFrame(columns=['Team', 'Elo', 'Previous'])
        lb.set_index('Team', inplace=True)
        teams = self.session.teams.find({'league': league})
        count = self.session.teams.count_documents({'league': league})

        if count == 0:
            return league + "appears to be an invalid league"

        for i in range(count):
            team = teams.next()
            lb.loc[team['team']] = [team['elo']['elo'], team['elo']['previous']]

        lb.sort_values(by='Elo', ascending=False, inplace=True)
        return lb

    def autoparse(self, games: str) -> None:
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

            league = self.identifier.find_league(team1)
            if league != self.identifier.find_league(team2):
                return f"{game} failed: Not same league"

            try:
                self.add_game_manual(league, team1, team2, team1, score)
            except:
                return f"{game} failed"