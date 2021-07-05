import unittest
from fantasy_infrastructure import FantasyHandler
import pandas as pd

fantasy = FantasyHandler()

class TestPlayers(unittest.TestCase):
    def test_lb(self):
        self.assertIsInstance(fantasy.fantasy_lb(), pd.Series)

if __name__ == '__main__':
    unittest.main()