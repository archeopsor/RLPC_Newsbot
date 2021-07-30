from typing import Union

import numpy as np
from matplotlib import pyplot as plt
import scipy
from scipy.stats._discrete_distns import poisson
import pandas as pd

from tools.mongo import Session, teamIds
from tools.sheet import Sheet

from settings import leagues, sheet_indy, sheet_p4

from errors.general_errors import LeagueNotFoundError


class SheetsPoisson:
    def __init__(self, p4sheet: Sheet = None, indysheet: Sheet = None):
        if not p4sheet:
            self.p4sheet = Sheet(sheet_p4)
        else:
            self.p4sheet = p4sheet
        if not indysheet:
            self.indysheet = Sheet(sheet_indy)
        else:
            self.indysheet = indysheet

    def getData(self, league) -> pd.DataFrame:
        sheet = self.p4sheet if league.lower() in ['major', 'aaa', 'aa', 'a'] else self.indysheet
        data = sheet.to_df(f"{leagues[league.lower()]} Game Logs!B1:M")
        data = data[data['Matchup'] != '']
        data = data.apply(pd.to_numeric, errors='coerce').fillna(data)
        return data

    def getAverageGoals(self, league) -> float:
        if league.lower() not in leagues.keys():
            raise LeagueNotFoundError(league)
        
        data = self.getData(league)

        goals = data['Goals'].sum()
        games = data['Total Games'].sum() / 6       # 6 players per game

        return goals / (2 * games)                  # Average goals scored per game by *one* team (that's why the 2 is needed)

    def getTeamGoals(self, team: str, league: str) -> float:
        team = team.title()
        if league.lower() not in leagues.keys():
            raise LeagueNotFoundError(league)
        
        data = self.getData(league)

        data = data[data['Team'] == team]

        goals = data['Goals'].sum()
        games = data['Total Games'].sum() / 3             # 3 players per team per game

        return goals / games

    def getAverageGA(self, league) -> float:
        # This will be the same as average goals
        return self.getAverageGoals(league)

    def getTeamGA(self, team: str, league: str) -> float:
        team = team.title()
        if league.lower() not in leagues.keys():
            raise LeagueNotFoundError(league)

        data = self.getData(league)

        data = data[data['Matchup'].str.contains(team) & data['Team'] != team]

        goals = data['Goals'].sum()
        games = data['Total Games'].sum() / 3             # 3 players per team per game

        return goals / games

    def getRatings(self, team1: str, team2: str, league: str) -> Union[float, float]:
        avgGoals: float = self.getAverageGoals(league)
        avgGA: float = self.getAverageGA(league)

        team1OffensiveRating: float = self.getTeamGoals(team1, league) / avgGoals
        team1DefensiveRating: float = self.getTeamGA(team1, league) / avgGA

        team2OffensiveRating: float = self.getTeamGoals(team2, league) / avgGoals
        team2DefensiveRating: float = self.getTeamGA(team2, league) / avgGA

        team1Ratings = [team1OffensiveRating, team1DefensiveRating]
        team2Ratings = [team2OffensiveRating, team2DefensiveRating]

        return (team1Ratings, team2Ratings, avgGoals, avgGA)

    def generatePoisson(self, team1: str, team2: str, league: str, show: bool = False):
        team1Ratings, team2Ratings, avgGoals, avgGA = self.getRatings(team1, team2, league)

        # Calculate expected goals for each team
        team1xG: float = team1Ratings[0] * team2Ratings[1] * avgGoals
        team2xG: float = team2Ratings[0] * team1Ratings[1] * avgGoals

        # Create 2d array for discrete probabilities, with team1 as columns and team2 as rows
        distribution: np.ndarray((6, 6)) = np.zeros((6, 6))
        for i in range(6):
            for j in range(6):
                team1p = poisson.pmf(j, team1xG)
                team2p = poisson.pmf(i, team2xG)
                if j == 5:
                    team1p = 1 - poisson.cdf(5, team1xG)
                if i == 5:
                    team2p = 1 - poisson.cdf(5, team2xG)

                distribution[i][j] = team1p * team2p

        if show:
            plt.imshow(distribution)
            plt.show()

        return (distribution, team1xG, team2xG)

    def getOneWayPoisson(self, league: str, team1: str, team2: str) -> Union[list, list]:
        dist, team1xG, team2xG = self.generatePoisson(team1, team2, league)

        team1Poisson = []
        team2Poisson = []
        for i in range(5):
            team1Poisson.append(poisson.pmf(i, team1xG))
            team2Poisson.append(poisson.pmf(i, team2xG))

        team1Poisson.append(1-poisson.cdf(4, team1xG))
        team2Poisson.append(1-poisson.cdf(4, team2xG))

        return (team1Poisson, team2Poisson)
        


