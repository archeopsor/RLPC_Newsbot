from discord.ext import commands
import RLPC_ELO

recall_data = RLPC_ELO.recall_data
recall_data()
exp_score = RLPC_ELO.exp_score
rank_teams = RLPC_ELO.rank_teams

client = commands.Bot(command_prefix = '.')

class ELO(commands.Cog):
    
    def __init__(self,client):
        self.client = client
        
    @commands.command(aliases=("predict",))
    async def scorepredict(self,ctx,league,team1,team2,bestof=100):
        answer = exp_score(league,team1,team2,bestof)
        await ctx.send(answer)
        
    @scorepredict.error
    async def scorepredict_error(self,ctx,error):
        if isinstance(error,commands.BadArgument):
            await ctx.send('There was an error with your request')
        
    @commands.command(aliases=("rank",))
    async def rankteams(self,ctx,league):
        answer = rank_teams(league)
        await ctx.send(answer)
        
    @rankteams.error
    async def rankteams_error(self,ctx,error):
        if isinstance(error,commands.MissingRequiredArgument):
            await ctx.send('Please choose a league')

def setup(client):
    client.add_cog(ELO(client))