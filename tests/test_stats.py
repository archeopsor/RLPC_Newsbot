import unittest
import pandas as pd

from rlpc.stats import StatsHandler

statsHandler = StatsHandler()

class TestStats(unittest.TestCase):
    def test_player_stats(self):
        stats = statsHandler.get_player_stats("Zayo")
        self.assertIsInstance(stats, pd.DataFrame)

    def test_power_rankings(self):
        rankings = statsHandler.power_rankings("major")
        self.assertEqual(rankings.shape[0], 16)

    def test_stat_lb(self):
        lb = statsHandler.statlb(league = "major", pergame = True)
        self.assertIsInstance(lb, pd.Series)
        
if __name__ == '__main__':
    unittest.main()