class PoissonDataHandler:
    def __init__(self, league: str, team1: str, team2: str, session: Session = None):
        self.league: str = leagues[league.lower()]
        self.team1: str = team1
        self.team2: str = team2
        if not session:
            self.session = Session()
        else:
            self.session = session

    def getAverageGoals(self) -> float:
        data = self.session.games.find({'league': self.league})
        count = self.session.games.count_documents({'league': self.league})

        if count == 0:
            raise IOError("No data for league " + self.league)
        
        goals_sum = 0
        games_sum = 0
        for i in range(count):
            game = data.next()
            games_sum += game["games"]
            goals_sum += game['teams'][0]['score']
            goals_sum += game['teams'][1]['score']

        return goals_sum / (2 * games_sum)

    def getTeamGoals(self, team: str) -> float:
        team = team.title()
        teamId = teamIds[team]
        data = self.session.games.find({'teams': {'team': teamIds(team)}})
        count = self.session.games.count_documents({'teams': {'team': teamId}})

        if count == 0:
            raise IOError("No data for team " + team)
        
        goals_sum = 0
        games_sum = 0
        for game in range(count):
            game = data.next()
            games_sum += game['games']
            if game['teams'][0]['team'] == teamId:
                goals_sum += game['teams'][0]['score']
            else:
                goals_sum += game['teams'][1]['score']

        return goals_sum / games_sum

    def getAverageGA(self) -> float:
        # This will be the same as average goals
        return self.getAverageGoals()

    def getTeamGA(self, team: str) -> float:
        team = team.title()
        teamId = teamIds[team]
        data = self.session.games.find({'teams': {'team': teamIds(team)}})
        count = self.session.games.count_documents({'teams': {'team': teamId}})
        
        goals_sum = 0
        games_sum = 0
        for game in range(count):
            game = data.next()
            games_sum += game['games']
            if game['teams'][1]['team'] == teamId: # This is the only line different from getTeamGoals
                goals_sum += game['teams'][0]['score']
            else:
                goals_sum += game['teams'][1]['score']
                
        return goals_sum / games_sum

    def getRatings(self) -> Union[float, float]:
        avgGoals: float = self.getAverageGoals()
        avgGA: float = self.getAverageGA()

        self.avgGoals = avgGoals
        self.avgGA = avgGA

        team1OffensiveRating: float = self.getTeamGoals(self.team1) / avgGoals
        team1DefensiveRating = self.getTeamGA(self.team1) / avgGA

        team2OffensiveRating = self.getTeamGoals(self.team2) / avgGoals
        team2DefensiveRating = self.getTeamGA(self.team2) / avgGA

        self.team1Ratings = [team1OffensiveRating, team1DefensiveRating]
        self.team2Ratings = [team2OffensiveRating, team2DefensiveRating]

        return [self.team1Ratings, self.team2Ratings]

    def generatePoisson(self, show: bool = False) -> np.ndarray:
        try:
            self.team1Ratings
            self.team2Ratings
        except AttributeError:
            self.getRatings()

        # Calculate expected goals for each team
        team1xG: float = self.team1Ratings[0] * \
            self.team2Ratings[1] * self.avgGoals
        team2xG: float = self.team2Ratings[0] * \
            self.team1Ratings[1] * self.avgGoals

        # Create 2d array for discrete probabilities, with team1 as columns and team2 as rows
        distribution: np.ndarray((6, 6)) = np.zeros((6, 6))
        for i in range(6):
            for j in range(6):
                team1p = poisson.pmf(j, team1xG)
                team2p = poisson.pmf(i, team2xG)
                if j == 5:
                    team1p = 1 - poisson.cdf(5, team1xG)
                if i == 5:
                    team2p = 1 - poisson.cdf(5, team2xG)

                distribution[i][j] = team1p * team2p

        if show:
            plt.imshow(distribution)
            plt.show()

        self.dist = distribution
        self.team1xG = team1xG
        self.team2xG = team2xG

        return distribution

    def getOneWayPoisson(self) -> Union[list, list]:
        try:
            self.distribution
        except AttributeError:
            self.generatePoisson()
        
        team1Poisson = []
        team2Poisson = []
        for i in range(5):
            team1Poisson.append(poisson.pmf(i, self.team1xG))
            team2Poisson.append(poisson.pmf(i, self.team2xG))

        team1Poisson.append(1-poisson.cdf(4, self.team1xG))
        team2Poisson.append(1-poisson.cdf(4, self.team2xG))

        return [team1Poisson, team2Poisson]

if __name__ == "__main__":
    handler = SheetsPoisson()
    print(handler.getOneWayPoisson("Major", "Hawks", "Flames"))
