from fantasy_infrastructure import FantasyHandler
from tools.accounts import create_account
import pandas as pd
import unittest

fantasy = FantasyHandler()

class TestFantasy(unittest.TestCase):

    def test_lb(self):
        assert type(fantasy.fantasy_lb()) == pd.Series


if __name__ == "__main__":
    unittest.main()