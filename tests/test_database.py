import unittest
from tools.database import Session, select
import pandas as pd
import sqlalchemy

class TestDatabase(unittest.TestCase):
    def test_session(self):
        session = Session().session
        self.assertIsInstance(session, sqlalchemy.orm.session.Session)
        
    def test_select(self):
        players = select("players")
        self.assertIsInstance(players, pd.DataFrame)
        
if __name__ == '__main__':
    unittest.main()