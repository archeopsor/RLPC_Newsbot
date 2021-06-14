import logging
import os
import time

import pandas as pd
from sqlalchemy import BigInteger, Column, Date, Integer, Text, create_engine
from sqlalchemy.dialects.postgresql import ARRAY, Any
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.schema import MetaData, Table

try: 
    DATABASE_URL = os.environ['DATABASE_URL']
except: 
    from passwords import DATABASE_URL

engine = create_engine(DATABASE_URL)
Base = declarative_base()
metadata = MetaData(bind=engine)


def select(string):
    sql = engine.connect()
    data = pd.read_sql(string, sql)
    sql.close()
    return data


class Session:
    def __init__(self, refresh_cooldown=5):
        self._session = self.loadSession()
        self.cooldown = refresh_cooldown
        
    def loadSession(self):
        S = sessionmaker(bind=engine)
        session = S()
        self.time_loaded = time.time()
        return session
    
    def refresh(self):
        self._session = self.loadSession()
        self.time_loaded = time.time()
        return self._session
    
    def ensure_recent(self, minutes=5):
        if (time.time() - self.time_loaded) > (60*minutes):
            self.refresh()
            
    @property
    def session(self):
        self.ensure_recent(self.cooldown)
        return self._session


def loadSession():
    S = sessionmaker(bind=engine)
    session = S()
    return session


class Alerts_channels(Base):
    """Holds list of channels to send alerts to"""
    __tablename__ = "alerts_channels"
    
    id = Column(BigInteger, primary_key=True)
    
    def __init__(self, id):
        self.id = id


class Elo(Base):
    """Table to hold elo data on each team"""
    __tablename__ = 'elo'
    
    League = Column(Text)
    Team = Column(Text, primary_key=True)
    elo = Column(BigInteger)
    Previous = Column(BigInteger)
    
    def __init__(self, League, Team, elo, previous):
        self.League = League
        self.Team = Team
        self.elo = elo
        self.previous = previous    


class Fantasy_players(Base):
    """Table to hold everyone's fantasy accounts, points, and teams."""
    __tablename__ = 'fantasy_players'
    
    username = Column(Text, primary_key=True)
    account_league = Column(Text)
    players = Column(ARRAY(Text))
    points = Column(ARRAY(Integer))
    transfers_left = Column(BigInteger)
    salary = Column(BigInteger)
    total_points = Column(BigInteger)
    
    def __init__(self, username, account_league, players, points, transfers_left, salary, total_points):
        self.username = username
        self.account_league = account_league
        self.players = players
        self.points = points
        self.transfers_left = transfers_left
        self.salary = salary
        self.total_points = total_points
        

