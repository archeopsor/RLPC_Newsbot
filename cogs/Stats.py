from discord.ext import commands
import discord

prefix = '$'
client = commands.Bot(command_prefix = prefix)

class Stats(commands.Cog):
    
    def __init__(self,client):
        self.client = client
        
    @commands.command(aliases=("",))
    async def command(self, ctx):
        async with ctx.typing():
            pass
            

def setup(client):
    client.add_cog(Stats(client))