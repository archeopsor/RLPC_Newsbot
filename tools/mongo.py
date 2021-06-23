import pymongo

from database import *

client = pymongo.MongoClient("mongodb+srv://Simi:SdR8Ub7m6XUm9Pe@rlpc-news.puvzm.mongodb.net/myFirstDatabase?retryWrites=true&w=majority")
db = client['rlpc-news']

fantasy = db['fantasy']
teams = db['teams']
players = db['players']
games = db['games']

playersStructure = {
    "username": None,
    "info": {
        "region": None,
        "platform": None,
        "mmr": 0,
        "team": None,
        "league": None,
        "id": [],
        "discord_id": 0,
    },
    "fantasy": {
        "fantasy_value": 0,
        "fantasy_points": 0,
        "allowed": True
    },
    "stats": {
        "general": {
            "Series Played": 0,
            "Series Won": 0,
            "Games Played": 0,
            "Games Won": 0,
            "Goals": 0,
            "Assists": 0,
            "Saves": 0,
            "Shots": 0,
            "Demos Inflicted": 0,
            "Demos Taken": 0,
        }, 
        "boost": {
            "Boost Used": 0,
            "Wasted Collection": 0,
            "Wasted Usage": 0,
            "# Small Boosts": 0,
            "# Large Boosts": 0,
            "# Boost Steals": 0,
            "Wasted Big": 0,
            "Wasted Small": 0,
        },
        "movement": {
            "Time Slow": 0,
            "Time Boost": 0,
            "Time Supersonic": 0,
        },
        "possession": {
            "Dribbles": 0,
            "Passes": 0,
            "Aerials": 0,
            "Turnovers Lost": 0,
            "Defensive Turnovers Lost": 0,
            "Offensive Turnovers Lost": 0,
            "Turnovers Won": 0,
            "Hits": 0,
            "Flicks": 0,
            "Clears": 0,
        },
        "kickoffs": {
            "Kickoffs": 0,
            "First Touches": 0,
            "Kickoff Cheats": 0,
            "Kickoff Boosts": 0,
        }
    },
    "playoff_stats": {
        "general": {
            "Series Played": 0,
            "Series Won": 0,
            "Games Played": 0,
            "Games Won": 0,
            "Goals": 0,
            "Assists": 0,
            "Saves": 0,
            "Shots": 0,
            "Demos Inflicted": 0,
            "Demos Taken": 0,
        }, 
        "boost": {
            "Boost Used": 0,
            "Wasted Collection": 0,
            "Wasted Usage": 0,
            "# Small Boosts": 0,
            "# Large Boosts": 0,
            "# Boost Steals": 0,
            "Wasted Big": 0,
            "Wasted Small": 0,
        },
        "movement": {
            "Time Slow": 0,
            "Time Boost": 0,
            "Time Supersonic": 0,
        },
        "possession": {
            "Dribbles": 0,
            "Passes": 0,
            "Aerials": 0,
            "Turnovers Lost": 0,
            "Defensive Turnovers Lost": 0,
            "Offensive Turnovers Lost": 0,
            "Turnovers Won": 0,
            "Hits": 0,
            "Flicks": 0,
            "Clears": 0,
        },
        "kickoffs": {
            "Kickoffs": 0,
            "First Touches": 0,
            "Kickoff Cheats": 0,
            "Kickoff Boosts": 0,
        }
    },
}

