from discord.ext import commands
from RLPC_ELO import exp_score, rank_teams, recall_data
import discord

prefix = '$'
client = commands.Bot(command_prefix = prefix)

class ELO(commands.Cog):
    
    def __init__(self,client):
        self.client = client
        
    @commands.command(aliases=("predict","predictscore","score_predict","predict_score",))
    async def scorepredict(self,ctx,team1: str,team2: str,bestof: float=5.0):
        async with ctx.typing():
            bestof = float(bestof)
            answer = exp_score(team1,team2,bestof)
        await ctx.send(answer)
        
    @scorepredict.error
    async def scorepredict_error(self,ctx,error):
        if isinstance(error,commands.MissingRequiredArgument):
            if error.param.name in ['team1','team2']:
                await ctx.send('Please include two teams')
            await ctx.send(f'The format for this command is {prefix}predict [team 1] [team 2] [# of games *(optional)*]')
        
    @commands.command(aliases=("rank",))
    async def rankteams(self,ctx,league):
        async with ctx.typing():
            answer = rank_teams(league, previous=True)
            if league.casefold() == "major":
                league = "Major"
            elif league.casefold() in ["indy", "independent"]:
                league = "Independent"
            elif league.casefold() in ['mav', 'maverick']:
                league = "Maverick"
            elif league.casefold() in ['ren', 'renegade']:
                league = "Renegade"
            elif league.casefold() in ['pal', 'paladin']:
                league = "Paladin"
            else:
                league = league.upper()
            standings = discord.Embed(title=f"{league} Rankings",color=0x000080,description=f"Computer-generated rankings for the {league} league, based on an internal ELO system. For the official, human-made rankings, use $pr")
            value_response = ""
            for row in answer.index:
                value_response += f"{row+1}: {answer.loc[row, 'Team']} ({answer.loc[row, 'elo']}) [{answer.loc[row, 'elo'] - answer.loc[row, 'Previous']}]\n"
            standings.add_field(name="Rankings", value=value_response)
        await ctx.send(embed=standings)
        
    @rankteams.error
    async def rankteams_error(self,ctx,error):
        if isinstance(error,commands.MissingRequiredArgument):
            await ctx.send('Please choose a league')

def setup(client):
    client.add_cog(ELO(client))