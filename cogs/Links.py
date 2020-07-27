from discord.ext import commands

prefix = '$'
client = commands.Bot(command_prefix = prefix)

class Links(commands.Cog):
    
    def __init__(self,client):
        self.client = client
        
    @commands.command(aliases=('rlpc','leaguelink',))
    async def rlpclink(self,ctx):
        await ctx.send('Join the RLPC at: https://discord.gg/YfYaZCR')

    @commands.command(aliases=('rlpcnews','discord','discordlink',))
    async def rlpcnewslink(self,ctx):
        await ctx.send('Join RLPC News here: https://discord.gg/YUnSBBM')
        
    @commands.command(aliases=('redditlink',))
    async def reddit(self,ctx):
        await ctx.send("The RLPC Reddit can be found here: https://www.reddit.com/r/RLPC/new/")
        
    @commands.command(aliases=('application','applylink','applicationlink',))
    async def apply(self,ctx):
        await ctx.send("Apply to join RLPC News here: https://forms.gle/mqUGfJpZt8DsY43F7")

def setup(client):
    client.add_cog(Links(client))