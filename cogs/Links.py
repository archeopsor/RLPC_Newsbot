import discord
from discord import app_commands
from discord.ext import commands
from discord.ext.commands.context import Context

from settings import prefix


class Links(commands.Cog):
    
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name = "links")
    async def links(self, interaction: discord.Interaction):
        """Gets some links relevant to RLPC"""
        return await interaction.response.send_message(
"""
**RLPC Media**
Main Twitch Channel: https://www.twitch.tv/rlpcofficial
RLPC Twitter: https://twitter.com/officialrlpc 
RLPC YouTube: https://www.youtube.com/channel/UCJj3L-OriSD2w8-lHM7yUvw 
RLPC Subreddit: https://www.reddit.com/r/RLPC
RLPC News Discord: https://discord.gg/2SU3zVVAtz
RLPC Tik Tok: https://www.tiktok.com/@officialrlpc
RLPC Instagram: https://instagram.com/officialrlpc
Verification Discord: https://discord.gg/BUDpvq7egk

**Staff Applications**
Mod Application: https://forms.gle/ASGxbed27F76LnaY7
Marketing Team Application: https://forms.gle/xTcoSKJw21ZY7hJV9
Media Team Application: https://docs.google.com/forms/d/1isBkfMkLMhb_S7N1YTxUr4HM18wLKWa60glJINj2cfs/edit
News Team Application: https://forms.gle/KZstv17REUPyMuncA
Sheets Team Application: https://docs.google.com/forms/d/12Fzln9z7fNRyVYIyzOnE2m2rmFpq4kcnWiOG8uau-N4
PR Team Application: https://forms.gle/hBmnr2Fqer37vFgw5
GDD Team Application: https://forms.gle/UriHzeBQAhUW2Dqh9
Web Developer Application: https://forms.gle/dAsjBmDi26eqPSuSA
Orientation Application: https://forms.gle/3iB9Frf58UebPdDGA
Community Events Team Application: https://forms.gle/nmjfs5vV1yDuc7MZ7

**Other**
Invite this bot to your own server: https://discord.com/api/oauth2/authorize?client_id=635188576446840858&permissions=380104723520&scope=applications.commands%20bot
RLPC Forecasts: https://docs.google.com/spreadsheets/d/1GEFufHK5xt0WqThYC7xaK2gz3cwjinO43KOsb7HogQQ/edit?pli=1#gid=309392263
RLPC Gameday Stats: https://docs.google.com/spreadsheets/d/1GEFufHK5xt0WqThYC7xaK2gz3cwjinO43KOsb7HogQQ/edit?pli=1#gid=309392263
""", ephemeral = True
        )
        
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
        await ctx.send("Invite this bot to your own server: https://discord.com/api/oauth2/authorize?client_id=635188576446840858&permissions=380104723520&scope=applications.commands%20bot")