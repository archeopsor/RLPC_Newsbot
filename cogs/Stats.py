import discord
from discord.ext import commands

from rlpc import stats, mmr

from tools import sheet

prefix = '$'
client = commands.Bot(command_prefix = prefix)

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
            players = sheet.gsheet2df(sheet.get_google_sheet('1C10LolATTti0oDuW64pxDhYRLkdUxrXP0fHYBk3ZwmU', 'Players!A1:R'))
            
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
                msg = ctx.message.author.name
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
            print(answer)
            try:
                embed = discord.Embed(title=f"{answer.values[0][0]}'s Stats", color=0x3333ff)
            except:
                return await ctx.send(f"Could not find {msg}'s stats. Contact arco if you think this is a bug")
            for i, col in enumerate(answer.columns[1:]):
                embed.add_field(name=col, value=answer.values[0][i+1])
        await ctx.send(embed=embed)
        
    @commands.command(aliases=("probs","prob","probability", "forecast"))
    async def probabilities(self, ctx, *, msg):
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
            if league == "none":
                await ctx.send("You haven't chosen a league. You can also see all of the data here: <https://docs.google.com/spreadsheets/d/1GEFufHK5xt0WqThYC7xaK2gz3cwjinO43KOsb7HogQQ/edit?usp=sharing>")
                return
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
        
    @probabilities.error
    async def probabilities_error(self,ctx,error):
        if isinstance(error,commands.MissingRequiredArgument):
            await ctx.send("You haven't chosen a league. You can also see all of the data here: https://docs.google.com/spreadsheets/d/1GEFufHK5xt0WqThYC7xaK2gz3cwjinO43KOsb7HogQQ/edit?usp=sharing")

def setup(client):
    client.add_cog(Stats(client))