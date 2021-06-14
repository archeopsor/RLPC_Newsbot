from typing import Union

import numpy as np
from matplotlib import pyplot as plt
from scipy.stats import poisson
from sqlalchemy.sql.expression import false

from tools.database import Session, Teams, Game_Data

from settings import leagues


class PoissonDataHandler:
    def __init__(self, league: str, team1: str, team2: str):
        self.league: str = leagues[league.lower()]
        self.team1: str = team1
        self.team2: str = team2
        self.session = Session().session

    def getAverageGoals(self) -> float:
        data = self.session.query(Game_Data).filter(Game_Data.league == self.league)
        
        goals_sum = 0
        games_sum = 0
        for game in data.all():
            games_sum += game.games
            goals_sum += sum(game.goals)

        return goals_sum / (2 * games_sum)

    def getTeamGoals(self, team: str) -> float:
        team = team.title()
        data = self.session.query(Game_Data).filter(team == Game_Data.teams.any_())

        if data.count() == 0:
            raise IOError("No data for team " + team)
        
        goals_sum = 0
        games_sum = 0
        for game in data.all():
            games_sum += game.games
            if game.teams[0] == team:
                goals_sum += sum(game.goals[0:3])
            else:
                goals_sum += sum(game.goals[-3:])

        return goals_sum / games_sum

    def getAverageGA(self) -> float:
        # This will be the same as average goals
        return self.getAverageGoals()

    def getTeamGA(self, team: str) -> float:
        team = team.title()
        data = self.session.query(Game_Data).filter(team == Game_Data.teams.any_())
        
        goals_sum = 0
        games_sum = 0
        for game in data.all():
            games_sum += game.games
            if game.teams[1] == team:
                goals_sum += sum(game.goals[0:2])
            else:
                goals_sum += sum(game.goals[3:5])
                
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
    handler = PoissonDataHandler("Major", "hawks", "kings")
    handler.generatePoisson(show=False)
    print(sum(handler.getOneWayPoisson()[1]))
