from discord.ext import commands
import discord
import RLPC_Stats as stats

prefix = '$'
client = commands.Bot(command_prefix = prefix)

class Stats(commands.Cog):
    
    def __init__(self,client):
        self.client = client
        
    @commands.command(aliases=("getstats","stats","get_stats",))
    async def get_player_stats(self, ctx, player, stat="all"):
        async with ctx.typing():
            answer = stats.get_player_stats(player, stat)
            embed = discord.Embed(title=f"{player}'s Stats", color=0x3333ff)
            for i, col in enumerate(answer.columns):
                embed.add_field(name=col, value=answer.values[0][i])
        await ctx.send(answer)
            

def setup(client):
    client.add_cog(Stats(client))