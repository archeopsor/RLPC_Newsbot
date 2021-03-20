from discord.ext import commands
import fantasy_infrastructure as fantasy
import discord

from rlpc import mmr
from tools import accounts

from settings import prefix
client = commands.Bot(command_prefix = prefix)

class Fantasy(commands.Cog):
    
    def __init__(self,client):
        self.client = client
        
    @commands.command(aliases=("createaccount","create_account","newplayer", "new_player","newaccount","new_account","add_fantasy_player","new", "signup"))
    async def new_fantasy_player(self,ctx,league="none"):
        async with ctx.typing():
            if league.casefold() not in ["major","aaa","aa","a","independent", "indy", "maverick", "mav", "none"]:
                await ctx.send(f"{league} could not be understood")
                return
            else:
                pass
            author = ctx.message.author.name
            answer = accounts.create_account(author,league)
        await ctx.send(answer)
        
    @new_fantasy_player.error
    async def new_fantasy_player_error(self,ctx,error):
        if isinstance(error,commands.MissingRequiredArgument):
            await ctx.send(f'Please include the league you play in. If you are not a player, use "{prefix}new none"')
        
    @commands.command(aliases=("pick", "pickplayer", "addplayer", "add_player",))
    async def pick_player(self,ctx,*,message):
        async with ctx.typing():
            message = message.split()
            try: slot = int(message[-1])    
            except: slot = 0
            player = ""
            if slot != 0:
                for i in range(len(message)-1):
                    player = player + " " + message[i]
            elif len(message) > 1:
                for i in message:
                    player = player + " " + i
            else:
                player = message[0]
            player = player.lstrip()
            author = ctx.message.author.name
            person = author
            answer = fantasy.pick_player(person,player,slot)
        await ctx.send(answer)
        
    @pick_player.error
    async def pick_player_error(self,ctx,error):
        if isinstance(error,commands.MissingRequiredArgument):
            await ctx.send('Please include a player')
            
    @commands.command(aliases=("drop","dropplayer","removeplayer","remove_player",))
    async def drop_player(self,ctx,slot):
        async with ctx.typing():
            author = ctx.message.author.name
            try: slot = int(slot)
            except: 
                await ctx.send("Please choose a slot (1-5) rather than a player")
                return
            answer = fantasy.pick_player(author,"drop",slot)
        await ctx.send(answer)
        
    @drop_player.error
    async def drop_player_error(self,ctx,error):
        if isinstance(error,commands.MissingRequiredArgument):
            await ctx.send("Please include the slot you would like dropped")
            
    @commands.command(aliases=("leaderboard","lb","standings",))
    async def generate_leaderboard(self,ctx):
        async with ctx.typing():
            answer = fantasy.fantasy_lb()
            leaderboard=discord.Embed(title="Fantasy Leaderboard", color=0xffff00)
            for row in answer.index:
                leaderboard.add_field(name=f'{row+1}: {answer.loc[row,"Username"]}', value=answer.loc[row,"Total Points"], inline=False)
        await ctx.send(embed=leaderboard)
        
    @commands.command(aliases=("show","team","showteam",))
    async def show_team(self,ctx,*,author="none"):
        async with ctx.typing():
            if author == "none":
                author = ctx.message.author.name
            answer = fantasy.show_team(author)
            team=discord.Embed(title=f"{author}'s team", color=0x008080)
            team.add_field(name="Account League", value=answer[0], inline=True)
            team.add_field(name="Player 1", value=answer[1][0], inline=True)
            team.add_field(name="Player 2", value=answer[1][1], inline=True)
            team.add_field(name="Player 3", value=answer[1][2], inline=True)
            team.add_field(name="Player 4", value=answer[1][3], inline=True)
            team.add_field(name="Player 5", value=answer[1][4], inline=True)
            team.add_field(name="Transfers Left", value=answer[3], inline=True)
            team.add_field(name="Salary", value=answer[4], inline=True)
            team.add_field(name="Player 1 Points", value=answer[2][0], inline=True)
            team.add_field(name="Player 2 Points", value=answer[2][1], inline=True)
            team.add_field(name="Player 3 Points", value=answer[2][2], inline=True)
            team.add_field(name="Player 4 Points", value=answer[2][3], inline=True)
            team.add_field(name="Player 5 Points", value=answer[2][4], inline=True)
            team.add_field(name="Total Points", value=answer[5], inline=False)
        await ctx.send(embed=team)
    
    @commands.command(aliases=("player","playerinfo","info",))
    async def player_info(self,ctx,*,player):
        async with ctx.typing():
            answer = fantasy.info(player)
            player_card=discord.Embed(title=f"{player}'s player info", color=0xff0000)
            player_card.add_field(name="Region", value=answer[0], inline=True)
            player_card.add_field(name="Platform", value=answer[1], inline=True)
            
            try: 
                standard = int(mmr.playlist('steam', player, 'standard').replace(',', ''))
                doubles = int(mmr.playlist('steam', player, 'doubles').replace(',', ''))
                player_card.add_field(name="MMR", value=max(standard, doubles), inline=True)
            except: 
                player_card.add_field(name="MMR", value=answer[2], inline=True)
            
            player_card.add_field(name="Team", value=answer[3], inline=True)
            player_card.add_field(name="League", value=answer[4], inline=True)
            player_card.add_field(name="Fantasy Value", value=answer[5], inline=True)
            player_card.add_field(name="Allowed?", value=answer[6], inline=True)
            player_card.add_field(name="Fantasy Points", value=answer[7], inline=True)
        await ctx.send(embed=player_card)
    
    @player_info.error
    async def player_info_error(self,ctx,error):
        if isinstance(error,commands.MissingRequiredArgument):
            await ctx.send("Please include a player")
            
    @commands.command(aliases=("playerlb", "player_lb", "playerslb",))
    async def players(self,ctx, *, message=None):
        async with ctx.typing():
            league = None
            num = 10
            pergame = False
            if message != None:
                
                for i in ['Major', 'AAA', 'AA', 'A', 'Indy', 'Independent', 'Mav', 'Maverick', 'Ren', 'Renegade', 'Pal', 'Paladin']:
                    if i.casefold() in message.casefold().split():
                        league = i
                        break
                
                if league == "Indy":
                    league = "Independent"
                elif league == "Mav":
                    league = "Maverick"
                elif league == "Ren":
                    league = "Renegade"
                elif league == "Pal":
                    league = "Paladin"
                    
                for word in message.split():
                    try:
                        int(word)
                        num = int(word)
                    except:
                        pass
                    
                if "pergame" in message or "pg" in message:
                    pergame = True
            
            lb = fantasy.player_lb(league=league, num=num, pergame=pergame)
            
            
            
            message = f"**1)** {lb.index[0]} ({lb[lb.index[0]]})"
            for i in range(1,num):
                message = message + f"\n**{i+1})** {lb.index[i]} ({lb[lb.index[i]]})"
        
        await ctx.send(f"**Player Leaderboard for fantasy points**\n*Add 'pg' to the end of the command to divide points by the # of series played*") 
        try:
            await ctx.send(message)
        except:
            await ctx.send("That exceeds discord's 2000 character limit. Please try again with fewer players.")
        
    @commands.command(aliases=("fantasy","fhelp","f_help",))
    async def fantasy_help(self,ctx):
        answer = f"""
Welcome to RLPC Fantasy! This is a just-for-fun fantasy league in which people can build a team of RLPC players and compete against other fantasy teams.
**To get started, type {prefix}new to create a new fantasy account.**

**__RULES/STRUCTURE__**
 - Each fantasy team has 5 players
 - You can pick up players at any time EXCEPT for Tuesdays and Thursdays (Gamedays)
     - You may also be prevented from picking players on Wednesday or Friday morning if points haven't been calculated yet
 - Points are calculated after every gameday (Wednesday/Friday)
 - Each team can do 2 transfers (replacing one player with another player) every week. Filling an empty slot doesn't add to this counter, but dropping a player does.
 - Each player is given a specific "salary" based on their mmr and team. The total salary value of a fantasy team must be below 700 at all times.

**__FANTASY COMMANDS__**

**{prefix}fantasy** - Shows this message
**{prefix}new** - Creates a fantasy team linked to your discord account.
    *Example: {prefix}new*
**{prefix}team** - Shows the current fantasy team of any fantasy player. Not specifying a player will show your own team
    *Example: {prefix}team arco*
**{prefix}info** - Gives important information about a player, such as their salary and a variety of stats.
    *Example: {prefix}info arco*
**{prefix}pick** - Adds a player to your fantasy team, in one of 5 player slots. Please specify which player you want, as well as which slot.
    *Example: {prefix}pick arco 4*
**{prefix}drop** - Drops the player in the specified slot, replacing them with 'Not Picked'.
    *Example: {prefix}drop 4*
**{prefix}lb** - Displays the current leaderboard of points
**{prefix}search**- Searches for the top 5 players fiting specified parameters
    *Example: {prefix}search name: arco min: 100 max: 160 league: AA team: all strictness: 0.8*
**{prefix}players** - Shows a leaderboard of players based on the fantasy points they have earned since the start of the season.
    *Example: {prefix}players major*
        """
        await ctx.send(answer)
        
    @commands.command(aliases=("searchplayers",))
    async def search(self,ctx,arg1="",arg2="",arg3="",arg4="",arg5="",arg6="",arg7="",arg8="",arg9="",arg10="",arg11="",arg12=""):
        async with ctx.typing():
            name = "none"
            minsalary = 0
            maxsalary = 700
            league = "all"
            team = "all"
            maxdistance = 5
            argument_labels = [arg1, arg3, arg5, arg7, arg9, arg11]
            arguments = [arg2, arg4, arg6, arg8, arg10, arg12]
            for arg in argument_labels:
                index = argument_labels.index(arg)
                if arg.casefold() in ["name","username","player","name:","username:","player:"]:
                    name = arguments[index]
                elif arg.casefold() in ["min","min:","minimum","minimum:","minsalary","minsalary:","min_salary","min_salary:","minimumsalary","minimumsalary:","minimum_salary:","minimum_salary"]:
                    minsalary = int(arguments[index])
                elif arg.casefold() in ["max","max:","maximum","maximum:","maxsalary","maxsalary:","max_salary","max_salary:","maximumsalary","maximumsalary:","maximum_salary:","maximum_salary"]:
                    maxsalary = int(arguments[index])
                elif arg.casefold() in ["team","team:"]:
                    team = arguments[index]
                elif arg.casefold() in ["league","league:"]:
                    league = arguments[index]
                elif arg.casefold() in ["maxdistance","difference","difference:","maxdistance:","strictness","strictness:"]:
                    maxdistance = int(arguments[index])
            
            answer = fantasy.search(minsalary=minsalary,maxsalary=maxsalary,league=league,team=team,name=name,maxdistance=maxdistance)
            
            embeds = []
            
            if len(answer.index) > 0:
                embed1 = discord.Embed(title=answer.iloc[0,0], color=0x000080)
                embed1.add_field(name="Username:", value=answer.iloc[0,0], inline=True)
                embed1.add_field(name="MMR:", value=answer.iloc[0,3], inline=True)
                embed1.add_field(name="Team:", value=answer.iloc[0,4], inline=True)
                embed1.add_field(name="League:", value=answer.iloc[0,5], inline=True)
                embed1.add_field(name="Fantasy Value:", value=answer.iloc[0,6], inline=True)
                embed1.add_field(name="Allowed?", value=answer.iloc[0,7], inline=True)
                embeds.append(embed1)
            
            if len(answer.index) > 1:
                embed2 = discord.Embed(title=answer.iloc[1,0], color=0x000080)
                embed2.add_field(name="Username:", value=answer.iloc[1,0], inline=True)
                embed2.add_field(name="MMR:", value=answer.iloc[1,3], inline=True)
                embed2.add_field(name="Team:", value=answer.iloc[1,4], inline=True)
                embed2.add_field(name="League:", value=answer.iloc[1,5], inline=True)
                embed2.add_field(name="Fantasy Value:", value=answer.iloc[1,6], inline=True)
                embed2.add_field(name="Allowed?", value=answer.iloc[1,7], inline=True)
                embeds.append(embed2)
            
            if len(answer.index) > 2:
                embed3 = discord.Embed(title=answer.iloc[2,0], color=0x000080)
                embed3.add_field(name="Username:", value=answer.iloc[2,0], inline=True)
                embed3.add_field(name="MMR:", value=answer.iloc[2,3], inline=True)
                embed3.add_field(name="Team:", value=answer.iloc[2,4], inline=True)
                embed3.add_field(name="League:", value=answer.iloc[2,5], inline=True)
                embed3.add_field(name="Fantasy Value:", value=answer.iloc[2,6], inline=True)
                embed3.add_field(name="Allowed?", value=answer.iloc[2,7], inline=True)
                embeds.append(embed3)
            
            if len(answer.index) > 3:
                embed4 = discord.Embed(title=answer.iloc[3,0], color=0x000080)
                embed4.add_field(name="Username:", value=answer.iloc[3,0], inline=True)
                embed4.add_field(name="MMR:", value=answer.iloc[3,3], inline=True)
                embed4.add_field(name="Team:", value=answer.iloc[3,4], inline=True)
                embed4.add_field(name="League:", value=answer.iloc[3,5], inline=True)
                embed4.add_field(name="Fantasy Value:", value=answer.iloc[3,6], inline=True)
                embed4.add_field(name="Allowed?", value=answer.iloc[3,7], inline=True)
                embeds.append(embed4)
            
            if len(answer.index) > 4:
                embed5 = discord.Embed(title=answer.iloc[4,0], color=0x000080)
                embed5.add_field(name="Username:", value=answer.iloc[4,0], inline=True)
                embed5.add_field(name="MMR:", value=answer.iloc[4,3], inline=True)
                embed5.add_field(name="Team:", value=answer.iloc[4,4], inline=True)
                embed5.add_field(name="League:", value=answer.iloc[4,5], inline=True)
                embed5.add_field(name="Fantasy Value:", value=answer.iloc[4,6], inline=True)
                embed5.add_field(name="Allowed?", value=answer.iloc[4,7], inline=True)
                embeds.append(embed5)
        
        if len(embeds) == 0:
            await ctx.send("There were no players matching those parameters")
            return
        elif len(embeds) == 1:
            await ctx.send("Here's the only player matching those parameters")
        else: 
            await ctx.send(f"Here are {len(answer.index)} players matching those parameters:")
        for i in embeds:
            await ctx.send(embed=i)
        
def setup(client):
    client.add_cog(Fantasy(client))