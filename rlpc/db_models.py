from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from datetime import datetime
from bson.objectid import ObjectId

# Allow imports when running script from within project dir
import sys
[sys.path.append(i) for i in ['.', '..']]

from tools.mongo import Session
from tools.sheet import Sheet
from settings import sheet_p4

###########
## ENUMS ##
###########

class League(Enum):
    MAJOR = "major"
    AAA = "aaa"
    AA = "aa"
    A = "a"
    INDEPENDENT = "independent"
    MAVERICK = "maverick"
    RENEGADE = "renegade"
    PALADIN = "paladin"

    @staticmethod
    def from_str(label: str) -> League:
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
            raise NotImplementedError

class JoinMethod(Enum):
    DRAFT = "draft"
    FA = "fa"
    WAITLIST = "waitlist"
    TRADE = "trade"
    OTHER = None

class LeaveMethod(Enum):
    RELEASE = "release"
    CONTRACT = "contract"
    TRADE = "trade"
    NA = "n/a" # If the player hasn't left the team
    OTHER = None

class Region(Enum):
    NA = "NA"      # Not sure what this one is for, maybe canada?
    USE = "US-E" 
    USW = "US-W"
    USC = "US-C"
    EU = "EU"
    OTHER = None

    @staticmethod
    def from_str(label: str) -> Region:
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
    PC = "pc"
    XBOX = "xbox"
    PS = "ps"
    SWITCH = "switch"
    OTHER = None

    @staticmethod
    def from_str(label: str) -> Platform:
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

@dataclass
class PlayerData:
    playerid: str           # Player's discord id
    join_date: datetime
    leave_data: datetime
    join_method: JoinMethod
    leave_method: LeaveMethod

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

@dataclass
class TeamSeason:
    season_num: int
    players: list[TeamData]
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
    elo_history: list[int]

#####################
## DATABASE MODELS ##
#####################

@dataclass
class Player:
    _id: str             # String version of player's discord id. 

    username: str
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
    def from_db_old(cls, id: ObjectId) -> Player:
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
        players_df = sheet.to_df('Players!A1:R')
        links = players_df.loc[players_df['Username'] == doc['username'], "Tracker"].values[0]

        return Player(
            doc['info']['discord_id'],
            doc['username'],
            None,
            doc['info']['id'],
            links.split(', '),
            Region.from_str(doc['info']['region']),
            Platform.from_str(doc['info']['platform']),
            MMRData(doc['info']['mmr'], doc['info']['mmr']),
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
    def from_db_old(cls, id: ObjectId) -> Team:
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
    team1: str
    team2: str
    team1_players: list[str]
    team2_players: list[str]
    is_playoff: bool
    won: bool
    score: list[int] # [Team1 score, Team2 score]
    stats: dict[str, Stats] # key is a player's discord id


# Just for testing
if __name__ == '__main__':
    session = Session()
    sheet = Sheet(sheet_p4)
    players = []
    teams = []

    cursor = session.players.find({})
    while cursor.alive:
        players.append(Player.from_db_old(cursor.next()['_id']))

    cursor = session.teams.find({})
    while cursor.alive:
        teams.append(Team.from_db_old(cursor.next()['_id']))

    cursor.close()