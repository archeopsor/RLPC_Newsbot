from typing import Union
from scipy.stats import poisson
import numpy as np
from matplotlib import pyplot as plt

class PoissonDataHandler:
    def __init__(self, league: str, team1: str, team2: str):
        self.league: str = league
        self.team1: str = team1
        self.team2: str = team2

    @staticmethod
    def getAverageGoals(league: str) -> float:
        # TODO: Get average goals scored per game for the given league from the database or from the sheet

        # Temporary solution (average goals scored for each team per game in major in S14)
        return 2.47

    @staticmethod
    def getTeamGoals(league: str, team: str) -> float:
        # TODO: Get average goals scored per game for the given team

        # Temporary solution (average goals scored per game for the Hawks and Kings in S14)
        return 2.53 if team == "hawks" else 1.23

    @staticmethod
    def getAverageGA(league: str) -> float:
        # TODO: Get average goals conceded per game for the given league from the database or from the sheet

        # Temporary solution (Average goals conceded for each team per game in major in S14)
        return 2.47

    @staticmethod
    def getTeamGA(league: str, team: str) -> float:
        # TODO: Get average goals conceded per game for the given team

        # Temporary solution (Average goals conceded for the Hawks and Kings in S14)
        return 2.12 if team == "hawks" else 2.11

    def getRatings(self) -> Union[float, float]:
        avgGoals: float = self.getAverageGoals(self.league)
        avgGA: float = self.getAverageGA(self.league)

        self.avgGoals = avgGoals
        self.avgGA = avgGA

        team1OffensiveRating: float = self.getTeamGoals(self.league, self.team1) / avgGoals
        team1DefensiveRating = self.getTeamGA(self.league, self.team1) / avgGA

        team2OffensiveRating = self.getTeamGoals(self.league, self.team2) / avgGoals
        team2DefensiveRating = self.getTeamGA(self.league, self.team2) / avgGA

        self.team1Ratings = [team1OffensiveRating, team1DefensiveRating]
        self.team2Ratings = [team2OffensiveRating, team2DefensiveRating]

        return [self.team1Ratings, self.team2Ratings]

    def generatePoisson(self, show: bool = False) -> np.ndarray:
        try:
            self.team1Ratings
        except:
            self.getRatings()

        # Calculate expected goals for each team
        team1xG: float = self.team1Ratings[0] * self.team2Ratings[1] * self.avgGoals
        team2xG: float = self.team2Ratings[0] * self.team1Ratings[1] * self.avgGoals

        # Create 2d array for discrete probabilities, with team1 as columns and team2 as rows
        distribution: np.ndarray((6,6)) = np.zeros((6,6))
        for i in range(6):
            for j in range(6):
                distribution[i][j] = poisson.pmf(i, team2xG) * poisson.pmf(j, team1xG)

        if show:
            plt.imshow(distribution)
            plt.show()

        return distribution

if __name__ == "__main__":
    handler = PoissonDataHandler("major", "hawks", "kings")
    print(handler.generatePoisson())