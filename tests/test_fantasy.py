from fantasy_infrastructure import FantasyHandler
import pandas as pd

fantasy = FantasyHandler()

def test_lb():
    assert type(fantasy.fantasy_lb()) == pd.Series