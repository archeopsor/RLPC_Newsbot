from __future__ import annotations

from dataclasses import dataclass, asdict, fields
from enum import Enum
from datetime import datetime
from bson.objectid import ObjectId
import numpy as np
import pandas as pd

# Allow imports when running script from within project dir
import sys
try:
    from replay_processing.replay_classes import BallchasingReplay
except ImportError:
    pass

[sys.path.append(i) for i in ['.', '..']]

from tools.mongo import Session
from tools.sheet import Sheet
import rlpc.stats

from errors.stocks_errors import AccountNotFoundError
from settings import sheet_p4, valid_stats, current_season

###########
## UTILS ##
###########

def convert_enums(obj: dict) -> dict:
    """Recursively loops through a dictionary to reach every value and convert enums to their representative values

    Args:
        obj (dict): dictionary produced by a dataclass, containing dicts, strings, ints, floats, and Enums. 

    Returns:
        dict: The same dictionary, but with all enums converted.
    """
    if isinstance(obj, (str, int, float)):
        return obj
    elif isinstance(obj, np.int64):
        return obj.item()
    elif isinstance(obj, list):
        for i, val in enumerate(obj):
            obj[i] = convert_enums(obj[i])
    elif isinstance(obj, Enum):
        return obj.value
    elif isinstance(obj, dict):
        keys = obj.keys()
        for key in keys:
            obj[key] = convert_enums(obj[key])

    return obj

###########
## ENUMS ##
###########

class League(Enum):
    MAJOR = "Major"
    AAA = "AAA"
    AA = "AA"
    A = "A"
    INDEPENDENT = "Independent"
    MAVERICK = "Maverick"
    RENEGADE = "Renegade"
    PALADIN = "Paladin"
    OTHER = "Non-league"

    @staticmethod
    def from_str(label: str) -> League:
        if not label:
            raise NotImplementedError
        label = label.lower()
        if label == "major":
            return League.MAJOR
        elif label == "aaa":
            return League.AAA
        elif label == "aa":
            return League.AA
        elif label == "a":
            return League.A
        elif label == "independent":
            return League.INDEPENDENT
        elif label == "maverick":
            return League.MAVERICK
        elif label == "renegade":
            return League.RENEGADE
        elif label == "paladin":
            return League.PALADIN
        else:
            return League.OTHER

class JoinMethod(Enum):
    DRAFT = "draft"
    FA = "fa"
    WAITLIST = "waitlist"
    TRADE = "trade"
    OTHER = None

    @staticmethod
    def from_str(label: str) -> JoinMethod:
        if not label:
            return JoinMethod.OTHER
        label = label.lower()
        if label == "draft":
            return JoinMethod.DRAFT
        elif label == "fa":
            return JoinMethod.FA
        elif label == "waitlist":
            return JoinMethod.WAITLIST
        elif label == "trade":
            return JoinMethod.TRADE
        else:
            return JoinMethod.OTHER

class LeaveMethod(Enum):
    RELEASE = "release"
    CONTRACT = "contract"
    TRADE = "trade"
    NONPLAYING = "non-playing"
    NA = "n/a" # If the player hasn't left the team
    OTHER = None

    @staticmethod
    def from_str(label: str) -> LeaveMethod:
        if not label:
            return LeaveMethod.OTHER
        label = label.lower()
        if label == "release":
            return LeaveMethod.RELEASE
        elif label == "contract":
            return LeaveMethod.CONTRACT
        elif label == "trade":
            return LeaveMethod.TRADE
        elif label == "non-playing":
            return LeaveMethod.NONPLAYING
        else:
            return LeaveMethod.OTHER

class Region(Enum):
    NA = "NA"      # Not sure what this one is for, maybe canada?
    USE = "US-E" 
    USW = "US-W"
    USC = "US-C"
    EU = "EU"
    OTHER = None

    @staticmethod
    def from_str(label: str) -> Region:
        if not label:
            return Region.OTHER
        label = label.lower()
        if label == "na":
            return Region.NA
        elif label == "us-e":
            return Region.USE
        elif label == "us-w":
            return Region.USW
        elif label == "us-c":
            return Region.USC
        elif label == "eu":
            return Region.EU
        else:
            return Region.OTHER

