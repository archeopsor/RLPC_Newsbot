from discord.ext import commands
from discord.ext.commands.context import Context

from settings import prefix


class Links(commands.Cog):
    
    def __init__(self, bot):
        self.bot = bot
        
    @commands.command(aliases=('rlpc','leaguelink',))
    async def rlpclink(self, ctx: Context):
        await ctx.send('Join the RLPC invite server at: https://discord.gg/BUDpvq7egk')

    @commands.command(aliases=('rlpcnews','discord','discordlink',))
    async def rlpcnewslink(self, ctx: Context):
        await ctx.send('Join RLPC News here: https://discord.gg/YUnSBBM')
        
    @commands.command(aliases=('redditlink',))
    async def reddit(self, ctx: Context):
        await ctx.send("The RLPC Reddit can be found here: https://www.reddit.com/r/RLPC/new/")
        
    @commands.command(aliases=('application','applylink','applicationlink',))
    async def apply(self, ctx: Context):
        await ctx.send("Apply to join RLPC News here: https://forms.gle/mqUGfJpZt8DsY43F7")
        
    @commands.command(aliases=('bot', 'botinvite', 'bot_invite', 'invitebot', 'invite_bot',))
    async def invite(self, ctx: Context):
        await ctx.send("Invite this bot to your own server: https://discord.com/oauth2/authorize?client_id=635188576446840858&permissions=117760&scope=bot")