from rlpc.players import Session, Players, Identifier
import pymongo
import unittest

session = Session()
players = Players()
identifier = Identifier()


class TestPlayers(unittest.TestCase):
    def test_client(self):
        self.assertIsInstance(session.client, pymongo.MongoClient)
        
    def test_identify(self):
        self.assertEqual("bdong", identifier.identify("76561199015415785"))

    def test_checks(self):
        players.check_players()
        players.download_ids()
        
if __name__ == '__main__':
    unittest.main()