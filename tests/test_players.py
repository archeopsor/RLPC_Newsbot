from rlpc.players import Session, PlayersHandler, Identifier
import pymongo
import unittest

session = Session()
players = PlayersHandler()
identifier = Identifier()


class TestPlayers(unittest.TestCase):
    # def test_checks(self):
    #     players.check_players()
    #     players.download_ids()

    def test_client(self):
        self.assertIsInstance(session.client, pymongo.MongoClient)
        
    def test_find_league(self):
        self.assertEqual("Major", identifier.find_league("Hawks"))

    def test_find_team(self):#
        self.assertEqual("Genesis", identifier.find_team(['SpadL', 'Computer', 'Zero']))

    def test_identify(self):#
        self.assertEqual("bdong", identifier.identify("76561199015415785"))

    def test_tracker_identify(self):
        self.assertEqual("Lil Uzi Yurt", identifier.tracker_identify("OhWaitWhy"))
        
if __name__ == '__main__':
    unittest.main()