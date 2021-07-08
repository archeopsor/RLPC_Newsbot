import pytest
import discord.ext.test as dpytest

from RLPC_Newsbot import Newsbot
from passwords import TEST_BOT_TOKEN

@pytest.fixture
def bot(event_loop):
    bot = Newsbot(TEST_BOT_TOKEN, loop=event_loop)
    dpytest.configure(bot)
    return bot


def pytest_sessionfinish():
    """Runs after all tests are finished, can be used to delete changes"""
    pass