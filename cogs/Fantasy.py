from discord.ext import commands
import fantasy_infrastructure as fantasy
import discord

prefix = '$'
client = commands.Bot(command_prefix = prefix)

class Fantasy(commands.Cog):
    
    def __init__(self,client):
        self.client = client
        
    @commands.command(aliases=("createaccount","create_account","newplayer", "new_player","newaccount","new_account","add_fantasy_player","new"))
    async def new_fantasy_player(self,ctx,league):
        async with ctx.typing():
            if league.casefold() not in ["major","aaa","aa","a","none"]:
                await ctx.send(f"{league} could not be understood")
                return
            else:
                pass
            author = ctx.message.author.name
            answer = fantasy.add_fantasy_player(author,league)
        await ctx.send(answer)
        
    @new_fantasy_player.error
    async def new_fantasy_player_error(self,ctx,error):
        if isinstance(error,commands.MissingRequiredArgument):
            await ctx.send(f'Please include the league you play in. If you are not a player, use "{prefix}new_fantasy_player none"')
        
    @commands.command(aliases=("pick", "pickplayer", "addplayer", "add_player",))
    async def pick_player(self,ctx,player,slot=1):
        async with ctx.typing():    
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
            person = author
            answer = fantasy.pick_player(person,"drop",slot)
        await ctx.send(answer)
        
    @drop_player.error
    async def drop_player_error(self,ctx,error):
        if isinstance(error,commands.MissingRequiredArgument):
            await ctx.send("Please include the slot you would like dropped")
            
    @commands.command(aliases=("leaderboard","lb","standings",))
    async def generate_leaderboard(self,ctx):
        async with ctx.typing():
            answer = fantasy.generate_leaderboard()
        await ctx.send(answer)
        
    @commands.command(aliases=("show","team","showteam",))
    async def show_team(self,ctx,author="none"):
        async with ctx.typing():
            if author == "none":
                author = ctx.message.author.name
            answer = fantasy.show_team(author)
        await ctx.send(answer)
    
    @commands.command(aliases=("player","playerinfo","info",))
    async def player_info(self,ctx,player):
        async with ctx.typing():
            answer = fantasy.info(player)
        await ctx.send(answer)
    
    @player_info.error
    async def player_info_error(self,ctx,error):
        if isinstance(error,commands.MissingRequiredArgument):
            await ctx.send("Please include a player")
        
    @commands.command(aliases=("fantasy","fhelp","f_help"))
    async def fantasy_help(self,ctx):
        answer = f"""
Welcome to RLPC Fantasy! This is a just-for-fun fantasy league in which people can build a team of RLPC players and compete against other fantasy teams.
**To get started, type {prefix}new_fantasy_player to create a new fantasy account.**

**__RULES/STRUCTURE__**
 - Each fantasy team has 5 players
 - You can pick up players at any time EXCEPT for Tuesdays and Thursdays (Gamedays)
 - You can't pick up players that play in the same league as you
 - Points are calculated after every gameday (Wednesday/Friday)
 - Each team can do 2 transfers (replacing one player with another player) every week. Filling an empty slot doesn't add to this counter
 - Each player is given a specific "salary" based on their mmr and team. The total salary value of a fantasy team must be below 700 at all times.

**__FANTASY COMMANDS__**

**{prefix}fantasy_help** - Shows this message
**{prefix}new_fantasy_player** - Creates a fantasy team linked to your discord account. Please include the league you play in, or 'none'.
    *Example: {prefix}new_fantasy_player major*
**{prefix}team** - Shows the current fantasy team of any fantasy player. "{prefix}team" will display your own team, although you can include any discord account name (Don't use nicknames')
    *Example: {prefix}team arco*
**{prefix}info** - Gives important information about a player, such as their salary and a variety of stats.
    *Example: {prefix}info arco*
**{prefix}pick_player** - Adds a player to your fantasy team, in one of 5 player slots. Please specify which player you want, as well as which slot.
    *Example: {prefix}pick_player arco 4*
**{prefix}drop_player** - Can also be done with '{prefix}pick_player drop [slot]', drops the player in the specified slot, replacing them with 'Not Picked'.
**{prefix}leaderboard** - Displays the current leaderboard of points
        """
        await ctx.send(answer)
        
    @commands.command(aliases=("searchplayers",))
    async def search(self,ctx,arg1="",arg2="",arg3="",arg4="",arg5="",arg6="",arg7="",arg8="",arg9="",arg10=""):
        async with ctx.typing():    
            name = "none"
            minsalary = 0
            maxsalary = 700
            league = "all"
            team = "all"
            argument_labels = [arg1, arg3, arg5, arg7, arg9]
            arguments = [arg2, arg4, arg6, arg8, arg10]
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
            
            answer = fantasy.search(minsalary=minsalary,maxsalary=maxsalary,league=league,team=team,name=name)
            print(answer)
            
            embed1 = discord.Embed(title=answer.iloc[0,0], color=0x000080)
            embed1.add_field(name="Username:", value=answer.iloc[0,0], inline=True)
            embed1.add_field(name="MMR:", value=answer.iloc[0,1], inline=True)
            embed1.add_field(name="Team:", value=answer.iloc[0,2], inline=True)
            embed1.add_field(name="League:", value=answer.iloc[0,3], inline=True)
            embed1.add_field(name="Fantasy Value:", value=answer.iloc[0,4], inline=True)
            embed1.add_field(name="Allowed?", value=answer.iloc[0,5], inline=True)
            
            embed2 = discord.Embed(title=answer.iloc[1,0], color=0x000080)
            embed2.add_field(name="Username:", value=answer.iloc[1,0], inline=True)
            embed2.add_field(name="MMR:", value=answer.iloc[1,1], inline=True)
            embed2.add_field(name="Team:", value=answer.iloc[1,2], inline=True)
            embed2.add_field(name="League:", value=answer.iloc[1,3], inline=True)
            embed2.add_field(name="Fantasy Value:", value=answer.iloc[1,4], inline=True)
            embed2.add_field(name="Allowed?", value=answer.iloc[1,5], inline=True)
            
            embed3 = discord.Embed(title=answer.iloc[2,0], color=0x000080)
            embed3.add_field(name="Username:", value=answer.iloc[2,0], inline=True)
            embed3.add_field(name="MMR:", value=answer.iloc[2,1], inline=True)
            embed3.add_field(name="Team:", value=answer.iloc[2,2], inline=True)
            embed3.add_field(name="League:", value=answer.iloc[2,3], inline=True)
            embed3.add_field(name="Fantasy Value:", value=answer.iloc[2,4], inline=True)
            embed3.add_field(name="Allowed?", value=answer.iloc[2,5], inline=True)
        
            embed4 = discord.Embed(title=answer.iloc[3,0], color=0x000080)
            embed4.add_field(name="Username:", value=answer.iloc[3,0], inline=True)
            embed4.add_field(name="MMR:", value=answer.iloc[3,1], inline=True)
            embed4.add_field(name="Team:", value=answer.iloc[3,2], inline=True)
            embed4.add_field(name="League:", value=answer.iloc[3,3], inline=True)
            embed4.add_field(name="Fantasy Value:", value=answer.iloc[3,4], inline=True)
            embed4.add_field(name="Allowed?", value=answer.iloc[3,5], inline=True)
        
            embed5 = discord.Embed(title=answer.iloc[4,0], color=0x000080)
            embed5.add_field(name="Username:", value=answer.iloc[4,0], inline=True)
            embed5.add_field(name="MMR:", value=answer.iloc[4,1], inline=True)
            embed5.add_field(name="Team:", value=answer.iloc[4,2], inline=True)
            embed5.add_field(name="League:", value=answer.iloc[4,3], inline=True)
            embed5.add_field(name="Fantasy Value:", value=answer.iloc[4,4], inline=True)
            embed5.add_field(name="Allowed?", value=answer.iloc[4,5], inline=True)
        
        await ctx.send("Here are 5 players matching those parameters (sorted alphabetically):")
        embeds = [embed1, embed2, embed3, embed4, embed5]
        for i in embeds:
            await ctx.send(embed=i)
        
def setup(client):
    client.add_cog(Fantasy(client))