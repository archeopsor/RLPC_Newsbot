import os
import time
from bson.objectid import ObjectId
from pandas.io.pytables import GenericTable

import pymongo

try:
    from passwords import MONGO_URL
except:
    MONGO_URL = os.environ['MONGO_URL']


class Session:
    def __init__(self):
        self.client = pymongo.MongoClient(MONGO_URL)
        self.db = self.client['rlpc-news']
        self.time_loaded = time.time()

        self.fantasy = self.db['fantasy']
        self.teams = self.db['old_teams']
        self.players = self.db['players']
        self.all_players = self.db['all_players']
        self.games = self.db['games']
        self.admin = self.db['admin']

        self.structures = {
            "players": playersStructure,
            "teams": teamsStructure,
            "fantasy": fantasyStructure,
            "games": gamesStructure,
        }

    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.close()

    def refresh(self):
        self.close()

        self.client = pymongo.MongoClient(MONGO_URL)
        self.db = self.client['rlpc-news']

        self.fantasy = self.db['fantasy']
        self.teams = self.db['teams']
        self.players = self.db['players']
        self.games = self.db['games']
        self.admin = self.db['admin']

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
        "team": None,  # Team ObjectId
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
            "MVPs": 0,
            "Goals": 0,
            "Assists": 0,
            "Saves": 0,
            "Shots": 0,
            "Goals Against": 0,
            "Shots Against": 0,
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
            "Time Empty": 0,
        },
        "movement": {
            "Time Slow": 0,
            "Time Boost": 0,
            "Time Supersonic": 0,
            "Time Powerslide": 0,
            "Time Ground": 0,
            "Time Low Air": 0,
            "Time High Air": 0,
        },
        "positioning": {
            "Time Behind Ball": 0,
            "Time Infront Ball": 0,
            "Time Defensive Half": 0,
            "Time Offensive Half": 0,
            "Time Most Back": 0,
            "Time Most Forward": 0,
            "Time Closest": 0,
            "Time Furthest": 0,
            "Conceded When Last": 0,
        },
    },
    "playoff_stats": {
        "general": {
            "Series Played": 0,
            "Series Won": 0,
            "Games Played": 0,
            "Games Won": 0,
            "MVPs": 0,
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
            "Time Empty": 0,
        },
        "movement": {
            "Time Slow": 0,
            "Time Boost": 0,
            "Time Supersonic": 0,
            "Time Powerslide": 0,
            "Time Ground": 0,
            "Time Low Air": 0,
            "Time High Air": 0,
        },
        "positioning": {
            "Time Behind Ball": 0,
            "Time Infront Ball": 0,
            "Time Defensive Half": 0,
            "Time Offensive Half": 0,
            "Time Most Back": 0,
            "Time Most Forward": 0,
            "Time Closest": 0,
            "Time Furthest": 0,
            "Conceded When Last": 0,
        },
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
    "discord_id": None,
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
    "points": 0,
    "transfer_log": [
        # {
        #     "Timestamp": "",
        #     "Type": "", # in | out
        #     "Player": {
        #         "id": ObjectId(""),
        #         "salary": 0,
        #         "points": 0,
        #     },
        # }
    ]
}

gamesStructure = {
    "gameday": "",
    "league": "",
    "playoff": False,
    "teams": [],
    "games": 0,
}

teamIds = {
    'Bulls': ObjectId('619719ebc11e66b1891284ef'),
    'Lions': ObjectId('61971a72c11e66b1891284f0'),
    'Panthers': ObjectId('61971a80c11e66b1891284f1'),
    'Sharks': ObjectId('61971a9ac11e66b1891284f2'),
    'Cobras': ObjectId('61971aa8c11e66b1891284f3'),
    'Ducks': ObjectId('61971ac6c11e66b1891284f4'),
    'Eagles': ObjectId('61971ad2c11e66b1891284f5'),
    'Hawks': ObjectId('61971ae5c11e66b1891284f6'),
    'Ascension': ObjectId('61971af2c11e66b1891284f7'),
    'Flames': ObjectId('61971afdc11e66b1891284f8'),
    'Storm': ObjectId('61971b0dc11e66b1891284f9'),
    'Whitecaps': ObjectId('61971b19c11e66b1891284fa'),
    'Kings': ObjectId('61971b26c11e66b1891284fb'),
    'Lumberjacks': ObjectId('61971b3ac11e66b1891284fc'),
    'Pirates': ObjectId('61971b49c11e66b1891284fd'),
    'Spartans': ObjectId('61971b5cc11e66b1891284fe'),
    'Bulldogs': ObjectId('61971b75c11e66b1891284ff'),
    'Tigers': ObjectId('61971b85c11e66b189128500'),
    'Bobcats': ObjectId('61971b9dc11e66b189128501'),
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
    # 'Eskimos': ObjectId('60d3de4cf44f81cfb194dd75'),
    'The Snowmen': ObjectId('6195a4650f00b7e2e3acc0e3'),
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
    'Comets': ObjectId('626af7dc8b46d2aa975c6c5b'),
    'Coyotes': ObjectId('626af80e8b46d2aa975c6c5c'),
    'Fireflies': ObjectId('626af81d8b46d2aa975c6c5d'),
    'Gorillas': ObjectId('626af82f8b46d2aa975c6c5e'),
    'Harriers': ObjectId('626af8d30a07ea96acc1941d'),
    'Hounds': ObjectId('626af9100a07ea96acc1941e'),
    'Hurricanes': ObjectId('626af9230a07ea96acc1941f'),
    'Koalas': ObjectId('626af93b0a07ea96acc19420'),
    'Pilots': ObjectId('626af94d0a07ea96acc19421'),
    'Puffins': ObjectId('626af97f0a07ea96acc19422'),
    'Stingrays': ObjectId('626af9950a07ea96acc19423'),
    'Vikings': ObjectId('626af9a20a07ea96acc19424'),
    'Warthogs': ObjectId('626af9bd0a07ea96acc19425'),
    'Werewolves': ObjectId('626af9c90a07ea96acc19426'),
    'Witches': ObjectId('626af9e60a07ea96acc19427'),
    'Wolverines': ObjectId('626afa000a07ea96acc19428'),
    'Free Agent': 'Free Agent',
    'Draftee': 'Draftee',
    'Not Playing': 'Not Playing',
    'Departed': 'Departed'
}

statsCategories = {
    "general": [
        "Series Played",
        "Series Won",
        "Games Played",
        "Games Won",
        "MVPs",
        "Goals",
        "Assists",
        "Saves",
        "Shots",
        "Goals Against", 
        "Shots Against",
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
        "Time Empty", 
    ],
    "movement": [
        "Time Slow",
        "Time Boost",
        "Time Supersonic",
        "Time Powerslide", 
        "Time Ground", 
        "Time Low Air", 
        "Time High Air",
    ],
    "positioning": [
        "Time Behind Ball",
        "Time Infront Ball", 
        "Time Defensive Half",
        "Time Offensive Half", 
        "Time Most Back", 
        "Time Most Forward",
        "Time Closest",
        "Time Furthest", 
        "Conceded When Last",
    ],
}


def findCategory(stat: str) -> str:
    if stat in statsCategories['general']:
        return "general"
    elif stat in statsCategories["boost"]:
        return "boost"
    elif stat in statsCategories["movement"]:
        return "movement"
    elif stat in statsCategories["positioning"]:
        return "positioning"
    else:
        return None
