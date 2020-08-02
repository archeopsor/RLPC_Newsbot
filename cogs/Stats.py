from discord.ext import commands
import discord
import RLPC_Stats as stats
import Google_Sheets as sheet
import mmr

prefix = '$'
client = commands.Bot(command_prefix = prefix)

class Stats(commands.Cog):
    
    def __init__(self,client):
        self.client = client
        
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
                mmrs[name]['Duels'] = mmr.playlist(platform, name, '1s')[rating]
                mmrs[name]['Doubles'] = mmr.playlist(platform, name, '2s')[rating]
                mmrs[name]['Solo Standard'] = mmr.playlist(platform, name, 'ss')[rating]
                mmrs[name]['Standard'] = mmr.playlist(platform, name, '3s')[rating]
            
                embed = discord.Embed(title=f"{player}'s MMRs", color=0xffffff)
                for playlist in list(mmrs[name]):
                    embed.add_field(name=playlist, value=mmrs[name][playlist])
                
                await ctx.send(embed)
    
    @commands.command(aliases=("getstats","stats","get_stats",))
    async def get_player_stats(self, ctx, *, msg):
        async with ctx.typing():
            if msg.casefold() == "me":
                msg = ctx.message.author.name
            first = " ".join(msg.split()[:-1])
            last = msg.split()[-1]
            try: answer = stats.get_player_stats(first, last)
            except: 
                try: answer = stats.get_player_stats(msg)
                except: await ctx.send(f"Cound not find player {msg}")
            embed = discord.Embed(title=f"{answer.values[0][0]}'s Stats", color=0x3333ff)
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
                if word.casefold() in ["major","aaa","aa","a"]:
                    league = word.casefold()
                elif word.casefold() in ['ascension', 'bulls', 'cobras', 'ducks', 'eagles', 'flames', 'hawks', 'kings', 'lions', 'lumberjacks', 'panthers', 'pirates', 'sharks', 'spartans', 'storm', 'whitecaps', 'bobcats', 'bulldogs', 'dolphins', 'entropy', 'geese', 'heat', 'knights', 'osprey', 'owls', 'pioneers', 'raiders', 'thunder', 'tigers', 'trojans', 'tundra', 'vipers', 'bobcats', 'bulldogs', 'dolphins', 'entropy', 'geese', 'heat', 'knights', 'osprey', 'owls', 'pioneers', 'raiders', 'thunder', 'tigers', 'trojans', 'tundra', 'vipers', 'avalanche', 'bandits', 'barracuda', 'dukes', 'falcons', 'herons', 'inferno', 'jaguars', 'lightning', 'lynx', 'mustangs', 'pulsars', 'pythons', 'voyagers', 'vultures', 'warriors', 'cardinals', 'cougars', 'embers', 'eskimos', 'genesis', 'gulls', 'jesters', 'leopards', 'miners', 'pelicans', 'rattlers', 'ravens', 'stallions', 'tempest', 'titans', 'wranglers']:
                    team = word
                elif word.casefold() in ["wins","record","playoffs","playoff","semifinals","semifinal","finals","final","finalist","champions","champion","winners","winner"]:
                    part = word
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