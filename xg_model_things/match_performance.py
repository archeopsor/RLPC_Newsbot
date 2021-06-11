from typing import Union
import numpy as np
from replay_processing.replays import Replay


class MatchPerformance:
    def __init__(self, replay: Replay):
        self.replay = replay
        self.team1 = replay.get_teams[0]
        self.team2 = replay.get_teams[1]

    def adjusted_goals(self) -> Union[int, int]:
        stats = self.replay.stats
        
        # TODO: For every player advantage the scoring team has for each goal, subtract 0.1 goals, and add 0.1 for disadvantage
        
        # TODO: Scale late goals and goals with a lead
        # Rules for this: 
            # If a team has a 2+ goal lead, cut any goals by half
            # If a team is down by 3+ goals, scale any goals by 0.75
            # If a team is not tied or down by one, any goals scored in the last 30 seconds are decreased by 0.2

        # TODO: Increase all goals by 0.05

    def shot_based_xG(self) -> Union[int, int]:
        stats = self.replay.stats

        # TODO: Create xG model and use it here

    def non_shot_xG(self) -> Union[int, int]:
        stats = self.replay.stats

        # TODO: Count hits and time in attacking 3rd for each team and create a metric for this

    def get_match_performance(self) -> Union[int, int]:
        adjusted = self.adjusted_goals()
        shot_based = self.shot_based_xG()
        non_shot = self.non_shot_xG()

        team1_goals = adjusted[0] + shot_based[0] + non_shot[0]
        team2_goals = adjusted[1] + shot_based[1] + non_shot[1]

        return [team1_goals, team2_goals]