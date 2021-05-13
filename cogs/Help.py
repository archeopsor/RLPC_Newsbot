import discord
from discord.ext import commands
import os

from settings import prefix

client = commands.Bot(command_prefix = prefix)

class Help(commands.Cog):
    
    def __init__(self,client):
        self.client = client
        
        
    @commands.command(pass_context=True)
    async def help(self, ctx, specified="none"):
        author = ctx.message.author
        specified = specified.lower()
        
        if specified in ['elo', 'fantasy', 'link', 'reddit', 'statscog', 'other']:
            specified = specified.title()
        elif specified not in ['none', 'predict', 'rank', 'forecast', 'new', 'pick', 'drop', 'lb', 'team', 'info', 'players', 'search', 'getreddit', 'get', 'newest', 'valid', 'pr', 'mmr', 'stats', 'gdstats', 'top', 'ping', 'alerts']:
            await ctx.send(f"Couldn't understand {specified.title()}")
            specified = "none"
        
        path = os.getcwd()[-4]+'help_text\\'
        with open(path+specified+'.txt') as f:
            text = f.read()
            text = text.replace('{prefix}', prefix)
        
        if not isinstance(ctx.channel, discord.channel.DMChannel):
            await author.send(text)
            return await ctx.send("A DM has been sent! If you have any further questions, please DM Arco.")
        else:
            return await ctx.send(text)
        
        
def setup(client):
    client.add_cog(Help(client))