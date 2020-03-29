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
        
    @commands.command(aliases=("probs","prob","probability"))
    async def probabilities(self, ctx, *, msg):
        async with ctx.typing():
            msg = msg.split()
            league = "none"
            team = "none"
            section = "none"
            for word in msg:
                if word.casefold() in ["major","aaa","aa","a"]:
                    league = word
                elif word.casefold() in ['ascension', 'bulls', 'cobras', 'ducks', 'eagles', 'flames', 'hawks', 'kings', 'lions', 'lumberjacks', 'panthers', 'pirates', 'sharks', 'spartans', 'storm', 'whitecaps', 'bobcats', 'bulldogs', 'dolphins', 'entropy', 'geese', 'heat', 'knights', 'osprey', 'owls', 'pioneers', 'raiders', 'thunder', 'tigers', 'trojans', 'tundra', 'vipers', 'bobcats', 'bulldogs', 'dolphins', 'entropy', 'geese', 'heat', 'knights', 'osprey', 'owls', 'pioneers', 'raiders', 'thunder', 'tigers', 'trojans', 'tundra', 'vipers', 'avalanche', 'bandits', 'barracuda', 'dukes', 'falcons', 'herons', 'inferno', 'jaguars', 'lightning', 'lynx', 'mustangs', 'pulsars', 'pythons', 'voyagers', 'vultures', 'warriors', 'cardinals', 'cougars', 'embers', 'eskimos', 'genesis', 'gulls', 'jesters', 'leopards', 'miners', 'pelicans', 'rattlers', 'ravens', 'stallions', 'tempest', 'titans', 'wranglers']:
                    team = word
                elif word.casefold() in ["wins","record","playoffs","playoff","semifinals","semifinal","finals","final","finalist","champions","champion","winners","winner"]:
                    part = word
        pass

def setup(client):
    client.add_cog(Stats(client))