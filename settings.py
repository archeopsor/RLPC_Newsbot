prefix = '$'
k = 40
sheet_p4 = '17tPXpZACXlqrCS3gYo59C5gbZyp3oguVdjwsgWQJkcA'
sheet_indy = '1Ef08kD375wbs5VHm_EFQw3C6k4dt7Aw69wyDfVKGVHc'
test_sheet = '1gHlqD-xekmpwFDpblAiJfpuCvxRliK6C-AjYoEUU8tc'
power_rankings_sheet = '1Tlc_TgGMrY5aClFF-Pb5xvtKrJ1Hn2PJOLy2fUDDdFI'
gdstats_sheet = '1DU14mG8jHh2AG8ol16iYpUvXDjTHFgt7Kwe7CIoxRxU'
forecast_sheet = '1GEFufHK5xt0WqThYC7xaK2gz3cwjinO43KOsb7HogQQ'
valid_stats = ['Series Played' , 'Series Won' , 'Games Played' , 'Games Won' , 'Goals' , 'Assists' , 'Saves' , 'Shots' , 'Dribbles' , 'Passes' , 'Aerials' , 'Boost Used' , 'Wasted Collection' , 'Wasted Usage' , '# Small Boosts' , '# Large Boosts' , '# Boost Steals' , 'Wasted Big' , 'Wasted Small' , 'Time Slow' , 'Time Boost' , 'Time Supersonic' , 'Turnovers Lost' , 'Defensive Turnovers Lost' , 'Offensive Turnovers lost' , 'Turnovers Won' , 'Hits' , 'Kickoffs' , 'Demos Inflicted' , 'Demos Taken' , 'First Touches' , 'Kickoff Cheats' , 'Kickoff Boosts' , 'Flicks' , 'Clears']
leagues = {'major': "Major", 'aaa': 'AAA', 'aa': 'AA', 'a': 'A', 'indy': 'Independent', 'independent': 'Independent', 'mav': 'Maverick', 'maverick': 'Maverick', 'renegade': 'Renegade', 'ren': 'Renegade', 'paladin': 'Paladin', 'pal': 'Paladin'}
divisions = {'Sharks': 'Predator', 'Bulls': 'Predator', 'Panthers': 'Predator', 'Lions': 'Predator', 
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

