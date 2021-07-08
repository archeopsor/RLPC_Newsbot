import discord
from discord.ext import commands
import os

from discord.ext.commands.context import Context

from settings import prefix

bot = commands.Bot(command_prefix = prefix)

class Help(commands.Cog):
    
    def __init__(self, bot):
        self.bot = bot
        
        
    @commands.command(pass_context=True)
    async def help(self, ctx: Context, specified="none"):
        author = ctx.message.author
        specified = specified.lower()
        
        if specified in ['elo', 'fantasy', 'link', 'reddit', 'statscog', 'other']:
            specified = specified.title()
        elif specified not in ['none', 'predict', 'rank', 'forecast', 'new', 'pick', 'drop', 'lb', 'team', 'info', 'players', 'search', 'getreddit', 'get', 'newest', 'valid', 'pr', 'mmr', 'stats', 'gdstats', 'top', 'ping', 'alerts']:
            await ctx.send(f"Couldn't understand {specified.title()}")
            specified = "none"

        if specified == "none":
            specified = "Base"
        
        path = '/'.join(os.getcwd().split('\\')) + '/help_text/'
        with open(path+specified+'.txt') as f:
            text = f.read()
            text = text.replace('{prefix}', prefix)
        
        if not isinstance(ctx.channel, discord.channel.DMChannel):
            await author.send(text)
            return await ctx.send("A DM has been sent! If you have any further questions, please DM Arco.")
        else:
            return await ctx.send(text)
        
        
def setup(bot):
    bot.add_cog(Help(bot))