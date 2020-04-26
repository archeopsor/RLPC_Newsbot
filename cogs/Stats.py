from discord.ext import commands
import discord
import RLPC_Stats as stats
import Google_Sheets as sheet

prefix = '$'
client = commands.Bot(command_prefix = prefix)

class Stats(commands.Cog):
    
    def __init__(self,client):
        self.client = client
        
    @commands.command(aliases=("getstats","stats","get_stats",))
    async def get_player_stats(self, ctx, *, msg):
        async with ctx.typing():
            first = " ".join(msg.split()[:-1])
            last = msg.split()[-1]
            try: answer = stats.get_player_stats(first, last)
            except: answer = stats.get_player_stats(msg)
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
                await ctx.send("You haven't chosen a league. You can also see all of the data here: https://docs.google.com/spreadsheets/d/1GEFufHK5xt0WqThYC7xaK2gz3cwjinO43KOsb7HogQQ/edit?usp=sharing")
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
                await ctx.send(data.reset_index())
                return
            
            if team != "none":
                data = data.loc[team.title()]
                
            if part != "none":
                data = data[part.title()]
                
            await ctx.send(data)
            await ctx.send("See all of the data here: https://docs.google.com/spreadsheets/d/1GEFufHK5xt0WqThYC7xaK2gz3cwjinO43KOsb7HogQQ/edit?usp=sharing")
        
    @probabilities.error
    async def probabilities_error(self,ctx,error):
        if isinstance(error,commands.MissingRequiredArgument):
            await ctx.send("Please pick a league")

def setup(client):
    client.add_cog(Stats(client))