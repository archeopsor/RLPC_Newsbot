from fantasy_infrastructure import FantasyHandler
import pandas as pd
import unittest

fantasy = FantasyHandler()

class TestFantasy(unittest.TestCase):

    def test_lb(self):
        assert type(fantasy.fantasy_lb()) == pd.Series