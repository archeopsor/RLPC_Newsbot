import discord
from discord.ext import commands
from PIL import Image, ImageDraw, ImageFont
import pandas as pd
import numpy as np

from rlpc import stats, mmr
from rlpc.players import find_league

from tools import sheet
from tools.database import select

from settings import prefix

client = commands.Bot(command_prefix = prefix)

valid_stats = ['Series Played' , 'Series Won' , 'Games Played' , 'Games Won' , 'Goals' , 'Assists' , 'Saves' , 'Shots' , 'Dribbles' , 'Passes' , 'Aerials' , 'Boost Used' , 'Wasted Collection' , 'Wasted Usage' , '# Small Boosts' , '# Large Boosts' , '# Boost Steals' , 'Wasted Big' , 'Wasted Small' , 'Time Slow' , 'Time Boost' , 'Time Supersonic' , 'Turnovers Lost' , 'Defensive Turnovers Lost' , 'Offensive Turnovers lost' , 'Turnovers Won' , 'Hits' , 'Kickoffs' , 'Demos Inflicted' , 'Demos Taken' , 'First Touches' , 'Kickoff Cheats' , 'Kickoff Boosts' , 'Flicks' , 'Clears']

class Stats(commands.Cog):
    
    def __init__(self,client):
        self.client = client
        
    @commands.command(aliases = ('power', 'powerrankings', 'power_rankings', 'rankings', 'ranking',))
    async def pr(self, ctx, league):
        async with ctx.typing():
            if league.casefold() == "major":
                league = "Major"
            elif league.casefold() in ["indy", "independent"]:
                league = "Independent"
            elif league.casefold() in ['mav', 'maverick']:
                league = "Maverick"
            elif league.casefold() in ['ren', 'renegade']:
                league = "Renegade"
            elif league.casefold() in ['pal', 'paladin']:
                league = "Paladin"
            else:
                league = league.upper()
            rankings = stats.power_rankings(league)
            embed = discord.Embed(title = f'{league} Power Rankings', description = f"Official human-generated Power Rankings for {league}. For computer rankings, use $rank", color=0x000080)

            value_response = ''
            for row in range(16):
                value_response += f"{row+1}: {rankings.index[row]}"
                if rankings.iloc[row] == rankings.iloc[(row+1 if row < 15 else 0)] or rankings.iloc[row] == rankings.iloc[(row-1 if row > 0 else 15)]:
                    value_response += f"ᵀ ({rankings.iloc[row]})\n"
                else:
                    value_response += f" ({rankings.iloc[row]})\n"
            
            embed.add_field(name="Rankings", value=value_response)

            await ctx.send(embed=embed)
            
    @pr.error
    async def prerror(self, ctx, error):
        if isinstance(error,commands.MissingRequiredArgument):
            await ctx.send("You haven't chosen a league.")
    
    @commands.command()
    async def mmr(self, ctx, *, player):
        async with ctx.typing():
            players = sheet.gsheet2df(sheet.get_google_sheet('1AJoBYkYGMIrpe8HkkJcB25DbLP2Z-eV7P6Tk9R6265I', 'Players!A1:R'))
            
            # Remove case-sensitivity
            lower_players = players['Username'].str.lower()
            if player.casefold() in lower_players.values:
                pindex = lower_players[lower_players == player.casefold()].index[0]
                player = players.loc[pindex][0]
            players = players.reset_index()
            
            mmrs = {}
            try:
                players.loc[player]
            except: 
                await ctx.send(f"Coudn't find player {player}")
                return

            for url in players.loc[player, 'Tracker'].split(", "):
                platform, name = url.split('/')[-2:]
                mmrs[name] = {}
                mmrs[name]['Duels'] = mmr.playlist(platform, name, '1s')
                mmrs[name]['Doubles'] = mmr.playlist(platform, name, '2s')
                mmrs[name]['Solo Standard'] = mmr.playlist(platform, name, 'ss')
                mmrs[name]['Standard'] = mmr.playlist(platform, name, '3s')
            
                embed = discord.Embed(title=f"{player}'s MMRs", color=0xffffff)
                for playlist in list(mmrs[name]):
                    embed.add_field(name=playlist, value=f'{mmrs[name][playlist]["rank"]} ({mmrs[name][playlist]["rating"]})')
                
                await ctx.send(embed=embed)
    
    @commands.command(aliases=("getstats","stats","get_stats",))
    async def get_player_stats(self, ctx, *, msg):
        async with ctx.typing():
            if msg.casefold() == "me":
                waitingMsg = await ctx.send("One second, retreiving discord ID and stats")
                msg = str(ctx.author.id)
                ids = sheet.gsheet2df(sheet.get_google_sheet('1AJoBYkYGMIrpe8HkkJcB25DbLP2Z-eV7P6Tk9R6265I', 'PlayerIDs!A1:B')).set_index('Discord ID')
                try:
                    msg = ids.loc[msg, 'Username']
                except:
                    return await ctx.send("You don't appear to have an up-to-date discord id on record. Try using the name that shows up on the RLPC spreadsheet.")
                await waitingMsg.delete(delay=5)
            first = " ".join(msg.split()[:-1])
            last = msg.split()[-1]
            try: 
                answer = stats.get_player_stats(first, last)
                if answer == 'That stat could not be understood.':
                    raise Exception
            except: 
                try: 
                    answer = stats.get_player_stats(msg)
                except: 
                    await ctx.send(f"Cound not find player {msg}")
                    return

            try:
                embed = discord.Embed(title=f"{answer.values[0][0]}'s Stats", color=0x3333ff)
            except:
                return await ctx.send(f"Could not find {msg}'s stats. Contact arco if you think this is a bug")
            for i, col in enumerate(answer.columns[1:]):
                embed.add_field(name=col, value=answer.values[0][i+1])
        await ctx.send(embed=embed)
        
        
    @commands.command(aliases=("topstats", "statslb", "stats_lb",))
    async def top(self, ctx, *, msg):
        async with ctx.typing():
            # Default arguments
            useSheet = False
            league = "all"
            stat = "Points Per Game"
            limit = 10
    
        
    @commands.command(aliases=("probs","prob","probability", "probabilities"))
    async def forecast(self, ctx, *, msg):
        async with ctx.typing():
            msg = msg.split()
            league = "none"
            team = "none"
            part = "none"
            
            for word in msg:
                if word.casefold() in ["major","aaa","aa","a","independent", "indy", "mav",'maverick', 'renegade','ren','paladin','pal']:
                    league = word.casefold()
                    if league == "indy":
                        league = "independent"
                    elif league == 'mav':
                        league = 'maverick'
                    elif league == 'ren':
                        league = 'renegade'
                    elif league == 'pal':
                        league = 'paladin'
                elif word.casefold() in ['bulls', 'lions', 'panthers', 'sharks', 'cobras', 'ducks', 'eagles', 'hawks', 'ascension', 'flames', 'storm', 'whitecaps', 'kings', 'lumberjacks', 'pirates', 'spartans', 'bulldogs', 'tigers', 'bobcats', 'dolphins', 'vipers', 'geese', 'osprey', 'owls', 'entropy', 'heat', 'thunder', 'tundra', 'knights', 'pioneers', 'raiders', 'trojans', 'mustangs', 'lynx', 'jaguars', 'barracuda', 'pythons', 'herons', 'falcons', 'vultures', 'pulsars', 'inferno', 'lightning', 'avalanche', 'dukes', 'voyagers', 'bandits', 'warriors', 'stallions', 'cougars', 'leopards', 'gulls', 'rattlers', 'pelicans', 'ravens', 'cardinals', 'genesis', 'embers', 'tempest', 'eskimos', 'jesters', 'miners', 'wranglers', 'titans', 'admirals', 'dragons', 'beavers', 'cyclones', 'grizzlies', 'centurions', 'yellow jackets', 'galaxy', 'sockeyes', 'wolves', 'wildcats', 'rhinos', 'scorpions', 'thrashers', 'toucans', 'wizards', 'captains', 'yetis', 'otters', 'tides', 'pandas', 'samurai', 'hornets', 'solar', 'piranhas', 'terriers', 'jackrabbits', 'zebras', 'camels', 'raptors', 'macaws', 'mages', 'pilots', 'werewolves', 'wolverines', 'hurricanes', 'koalas', 'vikings', 'fireflies', 'comets', 'stingrays', 'hounds', 'warthogs', 'gorillas', 'coyotes', 'harriers', 'puffins', 'witches', 'sailors', 'griffins', 'badgers', 'quakes', 'cubs', 'ninjas', 'dragonflies', 'cosmos', 'hammerheads', 'foxes', 'jackals', 'wildebeests', 'roadrunners', 'buzzards', 'penguins', 'sorcerers']:
                    team = word
                elif word.casefold() in ["wins","expected wins","record","playoffs","playoff","semifinals","semifinal","finals","final","finalist","champions","champion","winners","winner"]:
                    part = word
                    if part in ['playoff', 'semifinal', 'final', 'champion']:
                        part += 's'
                    elif part in ['wins', 'record']:
                        part = 'expected wins'
                    elif part == 'finalist':
                        part = 'finals'
                    elif part in ['winners', 'winner']:
                        part = 'champions'
    
            if league == "none" and team == "none":
                await ctx.send("You haven't chosen a league. You can also see all of the data here: <https://docs.google.com/spreadsheets/d/1GEFufHK5xt0WqThYC7xaK2gz3cwjinO43KOsb7HogQQ/edit?usp=sharing>")
                return
            elif league == "none" and team != "none":
                waitingMsg = await ctx.send(f'Finding league for team "{team}"...', )
                league = find_league(team.title(), select("players")).lower()
                waitingMsg.delete()
            elif league == "major":
                gsheet = sheet.get_google_sheet("1GEFufHK5xt0WqThYC7xaK2gz3cwjinO43KOsb7HogQQ", "Most Recent!A2:F18")
            elif league == "aaa":
                gsheet = sheet.get_google_sheet("1GEFufHK5xt0WqThYC7xaK2gz3cwjinO43KOsb7HogQQ", "Most Recent!A21:F37")
            elif league == "aa":
                gsheet = sheet.get_google_sheet("1GEFufHK5xt0WqThYC7xaK2gz3cwjinO43KOsb7HogQQ", "Most Recent!A40:F56")
            elif league == "a":
                gsheet = sheet.get_google_sheet("1GEFufHK5xt0WqThYC7xaK2gz3cwjinO43KOsb7HogQQ", "Most Recent!A59:F75")
            elif league == "independent":
                gsheet = sheet.get_google_sheet("1GEFufHK5xt0WqThYC7xaK2gz3cwjinO43KOsb7HogQQ", "Most Recent!A78:F94")
            elif league == "maverick":
                gsheet = sheet.get_google_sheet("1GEFufHK5xt0WqThYC7xaK2gz3cwjinO43KOsb7HogQQ", "Most Recent!A97:F113")
            elif league == "renegade":
                gsheet = sheet.get_google_sheet("1GEFufHK5xt0WqThYC7xaK2gz3cwjinO43KOsb7HogQQ", "Most Recent!A116:F132")
            elif league == "paladin":
                gsheet = sheet.get_google_sheet("1GEFufHK5xt0WqThYC7xaK2gz3cwjinO43KOsb7HogQQ", "Most Recent!A135:F151")
            
            data = sheet.gsheet2df(gsheet).set_index('Teams')
    
            
            
            if team == "none" and part == "none": 
                
                # if 'graph' in [x.lower() for x in msg]: # Returns a stacked bar graph rather than image with numbers
                #     new_data = pd.DataFrame(data.index).set_index("Teams", inplace=True)
                #     new_data['Champions'] = data['Champions']
                #     new_data['Finals'] = data['Finals'] - data['Champions']
                #     new_data['Semifinals'] = data['Semifinals'] - data['Finals']
                #     new_data['Playoffs'] = data['Playoffs'] - data['Semifinals']
                #     new_data['No Playoffs'] = 1 - data['Playoffs']
                #     new_data = new_data.sort_values(by="No Playoffs", ascending=False)
                #     plot = new_data.plot(kind='barh', stacked=True, title="Major Forecast", colormap='YlGn_r')
                #     plot.set_xlabel("Probability")
                #     plot.xaxis.grid(True)
                
                # else:
                #     template = Image.open(f"./Image_templates/Forecast Table.png")
                #     img = ImageDraw.Draw(template)
                #     titlefont = ImageFont.truetype('C:/Windows/Fonts/palab.ttf', size=100)
                #     w, h = template.size
                    
                #     colors = {'major': 'limegreen', 'aaa': 'dodgerblue', 'aa': 'red', 'a': 'yellow', 'independent': 'mediumpurple', 'maverick': 'orange', 'renegade': 'powderblue', 'paladin': 'orchid'}
                #     img.text((w/2-img.textsize(f"{league} Forecast", font=titlefont)[0]/2, 50), f"{league} Forecast", font=titlefont, fill=colors[league])
                    
                    
                message = f"""
╔═══════╦══════╦═════╦═══════╗ 
║ Teams        ║ Record    ║ Playoffs ║ Champions ║"""
                for team in data.index.values:
                    wins = str(data.loc[team, 'Expected Wins'])
                    playoffs = str(data.loc[team, 'Playoffs'])
                    champs = str(data.loc[team, 'Champions'])
                    message = message + f"\n╠═══════╬══════╬═════╬═══════╣\n║ {team+('  '*(9-len(team)))} ║ {wins+('  '*(8-len(wins)))} ║ {playoffs+('  '*(8-len(playoffs)))} ║ {champs+('  '*(10-len(champs)))} ║"
                message = message + "\n╚═══════╩══════╩═════╩═══════╝"
                embed=discord.Embed()
                embed.set_footer(text=message)
                await ctx.send(embed=embed) # TODO: Fix Formatting
                return
            
            if team != "none":
                data = data.loc[team.title()]
                
            if part != "none":
                data = data[part.title()]
                
            await ctx.send(data)
            await ctx.send("See all of the data here: <https://docs.google.com/spreadsheets/d/1GEFufHK5xt0WqThYC7xaK2gz3cwjinO43KOsb7HogQQ/edit?usp=sharing>")
        
    @forecast.error
    async def probabilities_error(self,ctx,error):
        if isinstance(error,commands.MissingRequiredArgument):
            await ctx.send("You haven't chosen a league. You can also see all of the data here: https://docs.google.com/spreadsheets/d/1GEFufHK5xt0WqThYC7xaK2gz3cwjinO43KOsb7HogQQ/edit?usp=sharing")

    @commands.command(aliases=("gameday_stats",))
    async def gdstats(self, ctx, *, msg):
        async with ctx.typing():
            player = "me"
            day = '1'
            stat = None
            pergame = False
            
            msg = msg.split(' ')
            used_args = []
            
            for i, arg in enumerate(msg):
                try:
                    day = str(int(arg)) # Ensure that it's an integer
                    used_args.append(arg)
                    continue
                except:
                    pass
                if arg == 'me':
                    used_args.append(arg)
                elif 'gd' in arg:
                    try:
                        day = str(int(arg.split('gd')[-1])) # Ensure that it's an integer
                        used_args.append(arg)
                    except:
                        pass
                elif arg == 'pg': 
                    pergame = True
                    used_args.append(arg)
                elif arg.lower() in [x.split()[0].lower() for x in valid_stats]: # First word of a stat
                    stat = arg.title()
                    used_args.append(arg)
                    if len(msg) == i+1: # If that was the last arg in the msg
                        break
                    if msg[i+1].lower() in [x.split()[1].lower() if len(x.split())>1 else None for x in valid_stats]: # Second word
                        stat = stat + ' ' + msg[i+1].title()
                        used_args.append(msg[i+1])
                        if len(msg) == i+2: # If the next arg is the last arg in the msg
                            break
                        if msg[i+2].lower() in [x.split()[2].lower() if len(x.split())>2 else None for x in valid_stats]: # Third word
                            stat = stat + ' ' + msg[i+2].title()
                            used_args.append(msg[i+2])
                    
                
            if len(msg) > len(used_args): # If there are still args left, it must be the player
                for i in used_args:
                    msg.remove(i)
                player = ' '.join(msg)
            
            dates = {'1': '3/16/21 Data', '2': '3/18/21 Data', '3': '3/23/21 Data', '4': '3/25/21 Data', '5': '3/30/21 Data', '6': '4/1/21 Data', '7': '4/6/21 Data', '8': '4/8/21 Data', '9': '4/13/21 Data', '10': '4/15/21 Data', '11': '4/20/21 Data', '12': '4/22/21 Data', '13': '4/27/21 Data', '14': '4/29/21 Data', '15': '5/4/21 Data', '16': '5/6/21 Data', '17': '5/11/21 Data', '18': '5/13/21 Data'}
            try:
                if 'gd' in day:
                    day = day.split('gd')[-1]
                datarange = dates[day]
            except:
                return await ctx.send(f'{day} is not a valid gameday. Please enter a number between 1 and 18.')
            
            try:
                data = sheet.gsheet2df(sheet.get_google_sheet('1DU14mG8jHh2AG8ol16iYpUvXDjTHFgt7Kwe7CIoxRxU', datarange)).set_index("Username")
            except:
                return await ctx.send(f'There was an error retrieving data from gameday {day}.')

            if player.lower() == "me":
                waitingMsg = await ctx.send("One second, retreiving discord ID and stats")
                playerid = str(ctx.author.id)
                ids = sheet.gsheet2df(sheet.get_google_sheet('1AJoBYkYGMIrpe8HkkJcB25DbLP2Z-eV7P6Tk9R6265I', 'PlayerIDs!A1:B')).set_index('Discord ID')
                try:
                    player = ids.loc[playerid, 'Username']
                except:
                    return await ctx.send("You don't appear to have an up-to-date discord id on record. Try using the name that shows up on the RLPC spreadsheet.")
                await waitingMsg.delete(delay=3)
            
            lower_players = data.index.str.lower()
            if player.lower() in lower_players.values:
                print("test")
                pindex = np.where(lower_players.to_numpy()==player.lower())
                player = data.index[pindex].values[0]
                print(player)
            else:
                return await ctx.send(f"Could not find stats for {player} on gameday {day}.")
            
            try:
                stats = data.loc[player]
            except:
                return await ctx.send(f"Could not find stats for {player} on gameday {day}.")
            
            if pergame:
                stats[3:-1] = stats[3:-1].apply(lambda x: float(x)) / int(stats['Games Played'])
                stats[3:-1] = stats[3:-1].apply(lambda x: round(x, 2))
            
            if stat == None:
                embed = discord.Embed(title=f"{player}'s Stats on Gameday {day}", color=0x3333ff)
                embed.add_field(name='Games Played', value=f'{stats.loc["Games Played"]}')
                embed.add_field(name="Goals", value=f"{stats.loc['Goals']}")
                embed.add_field(name="Assists", value=f"{stats.loc['Assists']}")
                embed.add_field(name="Saves", value=f"{stats.loc['Saves']}")
                embed.add_field(name="Shots", value=f"{stats.loc['Shots']}")
                embed.add_field(name="Fantasy Points", value=f"{stats.loc['Fantasy Points']}")
                
                return await ctx.send(embed=embed)
                
            else:
                try:
                    return await ctx.send(stats.loc[stat.title()])
                except:
                    return await ctx.send(f'Could not understand stat "{stat}".')
                
    @gdstats.error
    async def gdstats_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            return await ctx.send(error)


def setup(client):
    client.add_cog(Stats(client))