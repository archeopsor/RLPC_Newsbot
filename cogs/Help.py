import discord
from discord.ext import commands

from settings import prefix

client = commands.Bot(command_prefix = prefix)

class Help(commands.Cog):
    
    def __init__(self,client):
        self.client = client
        
        
    @commands.command(pass_context=True)
    async def help(self, ctx, specified="none"):
        author = ctx.message.author
        specified = specified.lower()
        
        
        
        # TODO: Text file for each individual command
        # TODO: read necessary text file
        # TODO: replace all {prefix} with the client prefix
        
        return await ctx.send("A DM has been sent! If you have any further questions, please DM Arco.")
        
        
def setup(client):
    client.add_cog(Help(client))