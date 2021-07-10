from errors.stats_errors import FindMeError
from discord.ext import commands
import discord
from discord.ext.commands.context import Context

from fantasy_infrastructure import FantasyHandler

from rlpc import mmr
from tools import accounts
from tools.sheet import Sheet
from tools.mongo import Session

from settings import prefix, sheet_p4

bot = commands.Bot(command_prefix=prefix)


class Fantasy(commands.Cog):

    def __init__(self, bot, session: Session = None, fantasy: FantasyHandler = None, p4_sheet: Sheet = None):
        self.bot = bot
        if not p4_sheet:
            self.p4_sheet = Sheet(sheet_p4)
        else:
            self.p4_sheet = p4_sheet
        if not session:
            self.session = Session()
        else:
            self.session = session
        if not fantasy:
            self.fantasy = FantasyHandler(self.session)
        else:
            self.fantasy = fantasy

    @commands.command(aliases=("createaccount", "create_account", "newplayer", "new_player", "newaccount", "new_account", "add_fantasy_player", "new", "signup"))
    async def new_fantasy_player(self, ctx: Context, league: str = None):
        async with ctx.typing():
            if not league:
                pass
            elif league.casefold() not in ["major", "aaa", "aa", "a", "independent", "indy", "maverick", "mav"]:
                return await ctx.send(f"{league} could not be understood")

            author = ctx.message.author.name
            id = ctx.message.author.id

            answer = accounts.create_account(
                author, id, league=league, session=self.session)
        return await ctx.send(answer)

    @new_fantasy_player.error
    async def new_fantasy_player_error(self, ctx: Context, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f'Please include the league you play in. If you are not a player, use "{prefix}new none"')
        else:
            self.bot.log_error(error, ctx.channel, ctx.command)

    @commands.command(aliases=("pick", "pickplayer", "addplayer", "add_player", "buy"))
    async def pick_player(self, ctx: Context, *, player: str):
        async with ctx.typing():
            answer = self.fantasy.pick_player(ctx.author.id, player)
        await ctx.send(answer)

    @pick_player.error
    async def pick_player_error(self, ctx: Context, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send('Please include a player')
        else:
            self.bot.log_error(error, ctx.channel, ctx.command)

    @commands.command(aliases=("drop", "dropplayer", "removeplayer", "remove_player", "sell"))
    async def drop_player(self, ctx: Context, player: str):
        async with ctx.typing():
            try:
                answer = self.fantasy.drop_player(ctx.author.id, player)
            except:
                return "There was an error dropping " + player + ". Contact arco if you think this is a bug."
        await ctx.send(answer)

    @drop_player.error
    async def drop_player_error(self, ctx: Context, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("Please include the player you would like dropped")
        else:
            self.bot.log_error(error, ctx.channel, ctx.command)

    @commands.command(aliases=("leaderboard", "lb", "standings",))
    async def generate_leaderboard(self, ctx: Context):
        async with ctx.typing():
            answer = self.fantasy.fantasy_lb()
            leaderboard = discord.Embed(
                title="Fantasy Leaderboard", color=0xffff00)
            for i, player in enumerate(answer.index):
                leaderboard.add_field(
                    name=f'{i+1}: {player}', value=answer.loc[player], inline=False)
        await ctx.send(embed=leaderboard)

    @commands.command(aliases=("show", "team", "showteam",))
    async def show_team(self, ctx: Context, *, author: str = "none"):
        async with ctx.typing():
            if author == "none":
                author = ctx.author.name

            try:
                author_id = self.session.fantasy.find_one(
                    {'username': author})['discord_id']
            except:
                return await ctx.send(f"Couldn't find a fantasy account for {author}")

            answer = self.fantasy.show_team(author_id)
            team = discord.Embed(title=f"{author}'s team", color=0x008080)

            if answer['account_league'] != '':
                team.add_field(name="Account League",
                               value=answer['account_league'], inline=True)
            else:
                team.add_field(name="Account League",
                               value="None", inline=True)

            for i in range(5):  # Get players and points and add to embed
                try:
                    player_id = answer['players'][i]
                    player: dict = self.session.players.find_one(
                        {'_id': player_id})
                    player_history: list = [
                        x for x in answer['player_history'] if x['Player'] == player_id]
                    # Gets points of most recent entry of player
                    points: int = player_history[-1]['Points']

                    team.add_field(
                        name=f"Player {i+1}", value=f"{player['username']} ({points})", inline=True)

                except IndexError:
                    team.add_field(
                        name=f"Player {i+1}", value="Not Picked", inline=True)

            team.add_field(name="Transfers Left",
                           value=answer['transfers_left'], inline=True)
            team.add_field(name="Salary", value=answer['salary'], inline=True)
            team.add_field(name="Total Points",
                           value=answer['points'], inline=True)
        await ctx.send(embed=team)

    # TODO: Add field to show how many teams the player is on
    @commands.command(aliases=("player", "playerinfo", "info",))
    async def player_info(self, ctx: Context, *, player):
        async with ctx.typing():
            pg = False
            if 'pg' in player:
                player = player[:-3]
                pg = True
            if 'me' in player.lower().split(' '):
                waitingMsg: discord.Message = await ctx.send("One second, retreiving discord ID and stats")
                try:
                    discord_id = str(ctx.author.id)
                    player = self.bot.stats.get_me(discord_id)
                except FindMeError:
                    return await ctx.send("You don't appear to have an up-to-date discord id on record. Try using the name that shows up on the RLPC spreadsheet.")
                await waitingMsg.delete(delay=3)

            try:
                answer = self.fantasy.info(player, pg=pg)
            except Exception: # TODO: replace with custom error
                return await ctx.send(f"Couldn't find a player named {player}.")

            player_card = discord.Embed(
                title=f"{player}'s player info", color=0xff0000)
            player_card.add_field(
                name="Region", value=answer['info']['region'], inline=True)
            player_card.add_field(
                name="Platform", value=answer['info']['platform'], inline=True)
            player_card.add_field(
                name="MMR", value=answer['info']['mmr'], inline=True)
            if answer['info']['team'] == None:
                player_card.add_field(name="Team", value="None")
            else:
                team = self.session.teams.find_one(
                    {'_id': answer['info']['team']})['team']
                player_card.add_field(name="Team", value=team, inline=True)
            player_card.add_field(
                name="League", value=answer['info']['league'], inline=True)
            player_card.add_field(
                name="Fantasy Value", value=answer['fantasy']['fantasy_value'], inline=True)
            player_card.add_field(
                name="Allowed?", value=answer['fantasy']['allowed'], inline=True)
            player_card.add_field(
                name="Fantasy Points", value=answer['fantasy']['fantasy_points'], inline=True)
        await ctx.send(embed=player_card)

    @player_info.error
    async def player_info_error(self, ctx: Context, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("Please include a player")
        else:
            self.bot.log_error(error, ctx.channel, ctx.command)

    @commands.command(aliases=("playerlb", "player_lb", "playerslb",))
    async def players(self, ctx: Context, *, message=None):
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

            lb = self.fantasy.player_lb(
                league=league, num=num, pergame=pergame)

            message = f"**1)** {lb.index[0]} ({lb[lb.index[0]]})"
            for i in range(1, num):
                message = message + \
                    f"\n**{i+1})** {lb.index[i]} ({lb[lb.index[i]]})"

        await ctx.send(f"**Player Leaderboard for fantasy points**\n*Add 'pg' to the end of the command to divide points by the # of series played*")
        try:
            await ctx.send(message)
        except:
            await ctx.send("That exceeds discord's 2000 character limit. Please try again with fewer players.")

    @commands.command(aliases=("fantasy", "fhelp", "f_help",))
    async def fantasy_help(self, ctx: Context):
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
    async def search(self, ctx: Context, arg1="", arg2="", arg3="", arg4="", arg5="", arg6="", arg7="", arg8="", arg9="", arg10="", arg11="", arg12=""):
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
                if arg.casefold() in ["name", "username", "player", "name:", "username:", "player:"]:
                    name = arguments[index]
                elif arg.casefold() in ["min", "min:", "minimum", "minimum:", "minsalary", "minsalary:", "min_salary", "min_salary:", "minimumsalary", "minimumsalary:", "minimum_salary:", "minimum_salary"]:
                    minsalary = int(arguments[index])
                elif arg.casefold() in ["max", "max:", "maximum", "maximum:", "maxsalary", "maxsalary:", "max_salary", "max_salary:", "maximumsalary", "maximumsalary:", "maximum_salary:", "maximum_salary"]:
                    maxsalary = int(arguments[index])
                elif arg.casefold() in ["team", "team:"]:
                    team = arguments[index]
                elif arg.casefold() in ["league", "league:"]:
                    league = arguments[index]
                elif arg.casefold() in ["maxdistance", "difference", "difference:", "maxdistance:", "strictness", "strictness:"]:
                    maxdistance = int(arguments[index])

            answer = self.fantasy.search(minsalary=minsalary, maxsalary=maxsalary,
                                         league=league, team=team, name=name, maxdistance=maxdistance)

            embeds = []

            for player in answer:
                embed = discord.Embed(title=player['username'], color=0x000080)
                embed.add_field(name="Username",
                                value=player['username'], inline=True)
                embed.add_field(
                    name="MMR", value=player['info']['mmr'], inline=True)
                try:
                    team = self.session.teams.find_one(
                        {'_id': player['info']['team']})['team']
                except TypeError:
                    team = player['info']['team']
                    team = team if team else "None"  # Ensure team can't end up as NoneType
                embed.add_field(name="Team", value=team, inline=True)
                embed.add_field(
                    name="League", value=player['info']['league'], inline=True)
                embed.add_field(
                    name="Fantasy Value", value=player['fantasy']['fantasy_value'], inline=True)
                embed.add_field(
                    name="Allowed?", value=player['fantasy']['allowed'], inline=True)
                embeds.append(embed)

        if len(embeds) == 0:
            return await ctx.send("There were no players matching those parameters")
        elif len(embeds) == 1:
            await ctx.send("Here's the only player matching those parameters")
        else:
            await ctx.send(f"Here are {len(embeds)} players matching those parameters:")
        for i in embeds:
            await ctx.send(embed=i)

        return


def setup(bot):
    bot.add_cog(Fantasy(bot))