class Platform(Enum):
    PC = "PC"
    XBOX = "Xbox"
    PS = "PS"
    SWITCH = "Switch"
    OTHER = None

    @staticmethod
    def from_str(label: str) -> Platform:
        if not label:
            return Platform.OTHER
        label = label.lower()
        if label == "pc":
            return Platform.PC
        elif label == "xbox":
            return Platform.XBOX
        elif label == "ps":
            return Platform.PS
        elif label == "switch":
            return Platform.SWITCH
        else:
            return Platform.OTHER

####################
## HELPER CLASSES ##
####################

@dataclass
class MMRData:
    current_official_mmr: int
    current_actual_mmr: int
    mmr_history: dict[str, int] = None # {timestamp: mmr} 

@dataclass
class TeamData:
    name: str               # Team name
    league: League
    join_season: int
    join_method: JoinMethod
    leave_season: int = None
    leave_method: LeaveMethod = None

    @classmethod
    def from_db(cls, doc: dict) -> TeamData:
        if not doc:
            return None

        if 'join_season' not in doc.keys(): # Temporary error
            doc['join_season'] = 17

        return(
            doc['name'],
            League.from_str(doc['league']),
            doc['join_season'],
            JoinMethod.from_str(doc['join_method']),
            doc['leave_season'],
            LeaveMethod.from_str(doc['leave_method'])
        )

@dataclass
class PlayerData:
    playerid: str           # Player's discord id
    join_date: datetime
    join_method: JoinMethod
    leave_date: datetime = None
    leave_method: LeaveMethod = None

@dataclass
class Stats:
    series_played: int = 0
    series_won: int = 0
    games_played: int = 0
    games_won: int = 0
    mvps: int = 0
    goals: int = 0
    assists: int = 0
    saves: int = 0
    shots: int = 0
    goals_against: int = 0
    shots_against: int = 0
    demos_inflicted: int = 0
    demos_taken: int = 0
    boost_used: int = 0
    wasted_collection: int = 0
    wasted_usage: int = 0
    num_small_boosts: int = 0
    num_large_boosts: int = 0
    num_boost_steals: int = 0
    time_empty: float = 0
    time_slow: float = 0
    time_boost: float = 0
    time_supersonic: float = 0
    time_powerslide: float = 0
    time_ground: float = 0
    time_low_air: float = 0
    time_high_air: float = 0
    time_behind_ball: float = 0
    time_infront_ball: float = 0
    time_defensive_half: float = 0
    time_offensive_half: float = 0
    time_most_back: float = 0
    time_most_forward: float = 0
    time_closest: float = 0
    time_furthest: float = 0
    conceded_when_last: int = 0

    @classmethod
    def from_db_old(cls, doc: dict, is_playoff: bool = False) -> Stats:
        stats = doc['stats' if not is_playoff else 'playoff_stats']
        try:
            general = stats['general']
        except KeyError:
            general = {
                'Series Played': 0,
                'Series Won': 0,
                'Games Played': 0,
                'Games Won': 0,
                'MVPs': 0,
                'Goals': 0,
                'Assists': 0,
                'Saves': 0,
                'Shots': 0,
                'Goals Against': 0,
                'Shots Against': 0,
                'Demos Inflicted': 0,
                'Demos Taken': 0,
            }
        try:
            boost = stats['boost']
        except KeyError:
            boost = {
                'Boost Used': 0,
                'Wasted Collection': 0,
                'Wasted Usage': 0,
                '# Small Boosts': 0,
                '# Large Boosts': 0,
                'Time Empty': 0,
            }
        try:
            movement = stats['movement']
        except KeyError:
            movement = {
            'Time Slow': 0,
            'Time Boost': 0,
            'Time Supersonic': 0,
            'Time Powerslide': 0,
            'Time Ground': 0,
            'Time Low Air': 0,
            'Time High Air': 0,
            }
        try:
            positioning = stats['positioning']
        except KeyError:
            positioning = {
            'Time Behind Ball': 0,
            'Time Infront Ball': 0,
            'Time Defensive Half': 0,
            'Time Offensive Half': 0,
            'Time Most Back': 0,
            'Time Most Forward': 0,
            'Time Closest': 0,
            'Time Furthest': 0,
            'Conceded When Last': 0,
            }

        return Stats(
            general['Series Played'],
            general['Series Won'],
            general['Games Played'],
            general['Games Won'],
            general['MVPs'],
            general['Goals'],
            general['Assists'],
            general['Saves'],
            general['Shots'],
            general['Goals Against'],
            general['Shots Against'],
            general['Demos Inflicted'],
            general['Demos Taken'],
            boost['Boost Used'],
            boost['Wasted Collection'],
            boost['Wasted Usage'],
            boost['# Small Boosts'],
            boost['# Large Boosts'],
            boost['# Boost Steals'],
            boost['Time Empty'],
            movement['Time Slow'],
            movement['Time Boost'],
            movement['Time Supersonic'],
            movement['Time Powerslide'],
            movement['Time Ground'],
            movement['Time Low Air'],
            movement['Time High Air'],
            positioning['Time Behind Ball'],
            positioning['Time Infront Ball'],
            positioning['Time Defensive Half'],
            positioning['Time Offensive Half'],
            positioning['Time Most Back'],
            positioning['Time Most Forward'],
            positioning['Time Closest'],
            positioning['Time Furthest'],
            positioning['Conceded When Last'],
        )

    @classmethod
    def from_db(cls, doc: dict) -> Stats:
        # Shortcut since this one isn't nested
        return Stats(*doc.values())

    @classmethod
    def from_series(cls, series: pd.Series) -> Stats:
        stats = Stats()
        for field in fields(stats):
            setattr(stats, field.name, series.loc[rlpc.stats.snakecase_stat(field.name, reverse=True)])
        return stats
    
    def __add__(self, stats: Stats) -> Stats:
        sum = Stats()
        for field in fields(self):
            value = getattr(self, field.name)
            additive = getattr(stats, field.name)
            setattr(sum, field.name, value + additive)

        return sum

    def to_series(self) -> pd.Series:
        df = pd.Series(index=valid_stats)
        for field in fields(self):
            value = getattr(self, field.name)
            df[field.name] = ValueError
        
        return df

