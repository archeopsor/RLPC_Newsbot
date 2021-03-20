import numpy as np
from PIL import Image, ImageDraw, ImageFont
from numba import jit, types
from numba.experimental import jitclass

from rlpc import elo

from tools.sheet import gsheet2df, get_google_sheet

@jitclass
class structures:
    def __init__(self, league):
        self.league = league.lower()
        assert (self.league in ['major', 'aaa', 'aa', 'a', 'independent', 'maverick', 'renegade', 'paladin']), f"{league} is not valid."
        
        self.winloss = gsheet2df(get_google_sheet("1Tlc_TgGMrY5aClFF-Pb5xvtKrJ1Hn2PJOLy2fUDDdFI","Team Wins!A1:AE17"))
        self.records = self.get_records()
        self.teams = self.records.index.to_numpy()
        self.divisions = self.get_divisions()
        self.ratings = self.get_elo()
        self.schedule = self.get_schedule()
    
    @staticmethod
    def capitalize_league(league):
        if league in ['major', 'independent', 'maverick', 'renegade', 'paladin']:
            return league.title()
        elif league in ['aaa', 'aa', 'a']:
            return league.upper()
        
    def get_records(self):
        winloss = self.winloss
        league = self.league
        
        if league == "major":
            records = winloss.iloc[:, 0:3].set_index("Major Teams").astype('int')
        elif league == "aaa":
            records = winloss.iloc[:, 4:7].set_index("AAA Teams").astype('int')
        elif league == "aa":
            records = winloss.iloc[:, 8:11].set_index("AA Teams").astype('int')
        elif league == "a":
            records = winloss.iloc[:, 12:15].set_index("A Teams").astype('int')
        elif league == "independent":
            records = winloss.iloc[:, 16:19].set_index("Indy Teams").astype('int')
        elif league == "maverick":
            records = winloss.iloc[:, 20:23].set_index("Mav Teams").astype('int')
        elif league == "renegade":
            records = winloss.iloc[:, 24:27].set_index("Renegade Teams").astype('int')
        elif league == "paladin":
            records = winloss.iloc[:, 28:31].set_index("Paladin Teams").astype('int')
        
        return records
    
    def get_divisions(self):
        return {'Sharks': 'Predator', 'Bulls': 'Predator', 'Panthers': 'Predator', 'Lions': 'Predator', 
                 'Whitecaps': 'Elements', 'Storm': 'Elements', 'Flames': 'Elements', 'Ascension': 'Elements',
                 'Eagles': 'Wild', 'Hawks': 'Wild', 'Ducks': 'Wild', 'Cobras': 'Wild',
                 'Lumberjacks': 'Brawler', 'Kings': 'Brawler', 'Pirates': 'Brawler', 'Spartans': 'Brawler',
                 'Bobcats': 'Predator', 'Bulldogs': 'Predator', 'Dolphins': 'Predator', 'Tigers': 'Predator',
                 'Heat': 'Elements', 'Tundra': 'Elements', 'Entropy': 'Elements', 'Thunder': 'Elements',
                 'Osprey': 'Wild', 'Vipers': 'Wild', 'Geese': 'Wild', 'Owls': 'Wild',
                 'Knights': 'Brawler', 'Trojans': 'Brawler', 'Pioneers': 'Brawler', 'Raiders': 'Brawler',
                 'Mustangs': 'Predator', 'Jaguars': 'Predator', 'Lynx': 'Predator', 'Barracuda': 'Predator',
                 'Avalanche': 'Elements', 'Inferno': 'Elements', 'Lightning': 'Elements', 'Pulsars': 'Elements',
                 'Herons': 'Wild', 'Pythons': 'Wild', 'Falcons': 'Wild', 'Vultures': 'Wild',
                 'Warriors': 'Brawler', 'Voyagers': 'Brawler', 'Bandits': 'Brawler', 'Dukes': 'Brawler',
                 'Stallions': 'Predator', 'Cougars': 'Predator', 'Leopards': 'Predator', 'Gulls': 'Predator',
                 'Tempest': 'Elements', 'Embers': 'Elements', 'Eskimos': 'Elements', 'Genesis': 'Elements',
                 'Ravens': 'Wild', 'Pelicans': 'Wild', 'Rattlers': 'Wild', 'Cardinals': 'Wild',
                 'Titans': 'Brawler', 'Miners': 'Brawler', 'Jesters': 'Brawler', 'Wranglers': 'Brawler',
                 'Beavers': 'Predator', 'Dragons': 'Predator', 'Cyclones': 'Predator', 'Admirals': 'Predator', 
                 'Wolves': 'Elements', 'Wildcats': 'Elements', 'Rhinos': 'Elements', 'Sockeyes': 'Elements',
                 'Galaxy': 'Wild', 'Centurions': 'Wild', 'Grizzlies': 'Wild', 'Yellow Jackets': 'Wild',
                 'Scorpions': 'Brawler', 'Toucans': 'Brawler', 'Thrashers': 'Brawler', 'Wizards': 'Brawler',
                 'Tides': 'Predator', 'Yetis': 'Predator', 'Otters': 'Predator', 'Captains': 'Predator',
                 'Terriers': 'Elements', 'Jackrabbits': 'Elements', 'Zebras': 'Elements', 'Piranhas': 'Elements',
                 'Samurai': 'Wild', 'Hornets': 'Wild', 'Solar': 'Wild', 'Pandas': 'Wild', 
                 'Macaws': 'Brawler', 'Camels': 'Brawler', 'Raptors': 'Brawler', 'Mages': 'Brawler',
                 'Pilots': 'Predator', 'Wolverines': 'Predator', 'Werewolves': 'Predator', 'Hurricanes': 'Predator',
                 'Gorillas': 'Elements', 'Stingrays': 'Elements', 'Warthogs': 'Elements', 'Hounds': 'Elements',
                 'Vikings': 'Wild', 'Koalas': 'Wild', 'Comets': 'Wild', 'Fireflies': 'Wild',
                 'Harriers': 'Brawler', 'Coyotes': 'Brawler', 'Puffins': 'Brawler', 'Witches': 'Brawler',
                 'Griffins': 'Predator', 'Quakes': 'Predator', 'Sailors': 'Predator', 'Badgers': 'Predator',
                 'Wildebeests': 'Elements', 'Hammerheads': 'Elements', 'Jackals': 'Elements', 'Foxes': 'Elements',
                 'Dragonflies': 'Wild', 'Cosmos': 'Wild', 'Ninjas': 'Wild', 'Cubs': 'Wild',
                 'Roadrunners': 'Brawler', 'Penguins': 'Brawler', 'Buzzards': 'Brawler', 'Sorcerers': 'Brawler'}

    def get_elo(self):
        return elo.recall_data(self.league).set_index("Team")['elo'].astype(int)

    def get_schedule(self):
        schedule = []
        if self.league in ['major', 'aaa', 'aa', 'a']:
            sheet_schedule = gsheet2df(get_google_sheet("1AJoBYkYGMIrpe8HkkJcB25DbLP2Z-eV7P6Tk9R6265I", str(self.league)+' Schedule!N4:V'))
        elif self.league in ['independent', 'maverick', 'renegade', 'paladin']:
            sheet_schedule = gsheet2df(get_google_sheet("1bWvgo_YluMbpQPheldQQZdASKGHRPIUVfYL2r2KSdaE", str(self.league)+' Schedule!N4:V'))
        for row in sheet_schedule.index:
            if sheet_schedule.loc[row, "Winner"] == '':
                game = sheet_schedule.iloc[row, 2]+' - '+sheet_schedule.iloc[row, 4]
                schedule.append(game)

        return np.array(schedule)
    
    
    
@jitclass
class simulation:
    def __init__(self, league, schedule, records, elo):
        self.league = league
        self.schedule = schedule.copy()
        self.records = records.copy()
        self.teams = self.records.index.to_numpy()
        
    
        
@jitclass
class sim_manager:
    
    def __init__(self, league, times, image=False, official=False):
        self.structs = structures(league)
        self.league = structures.capitalize_league(league)
        self.schedule = self.structs.schedule
        self.records = self.structs.records
        self.ratings = self.structs.ratings
        self.times = times
        
        self.playoff_teams = np.array([])
        self.semi_teams = np.array([])
        self.finals_teams = np.array([])
        self.champ_teams = np.array([])
        
    #@numba.jit
    def run_sim(self):
        predicted_records = {}
        for team in self.structs.teams:
            predicted_records[team] = 0
            
        for i in range(1, self.times+1):
            print("Simulation #"+str(i)+"     "+self.league)
            
            sim = simulation(self.league, self.schedule, self.records, self.ratings)
            
            
            