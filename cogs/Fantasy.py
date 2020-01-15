from discord.ext import commands
import fantasy_infrastructure as fantasy

client = commands.Bot(command_prefix = '.')

class Fantasy(commands.Cog):
    
    def __init__(self,client):
        self.client = client
        
    @commands.command(aliases=("createaccount","create_account","newplayer", "new_player","newaccount","new_account","add_fantasy_player"))
    async def new_fantasy_player(self,ctx,league):
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
            await ctx.send('Please include the league you play in. If you are not a player, use ".new_fantasy_player none"')
        
    @commands.command(aliases=("pick","add_player",))
    async def pick_player(self,ctx,player,slot=1):
        author = ctx.message.author.name
        person = author
        answer = fantasy.pick_player(person,player,slot)
        await ctx.send(answer)
        
    @pick_player.error
    async def pick_player_error(self,ctx,error):
        if isinstance(error,commands.MissingRequiredArgument):
            await ctx.send('Please include a player')
            
    @commands.command(aliases=("drop",))
    async def drop_player(self,ctx,slot):
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
        answer = fantasy.generate_leaderboard()
        await ctx.send(answer)
        
    @commands.command(aliases=("show","team","showteam",))
    async def show_team(self,ctx,author="none"):
        if author == "none":
            author = ctx.message.author.name
        answer = fantasy.show_team(author)
        await ctx.send(answer)
    
    @commands.command(aliases=("player","playerinfo","info",))
    async def player_info(self,ctx,player):
        answer = fantasy.info(player)
        await ctx.send(answer)
        
    @commands.command()
    async def fantasy_help(self,ctx):
        answer = """
Welcome to RLPC Fantasy! This is a just-for-fun fantasy league in which people can build a team of RLPC players and compete against other fantasy teams.
**To get started, type .new_fantasy_player to create a new fantasy account.**

**__RULES/STRUCTURE__**
 - Each fantasy team has 5 players
 - You can pick up players at any time EXCEPT for Tuesdays and Thursdays (Gamedays)
 - Points are calculated after every gameday (Wednesday/Friday)
 - Each team can do 2 transfers (replacing one player with another player) every week. Filling an empty slot doesn't add to this counter
 - Each player is given a specific "salary" based on their mmr and team. The total salary value of a fantasy team must be below 700 at all times.

**__FANTASY COMMANDS__**

**.fantasy_help** - Shows this message
**.new_fantasy_player** - Creates a fantasy team linked to your discord account. Please include the league you play in, or 'none'.
    *Example: .new_fantasy_player major*
**.team** - Shows the current fantasy team of any fantasy player. ".team" will display your own team, although you can include any discord account name (Don't use nicknames')
    *Example: .team arco*
**.info** - Gives important information about a player, such as their salary and a variety of stats.
    *Example: .info arco*
**.pick_player** - Adds a player to your fantasy team, in one of 5 player slots. Please specify which player you want, as well as which slot.
    *Example: .pick_player arco 4*
**.drop_player** - Can also be done with '.pick_player drop [slot]', drops the player in the specified slot, replacing them with 'Not Picked'.
**.leaderboard** - Displays the current leaderboard of points
        """
        await ctx.send(answer)
        
def setup(client):
    client.add_cog(Fantasy(client))