@dataclass
class PlayerSeason:
    season_num: int
    teams: list[TeamData]
    season_stats: Stats
    playoff_stats: Stats
    games: list[ObjectId]
    made_playoffs: bool
    finalists: bool
    champions: bool

    @classmethod
    def from_db(cls, doc: dict) -> PlayerSeason:
        return PlayerSeason(
            doc['season_num'],
            [TeamData.from_db(team) for team in doc['teams']],
            Stats.from_db(doc['season_stats']),
            Stats.from_db(doc['playoff_stats']),
            doc['games'],
            doc['made_playoffs'],
            doc['finalists'],
            doc['champions'],
        )

    def to_dict(self) -> dict:
        return convert_enums(asdict(self))

@dataclass
class TeamSeason:
    season_num: int
    players: list[PlayerData]
    gm: str
    agm: str
    captain: str
    season_stats: Stats
    playoff_stats: Stats
    games: list[Game]
    elo_history: list[int]
    made_playoffs: bool
    finalists: bool
    champions: bool

#####################
## DATABASE MODELS ##
#####################

@dataclass
class Player:
    _id: str             # String version of player's discord id. 

    username: str
    league: League
    date_joined: datetime = None
    rl_id: list[str] = None
    tracker_links: list[str] = None
    region: Region = None
    platform: Platform = None
    mmr: MMRData = None
    current_team: str = None
    team_history: list[TeamData] = None

    seasons: list[PlayerSeason] = None

    @classmethod
    def from_db_old(cls, id: ObjectId, session: Session, sheet: Sheet) -> Player:
        doc = session.players.find_one({"_id": id})
        team = session.teams.find_one({"_id": doc['info']['team']})
        if team:
            team_data = TeamData(
                    team['team'],
                    League.from_str(team['league']),
                    17,
                    JoinMethod.OTHER,
                    None,
                    LeaveMethod.OTHER
                )
        else:
            team_data = None
        players_df = sheet.to_df('Players!A1:Z').drop_duplicates(subset="Username").set_index("Username")
        links = players_df.loc[doc['username'], "Tracker"]

        return Player(
            players_df.loc[doc['username'], 'Discord ID'],  # Some of the ids in the database were wrong for some reason
            doc['username'],
            None,
            doc['info']['id'],
            links.split(', '),
            Region.from_str(doc['info']['region']),
            Platform.from_str(doc['info']['platform']),
            MMRData(doc['info']['mmr'], doc['info']['mmr'], {datetime.now().strftime("%m/%d/%y"): doc['info']['mmr']}),
            team['team'] if team else doc['info']['team'],
            [team_data],
            [PlayerSeason(
                17, 
                [team_data],
                Stats.from_db_old(doc),
                Stats(),
                [],
                False,
                False,
                False,
            )]
        )

    @classmethod
    def from_db(cls, doc: dict) -> Player:
        if doc.get("league"):
            league = doc['league']
        else:
            league = None
        team_history = []
        if doc['team_history']:
            if doc['team_history'][0]:
                team_history = [TeamData.from_db(team) for team in doc['team_history']]
        seasons = []
        if doc['seasons']:
            seasons = [PlayerSeason.from_db(season) for season in doc['seasons']]

        return Player(
            doc['_id'],
            doc['username'],
            league,
            doc['date_joined'],
            doc['rl_id'],
            doc['tracker_links'],
            Region.from_str(doc['region']),
            Platform.from_str(doc['platform']),
            MMRData(
                doc['mmr']['current_official_mmr'],
                doc['mmr']['current_actual_mmr'],
                doc['mmr']['mmr_history']
            ),
            doc['current_team'],
            team_history,
            seasons
        )

    def insert_new(self, session: Session):
        doc = convert_enums(asdict(self))
        return session.all_players.insert_one(doc)

