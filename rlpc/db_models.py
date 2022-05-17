from dataclasses import dataclass
from enum import Enum
from datetime import datetime
from bson.objectid import ObjectId

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

class Platform(Enum):
    PC = "pc"
    XBOX = "xbox"
    PS = "ps"
    SWITCH = "switch"
    OTHER = None

####################
## HELPER CLASSES ##
####################

@dataclass
class MMRData:
    current_official_mmr: int
    current_actual_mmr: int
    mmr_history: dict[str, int] # {timestamp: mmr} 

@dataclass
class TeamData:
    name: str               # Team name
    league: League
    join_season: int
    leave_season: int
    join_method: JoinMethod
    leave_method: LeaveMethod

@dataclass
class PlayerData:
    playerid: str           # Player's discord id
    join_date: datetime
    leave_data: datetime
    join_method: JoinMethod
    leave_method: LeaveMethod

@dataclass
class Stats:
    series_played: int
    series_won: int
    games_played: int
    games_won: int
    mvps: int
    goals: int
    assists: int
    saves: int
    shots: int
    goals_against: int
    shots_against: int
    demos_inflicted: int
    demos_taken: int
    boost_used: int
    wasted_collection: int
    wasted_usage: int
    num_small_boosts: int
    num_large_boosts: int
    time_empty: float
    time_slow: float
    time_boost: float
    time_supersonic: float 
    time_powerslide: float 
    time_ground: float
    time_low_air: float
    time_high_air: float
    time_behind_ball: float
    time_infront_ball: float
    time_defensive_half: float 
    time_offensive_half: float 
    time_most_back: float
    time_most_forward: float
    time_closest: float
    time_furthest: float
    conceded_when_last: int

@dataclass
class Game:
    date: datetime
    team1: str
    team2: str
    team1_players: list[str]
    team2_players: list[str]
    is_playoff: bool
    won: bool
    score: list[int] # [Team1 score, Team2 score]
    stats: dict[str, Stats] # key is a player's discord id

@dataclass
class PlayerSeason:
    season_num: int
    teams: list[TeamData]
    season_stats: Stats
    playoff_stats: Stats
    games: list[Game]
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
    date_joined: datetime
    rl_id: list[str]
    tracker_links: list[str]
    region: Region
    platform: Platform
    mmr: MMRData
    current_team: str
    team_history: list[TeamData]

    seasons: list[PlayerSeason]


@dataclass
class Team:
    _id: str             # Team Name

    league: League
    current_players: list[str] # values represent players' discord ids
    previous_players: list[str]
    current_elo: int

    seasons: list[TeamSeason]