teamsStructure = {
    "team": None,
    "league": None,
    "players": [],
    "stats": {
        "general": {
            "Series Played": 0,
            "Series Won": 0,
            "Games Played": 0,
            "Games Won": 0,
            "Goals": 0,
            "Assists": 0,
            "Saves": 0,
            "Shots": 0,
            "Demos Inflicted": 0,
            "Demos Taken": 0,
        }, 
        "boost": {
            "Boost Used": 0,
            "Wasted Collection": 0,
            "Wasted Usage": 0,
            "# Small Boosts": 0,
            "# Large Boosts": 0,
            "# Boost Steals": 0,
            "Wasted Big": 0,
            "Wasted Small": 0,
        },
        "movement": {
            "Time Slow": 0,
            "Time Boost": 0,
            "Time Supersonic": 0,
        },
        "possession": {
            "Dribbles": 0,
            "Passes": 0,
            "Aerials": 0,
            "Turnovers Lost": 0,
            "Defensive Turnovers Lost": 0,
            "Offensive Turnovers Lost": 0,
            "Turnovers Won": 0,
            "Hits": 0,
            "Flicks": 0,
            "Clears": 0,
        },
        "kickoffs": {
            "Kickoffs": 0,
            "First Touches": 0,
            "Kickoff Cheats": 0,
            "Kickoff Boosts": 0,
        }
    },
    "playoff_stats": {
        "general": {
            "Series Played": 0,
            "Series Won": 0,
            "Games Played": 0,
            "Games Won": 0,
            "Goals": 0,
            "Assists": 0,
            "Saves": 0,
            "Shots": 0,
            "Demos Inflicted": 0,
            "Demos Taken": 0,
        }, 
        "boost": {
            "Boost Used": 0,
            "Wasted Collection": 0,
            "Wasted Usage": 0,
            "# Small Boosts": 0,
            "# Large Boosts": 0,
            "# Boost Steals": 0,
            "Wasted Big": 0,
            "Wasted Small": 0,
        },
        "movement": {
            "Time Slow": 0,
            "Time Boost": 0,
            "Time Supersonic": 0,
        },
        "possession": {
            "Dribbles": 0,
            "Passes": 0,
            "Aerials": 0,
            "Turnovers Lost": 0,
            "Defensive Turnovers Lost": 0,
            "Offensive Turnovers Lost": 0,
            "Turnovers Won": 0,
            "Hits": 0,
            "Flicks": 0,
            "Clears": 0,
        },
        "kickoffs": {
            "Kickoffs": 0,
            "First Touches": 0,
            "Kickoff Cheats": 0,
            "Kickoff Boosts": 0,
        }
    },
    "elo": {
        "elo": 0,
        "previous": 0,
    },
}

fantasyStructure = {
    "username": None,
    "discord_id": 0,
    "account_league": "",
    "players": {
        # username: 0,
    },
    "player_history": {
        # username: {
        #     "Date in": "",
        #     "Date out": "",
        #     "points": 0,
        # }
    },
    "salary": 0,
    "transfers_left": 2,
    "transfer_log": [
        {
            "Timestamp": "",
            "Player_in": {
                "username": "",
                "salary": 0,
                "points": 0,
            },
            "Player_out": {
                "username": "",
                "salary": 0,
            }
        }
    ]
}

gamesStructure = {
    "gameday": "",
    "league": "",
    "teams": {
        "team1": {
            "players": [
                {
                    "username": "",
                    "stats": {
                        "general": {
                            "Series Played": 0,
                            "Series Won": 0,
                            "Games Played": 0,
                            "Games Won": 0,
                            "Goals": 0,
                            "Assists": 0,
                            "Saves": 0,
                            "Shots": 0,
                            "Demos Inflicted": 0,
                            "Demos Taken": 0,
                        }, 
                        "boost": {
                            "Boost Used": 0,
                            "Wasted Collection": 0,
                            "Wasted Usage": 0,
                            "# Small Boosts": 0,
                            "# Large Boosts": 0,
                            "# Boost Steals": 0,
                            "Wasted Big": 0,
                            "Wasted Small": 0,
                        },
                        "movement": {
                            "Time Slow": 0,
                            "Time Boost": 0,
                            "Time Supersonic": 0,
                        },
                        "possession": {
                            "Dribbles": 0,
                            "Passes": 0,
                            "Aerials": 0,
                            "Turnovers Lost": 0,
                            "Defensive Turnovers Lost": 0,
                            "Offensive Turnovers Lost": 0,
                            "Turnovers Won": 0,
                            "Hits": 0,
                            "Flicks": 0,
                            "Clears": 0,
                        },
                        "kickoffs": {
                            "Kickoffs": 0,
                            "First Touches": 0,
                            "Kickoff Cheats": 0,
                            "Kickoff Boosts": 0,
                        },
                    }
                }
            ],
        "score": 0,
        "won": False,
        }
    },
    "playoff": False,
}
