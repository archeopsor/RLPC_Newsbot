from discord.ext import commands
import RLPC_ELO
import discord

recall_data = RLPC_ELO.recall_data
recall_data()
exp_score = RLPC_ELO.exp_score
rank_teams = RLPC_ELO.rank_teams

prefix = '$'
client = commands.Bot(command_prefix = prefix)

class ELO(commands.Cog):
    
    def __init__(self,client):
        self.client = client
        
    @commands.command(aliases=("predict","predictscore","score_predict","predict_score",))
    async def scorepredict(self,ctx,league,team1,team2,bestof=100):
        async with ctx.typing():
            bestof = float(bestof)
            answer = RLPC_ELO.exp_score(league,team1,team2,bestof)
        await ctx.send(answer)
        
    @scorepredict.error
    async def scorepredict_error(self,ctx,error):
        if isinstance(error,commands.MissingRequiredArgument):
            if error.param.name == 'league':
                await ctx.send('Please include a league and two teams')
            if error.param.name in ['team1','team2']:
                await ctx.send('Please include two teams')
            await ctx.send(f'The format for this command is {prefix}predict [league] [team 1] [team 2] [# of games *(optional)*]')
        
    @commands.command(aliases=("rank",))
    async def rankteams(self,ctx,league):
        async with ctx.typing():
            answer = RLPC_ELO.rank_teams(league)
            answer = answer.reset_index()
            if league.casefold() == "major":
                league = "Major"
            else:
                league = league.upper()
            standings = discord.Embed(title=f"{league} Rankings",color=0x000080,description=f"Computer-generated rankings for the {league} league, based on an internal ELO system")
            teams_elos = []
            for row in answer.index:
                teams_elos.append(f'{answer.loc[row][0]+1}: {answer.loc[row][1]}')
            value_response = ""
            for i in teams_elos:
                value_response += f' \n {i}'
            value_response = value_response[3:]
            standings.add_field(name="Rankings", value=value_response)
            # for row in answer.index:
            #     standings.add_field(name=f'{row+1}. {answer.loc[row][0]}:',value=answer.loc[row][1],inline=False)
        await ctx.send(embed=standings)
        
    @rankteams.error
    async def rankteams_error(self,ctx,error):
        if isinstance(error,commands.MissingRequiredArgument):
            await ctx.send('Please choose a league')

def setup(client):
    client.add_cog(ELO(client))