class Players(Base):
    """Table to hold info and stats for each player."""
    __tablename__ = 'players'
    
    username = Column("Username", Text, primary_key=True)
    region = Column("Region", Text)
    platform = Column("Platform", Text)
    mmr = Column("MMR", BigInteger)
    team = Column("Team", Text)
    league = Column("League", Text)
    fantasy_value = Column("Fantasy Value", Integer)
    allowed = Column("Allowed?", Text)
    fantasy_points = Column("Fantasy Points", BigInteger)
    series_played = Column("Series Played", Integer)
    series_won = Column("Series Won", Integer)
    games_played = Column("Games Played", Integer)
    games_won = Column("Games Won", Integer)
    goals = Column("Goals", Integer)
    assists = Column("Assists", Integer)
    saves = Column("Saves", Integer)
    shots = Column("Shots", Integer)
    dribbles = Column("Dribbles", Integer)
    passes = Column("Passes", Integer)
    aerials = Column("Aerials", Integer)
    boost_used = Column("Boost Used", Integer)
    wasted_collection = Column("Wasted Collection", Integer)
    wasted_usage = Column("Wasted Usage", Integer)
    num_small_boosts = Column("# Small Boosts", Integer)
    num_large_boosts = Column("# Large Boosts", Integer)
    num_boost_steals = Column("# Boost Steals", Integer)
    wasted_big = Column("Wasted Big", Integer)
    wasted_small = Column("Wasted Small", Integer)
    time_slow = Column("Time Slow", Integer)
    time_boost = Column("Time Boost", Integer)
    time_supersonic = Column("Time Supersonic", Integer)
    turnovers_lost = Column("Turnovers Lost", Integer)
    defensive_turnovers_lost = Column("Defensive Turnovers Lost", Integer)
    offensive_turnovers_lost = Column("Offensive Turnovers Lost", Integer)
    turnovers_won = Column("Turnovers Won", Integer)
    hits = Column("Hits", Integer)
    kickoffs = Column("Kickoffs", Integer)
    demos_inflicted = Column("Demos Inflicted", Integer)
    demos_taken = Column("Demos Taken", Integer)
    id = Column("id", ARRAY(Text))
    first_touches = Column("First Touches", Integer)
    kickoff_cheats = Column("Kickoff Cheats", Integer)
    kickoff_boosts = Column("Kickoff Boosts", Integer)
    flicks = Column("Flicks", Integer)
    clears = Column("Clears", Integer)
    price = Column("price", Integer)
    price_history = Column("price_history", ARRAY(Integer))    
    stock_float = Column("stock_float", Integer)
    
    def __init__(self, username, region, platform, mmr, team, league, fantasy_value, allowed="Yes", fantasy_points=0, 
                 series_played=0, series_won=0, games_played=0, games_won=0, goals=0, assists=0, saves=0,
                 shots=0, dribbles=0, passes=0, aerials=0, boost_used=0, wasted_collection=0, 
                 wasted_usage=0, num_small_boosts=0, num_large_boosts=0, num_boost_steals=0, 
                 wasted_big=0, wasted_small=0, time_slow=0, time_boost=0, time_supersonic=0, 
                 turnovers_lost=0, defensive_turnovers_lost=0, offensive_turnovers_lost=0, 
                 turnovers_won=0, hits=0, kickoffs=0, demos_inflicted=0, demos_taken=0, 
                 id=None, first_touches=0, kickoff_cheats=0, kickoff_boosts=0, flicks=0, clears=0, 
                 price=0, price_history=None, stock_float=0):
        
        self.username = username
        self.region = region
        self.platform = platform
        self.mmr = mmr
        self.team = team
        self.league = league
        self.fantasy_value = fantasy_value
        self.allowed = allowed
        self.fantasy_points = fantasy_points
        self.series_played = series_played
        self.series_won= series_won
        self.games_played = games_played
        self.games_won = games_won
        self.goals = goals 
        self.assists = assists
        self.saves = saves
        self.shots = shots
        self.dribbles = dribbles
        self.passes = passes
        self.aerials = aerials
        self.boost_used = boost_used
        self.wasted_collection = wasted_collection
        self.wasted_usage = wasted_usage
        self.num_small_boosts = num_small_boosts
        self.num_large_boosts = num_large_boosts
        self.num_boost_steals = num_boost_steals
        self.wasted_big = wasted_big
        self.wasted_small = wasted_small
        self.time_slow = time_slow
        self.time_boost = time_boost
        self.time_supersonic
        self.turnovers_lost = turnovers_lost
        self.defensive_turnovers_lost = defensive_turnovers_lost
        self.offensive_turnovers_lost = offensive_turnovers_lost
        self.turnovers_won = turnovers_won
        self.hits = hits
        self.kickoffs = kickoffs
        self.demos_inflicted = demos_inflicted
        self.demos_taken = demos_taken
        self.id = id
        self.first_touches = first_touches
        self.kickoff_cheats = kickoff_cheats
        self.kickoff_boosts = kickoff_boosts
        self.flicks = flicks
        self.clears = clears
        self.price = price
        self.price_history = price_history
        self.stock_float = stock_float


class Transfer_log(Base):
    """Log of all fantasy transfers that happen"""
    __tablename__ = "transfer_log"
    
    Timestamp = Column(Text, primary_key=True)
    Account = Column(Text)
    Player_in = Column(Text)
    Player_out = Column(Text)
    
    def __init__(self, Timestamp, Account, Player_in, Player_out):
        self.Timestamp = Timestamp
        self.Account = Account
        self.Player_in = Player_in
        self.Player_out = Player_out


class Teams(Base):
    """Team stats"""
    __tablename__ = "teams"

    league = Column(Text, primary_key=True)
    team = Column(Text, primary_key=True)
    players = Column(ARRAY(Text))

    def __init__(self, league, team, players):
        self.League = league
        self.Team = team
        self.Players = players


class Game_Data(Base):
    """Stats for each series played"""
    __tablename__ = "game_data"

    game_id = Column(Integer, primary_key=True)
    gameday = Column(Date)
    league = Column(Text)
    teams = Column(ARRAY(Text))
    players = Column(ARRAY(Text))
    games = Column(Integer)
    goals = Column(ARRAY(Integer))
    assists = Column(ARRAY(Integer))
    saves = Column(ARRAY(Integer))
    shots = Column(ARRAY(Integer))

    def __init__(self, game_id, gameday, league, teams, players, games, goals, assists, saves, shots):
        self.Id = game_id
        self.Gameday = gameday
        self.League = league
        self.Teams = teams
        self.Players = players
        self.Games = games
        self.Goals = goals
        self.Assists = assists
        self.Saves = saves
        self.Shots = shots