import os
import time
from bson.objectid import ObjectId
from pandas.io.pytables import GenericTable

import pymongo

try:
    MONGO_URL = os.environ['MONGO_URL']
except:
    from passwords import MONGO_URL


class Session:
    def __init__(self):
        self.client = pymongo.MongoClient(MONGO_URL)
        self.db = self.client['rlpc-news']
        self.time_loaded = time.time()

        self.fantasy = self.db['fantasy']
        self.teams = self.db['teams']
        self.players = self.db['players']
        self.games = self.db['games']

        self.structures = {
            "players": playersStructure,
            "teams": teamsStructure,
            "fantasy": fantasyStructure,
            "games": gamesStructure,
        }

    def refresh(self):
        self.client = pymongo.MongoClient(MONGO_URL)
        self.db = self.client['rlpc-news']

        self.fantasy = self.db['fantasy']
        self.teams = self.db['teams']
        self.players = self.db['players']
        self.games = self.db['games']

    def ensure_recent(self, minutes=5):
        if (time.time() - self.time_loaded) > (60*minutes):
            self.refresh()

        return self.db

    def close(self):
        return self.client.close()

playersStructure = {
    "username": None,
    "info": {
        "region": None,
        "platform": None,
        "mmr": 0,
        "team": None, # Team ObjectId
        "league": None,
        "id": [],
        "discord_id": "",
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
    "players": [
        # ObjectId() | None,
        # ObjectId() | None,
        # ObjectId() | None,
        # ObjectId() | None,
        # ObjectId() | None,
    ],
    "player_history": [
        # {
        #     "Player": ObjectId(),    
        #     "Date in": "",
        #     "Date out": "" | None,
        #     "Points": 0,
        # }
    ],
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

teamIds = {
    'Bulls': ObjectId('60d3d012f44f81cfb194dd38'), 
    'Lions': ObjectId('60d3d0f1f44f81cfb194dd39'), 
    'Panthers': ObjectId('60d3d0faf44f81cfb194dd3a'), 
    'Sharks': ObjectId('60d3d106f44f81cfb194dd3c'), 
    'Cobras': ObjectId('60d3d122f44f81cfb194dd3d'), 
    'Ducks': ObjectId('60d3d135f44f81cfb194dd3e'), 
    'Eagles': ObjectId('60d3d13ef44f81cfb194dd3f'), 
    'Hawks': ObjectId('60d3d15ef44f81cfb194dd40'), 
    'Ascension': ObjectId('60d3d166f44f81cfb194dd41'), 
    'Flames': ObjectId('60d3d170f44f81cfb194dd42'), 
    'Storm': ObjectId('60d3d17bf44f81cfb194dd43'), 
    'Whitecaps': ObjectId('60d3d183f44f81cfb194dd44'), 
    'Kings': ObjectId('60d3d18cf44f81cfb194dd45'), 
    'Lumberjacks': ObjectId('60d3d196f44f81cfb194dd46'), 
    'Pirates': ObjectId('60d3d1a3f44f81cfb194dd47'), 
    'Spartans': ObjectId('60d3d1acf44f81cfb194dd48'),
    'Bulldogs': ObjectId('60d3d1b9f44f81cfb194dd49'), 
    'Tigers': ObjectId('60d3d1d7f44f81cfb194dd4a'), 
    'Bobcats': ObjectId('60d3d1e8f44f81cfb194dd4b'), 
    'Dolphins': ObjectId('60d3d1f2f44f81cfb194dd4c'), 
    'Vipers': ObjectId('60d3d1faf44f81cfb194dd4d'), 
    'Geese': ObjectId('60d3d208f44f81cfb194dd4e'),
    'Osprey': ObjectId('60d3d211f44f81cfb194dd4f'), 
    'Owls': ObjectId('60d3d27ef44f81cfb194dd50'), 
    'Entropy': ObjectId('60d3d285f44f81cfb194dd51'), 
    'Heat': ObjectId('60d3d292f44f81cfb194dd52'), 
    'Thunder': ObjectId('60d3dc51f44f81cfb194dd53'), 
    'Tundra': ObjectId('60d3dc5af44f81cfb194dd54'), 
    'Knights': ObjectId('60d3dcaff44f81cfb194dd55'), 
    'Pioneers': ObjectId('60d3dcb9f44f81cfb194dd56'), 
    'Raiders': ObjectId('60d3dcc2f44f81cfb194dd57'), 
    'Trojans': ObjectId('60d3dccbf44f81cfb194dd58'), 
    'Mustangs': ObjectId('60d3dcd7f44f81cfb194dd59'), 
    'Lynx': ObjectId('60d3dce3f44f81cfb194dd5a'), 
    'Jaguars': ObjectId('60d3dcedf44f81cfb194dd5b'), 
    'Barracuda': ObjectId('60d3dcf4f44f81cfb194dd5c'), 
    'Pythons': ObjectId('60d3dd02f44f81cfb194dd5d'), 
    'Herons': ObjectId('60d3dd1ef44f81cfb194dd5e'), 
    'Falcons': ObjectId('60d3dd28f44f81cfb194dd5f'), 
    'Vultures': ObjectId('60d3dd32f44f81cfb194dd60'), 
    'Pulsars': ObjectId('60d3dd52f44f81cfb194dd61'), 
    'Inferno': ObjectId('60d3dd60f44f81cfb194dd62'), 
    'Lightning': ObjectId('60d3dd73f44f81cfb194dd63'), 
    'Avalanche': ObjectId('60d3dd7cf44f81cfb194dd64'), 
    'Dukes': ObjectId('60d3dd84f44f81cfb194dd65'), 
    'Voyagers': ObjectId('60d3dd8bf44f81cfb194dd66'), 
    'Bandits': ObjectId('60d3dd94f44f81cfb194dd67'), 
    'Warriors': ObjectId('60d3dd9df44f81cfb194dd68'), 
    'Stallions': ObjectId('60d3dda8f44f81cfb194dd69'), 
    'Cougars': ObjectId('60d3ddb5f44f81cfb194dd6a'), 
    'Leopards': ObjectId('60d3ddd5f44f81cfb194dd6b'), 
    'Gulls': ObjectId('60d3ddddf44f81cfb194dd6c'), 
    'Rattlers': ObjectId('60d3dde6f44f81cfb194dd6d'), 
    'Pelicans': ObjectId('60d3ddeff44f81cfb194dd6e'), 
    'Ravens': ObjectId('60d3de0af44f81cfb194dd71'), 
    'Cardinals': ObjectId('60d3de1ef44f81cfb194dd72'),
    'Genesis': ObjectId('60d3e01ff44f81cfb194dd8b'), 
    'Embers': ObjectId('60d3de28f44f81cfb194dd73'), 
    'Tempest': ObjectId('60d3de41f44f81cfb194dd74'), 
    'Eskimos': ObjectId('60d3de4cf44f81cfb194dd75'), 
    'Jesters': ObjectId('60d3de56f44f81cfb194dd76'), 
    'Miners': ObjectId('60d3de74f44f81cfb194dd78'), 
    'Wranglers': ObjectId('60d3de7ef44f81cfb194dd79'), 
    'Titans': ObjectId('60d3de85f44f81cfb194dd7a'), 
    'Admirals': ObjectId('60d3de94f44f81cfb194dd7b'), 
    'Dragons': ObjectId('60d3de9ff44f81cfb194dd7c'), 
    'Beavers': ObjectId('60d3dea8f44f81cfb194dd7d'), 
    'Cyclones': ObjectId('60d3deb0f44f81cfb194dd7e'), 
    'Grizzlies': ObjectId('60d3deb9f44f81cfb194dd7f'),
    'Centurions': ObjectId('60d3deccf44f81cfb194dd80'), 
    'Yellow Jackets': ObjectId('60d3ded8f44f81cfb194dd81'), 
    'Galaxy': ObjectId('60d3deeaf44f81cfb194dd82'),
    'Sockeyes': ObjectId('60d3def6f44f81cfb194dd83'), 
    'Wolves': ObjectId('60d3df01f44f81cfb194dd84'), 
    'Wildcats': ObjectId('60d3df0af44f81cfb194dd85'), 
    'Rhinos': ObjectId('60d3df12f44f81cfb194dd86'), 
    'Scorpions': ObjectId('60d3df1cf44f81cfb194dd87'), 
    'Thrashers': ObjectId('60d3df25f44f81cfb194dd88'), 
    'Toucans': ObjectId('60d3df2df44f81cfb194dd89'), 
    'Wizards': ObjectId('60d3df37f44f81cfb194dd8a'), 
    'Captains': ObjectId('60d3e02bf44f81cfb194dd8c'), 
    'Yetis': ObjectId('60d3e04af44f81cfb194dd8d'), 
    'Otters': ObjectId('60d3e053f44f81cfb194dd8e'), 
    'Tides': ObjectId('60d3e05af44f81cfb194dd8f'), 
    'Pandas': ObjectId('60d3e063f44f81cfb194dd90'), 
    'Samurai': ObjectId('60d3e06cf44f81cfb194dd91'), 
    'Hornets': ObjectId('60d3e074f44f81cfb194dd92'), 
    'Solar': ObjectId('60d3e080f44f81cfb194dd93'), 
    'Piranhas': ObjectId('60d3e087f44f81cfb194dd94'), 
    'Terriers': ObjectId('60d3e094f44f81cfb194dd95'), 
    'Jackrabbits': ObjectId('60d3e0a1f44f81cfb194dd96'),
    'Zebras': ObjectId('60d3e0acf44f81cfb194dd97'), 
    'Camels': ObjectId('60d3e0b4f44f81cfb194dd98'), 
    'Raptors': ObjectId('60d3e0bcf44f81cfb194dd99'), 
    'Macaws': ObjectId('60d3e0c5f44f81cfb194dd9a'), 
    'Mages': ObjectId('60d3e0cdf44f81cfb194dd9b'), 
    'Free Agent': 'Free Agent',
    'Draftee': 'Draftee',
}

statsCategories = {
    "general": [
        "Series Played",
        "Series Won",
        "Games Played",
        "Games Won",
        "Goals",
        "Assists",
        "Saves",
        "Shots",
        "Demos Inflicted",
        "Demos Taken",
    ],
    "boost": [
        "Boost Used",
        "Wasted Collection",
        "Wasted Usage",
        "# Small Boosts",
        "# Large Boosts",
        "# Boost Steals",
        "Wasted Big",
        "Wasted Small",
    ],
    "movement": [
        "Time Slow",
        "Time Boost",
        "Time Supersonic",
    ],
    "possession": [
        "Dribbles",
        "Passes",
        "Aerials",
        "Turnovers Lost",
        "Defensive Turnovers Lost",
        "Offensive Turnovers Lost",
        "Turnovers Won",
        "Hits",
        "Flicks",
        "Clears",
    ],
    "kickoffs": [
        "Kickoffs",
        "First Touches",
        "Kickoff Cheats",
        "Kickoff Boosts",
    ],
}

def findCategory(stat: str) -> str:
    if stat in statsCategories['general']:
        return "general"
    elif stat in statsCategories["boost"]:
        return "boost"
    elif stat in statsCategories["kickoffs"]:
        return "kickoffs"
    elif stat in statsCategories["movement"]:
        return "movement"
    elif stat in statsCategories["possession"]:
        return "possession"
    else:
        return None