@dataclass
class Team:
    _id: str             # Team Name

    league: League
    current_elo: int
    previous_elo: int

    current_players: list[str] = None   # values represent players' discord ids
    previous_players: list[str] = None

    seasons: list[TeamSeason] = None

    @classmethod
    def from_db_old(cls, id: ObjectId, session: Session) -> Team:
        doc = session.teams.find_one({"_id": id})

        return Team(
            doc['team'],
            League.from_str(doc['league']),
            doc['elo']['elo'],
            doc['elo']['previous'],
        )

@dataclass
class Game:
    # Use auto-generated _id field
    date: datetime
    season: int
    team1: str
    team2: str
    team1_players: list[str]
    team2_players: list[str]
    is_playoff: bool
    score: list[int] # [Team1 score, Team2 score]
    stats: dict[str, Stats] # key is a player's discord id
    result = None

    @classmethod
    def from_replay(cls, replay: BallchasingReplay, session: Session) -> Game:
        # Make sure replay is uploaded and processed
        if not replay.processed:
            replay.process()
        data: dict = replay.stats
        player_stats, unknown = replay.player_stats
        stats: dict[str, Stats] = {}

        date = datetime.strptime(data['date'], "%Y-%m-%dT%H:%M:%S%z")
        for player in player_stats.index:
            stats[player] = Stats.from_series(player_stats.loc[player])

        team1, team2 = replay.teams
        
        return Game(
            date = date,
            season = current_season,
            team1 = team1,
            team2 = team2,
            team1_players = replay.teams[team1],
            team2_players = replay.teams[team2],
            is_playoff = False, # TODO: Find a way to detect playoff games
            score = [data['blue']['stats']['core']['goals'], data['orange']['stats']['core']['goals']],
            stats = stats,
        )

    def insert_new(self, session: Session) -> ObjectId:
        doc = convert_enums(asdict(self))
        self.result = session.games.insert_one(doc)
        return self.result.inserted_id

    def add_players(self, session: Session) -> None:
        if not self.result:
            self.insert_new(session)
        for player in [*self.team1_players, *self.team2_players]:
            session.all_players.find_one_and_update({"_id": id}, {
                "$push": {
                    "seasons.$[season].games": self.result.inserted_id,
                }
            }, array_filters = [{'season.season_num': current_season}])
        
@dataclass
class Stock_Account:
    _id: str        # Discord ID
    username: str
    balance: int
    portfolio_value: int
    value_history: dict[str, int]
    portfolio: list[dict]
    transaction_history: list[dict]

    def insert(self, session: Session):
        return session.stock_accounts.insert_one(asdict(self))

    @classmethod
    def get(cls, id: str, session: Session) -> Stock_Account:
        doc = session.stock_accounts.find_one({"_id": id})
        if doc:
            return Stock_Account(
                _id = doc['_id'],
                username = doc['username'],
                balance = doc['balance'],
                portfolio_value = doc['portfolio_value'],
                value_history = doc['value_history'],
                portfolio = doc['portfolio'],
                transaction_history = doc['transaction_history']
            )
        else:
            raise AccountNotFoundError(id)

# Just for testing
if __name__ == '__main__':
    from rlpc.players import PlayersHandler, Identifier
    from replay_processing.replay_classes import BallchasingReplay

    # session = Session()
    # identifier = Identifier(session)
    # players = PlayersHandler(session, identifier)
    # replay = BallchasingReplay(r"C:\Users\Simcha\Desktop\Replay Files\match_1\59A8F3F4445D329514F84AAE0B151F2C.replay", session, players, identifier)

    # game = Game.from_replay(replay, session)
    # res = game.insert_new(session)
    # print(res)