import unittest

from passwords import TEST_BOT_TOKEN
from RLPC_Newsbot import Newsbot

class TestPlayers(unittest.TestCase):
    def test_bot(self):
        self.bot = Newsbot(TEST_BOT_TOKEN)
        self.assertIsInstance(self.bot, Newsbot)

if __name__ == '__main__':
    unittest.main()