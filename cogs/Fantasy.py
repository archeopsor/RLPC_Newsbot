from typing import List

from discord.ext import commands
import discord
from discord.ext.commands.context import Context

from fantasy_infrastructure import FantasyHandler
from rlpc import mmr
from tools import accounts
from tools.sheet import Sheet
from tools.mongo import Session

from settings import prefix, sheet_p4, leagues
from errors.fantasy_errors import *
from errors.stats_errors import FindMeError


class Fantasy(commands.Cog):
    def __init__(
        self,
        bot,
        session: Session = None,
        fantasy: FantasyHandler = None,
        p4_sheet: Sheet = None,
    ):
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

    @commands.command(
        aliases=(
            "createaccount",
            "create_account",
            "newplayer",
            "new_player",
            "newaccount",
            "new_account",
            "add_fantasy_player",
            "new",
            "signup",
        )
    )
    async def new_fantasy_player(self, ctx: Context, league: str = None):
        async with ctx.typing():
            if not league:
                pass
            elif league.casefold() not in [
                "major",
                "aaa",
                "aa",
                "a",
                "independent",
                "indy",
                "maverick",
                "mav",
            ]:
                return await ctx.send(f"{league} could not be understood")

            author = ctx.message.author.name
            id = ctx.message.author.id

            answer = accounts.create_account(
                author, id, league=league, session=self.session
            )
        return await ctx.send(answer)

    @new_fantasy_player.error
    async def new_fantasy_player_error(self, ctx: Context, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(
                f'Please include the league you play in. If you are not a player, use "{prefix}new none"'
            )
        # else:
        #     await self.bot.log_error(error, ctx.channel, ctx.command, ctx.kwargs)

    @commands.command(
        aliases=(
            "pick",
            "pickplayer",
            "addplayer",
            "add_player",
            "buy",
            "sign",
        )
    )
    async def pick_player(self, ctx: Context, *, player: str):
        async with ctx.typing():
            try:
                answer = self.fantasy.pick_player(ctx.author.id, player)
            except TimeError:
                return await ctx.send(
                    "You're not allowed to make transfers right now, probably because there are games currently happening or the previous games have not yet been entered into the database. Please contact arco if you think this is an error."
                )
            except AccountNotFoundError:
                return await ctx.send(
                    f"You don't currently have an account! Use {prefix}new to make an account"
                )
            except PlayerNotFoundError:
                return await ctx.send(
                    "That player couldn't be found in the database. Make sure you spelled their name correctly"
                )
            except TeamFullError:
                return await ctx.send(
                    "You already have 5 players on your team. Please drop someone before picking your next player"
                )
            except IllegalPlayerError:
                return await ctx.send("This player is not available to be picked.")
            except SalaryError as error:
                return await ctx.send(
                    f"This player would cause you to exceed the salary cap of {error.salary_cap} by {error.excess}. Please choose a different player, or drop someone on your team."
                )
            except AlreadyPickedError:
                return await ctx.send("You already have this player on your team!")

        await ctx.send(answer)

    @pick_player.error
    async def pick_player_error(self, ctx: Context, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("Please include a player")
        # else:
        #     await self.bot.log_error(error, ctx.channel, ctx.command, ctx.kwargs)

    @commands.command(
        aliases=("drop", "dropplayer", "removeplayer", "remove_player", "sell")
    )
    async def drop_player(self, ctx: Context, *, player: str):
        async with ctx.typing():
            try:
                answer = self.fantasy.drop_player(ctx.author.id, player)
            except AccountNotFoundError:
                return await ctx.send(
                    "You don't currently have an account! Use {prefix}new to make an account"
                )
            except NoTransactionError:
                return await ctx.send(
                    "You don't have any transfers left for this week! They will reset after Thursday's games are processed on Friday morning."
                )
            except PlayerNotFoundError:
                return await ctx.send(
                    "That player couldn't be found in the database. Make sure you spelled their name correctly"
                )
            except IllegalPlayerError:
                return await ctx.send(f"{player} isn't on your team!")

        await ctx.send(answer)

    @drop_player.error
    async def drop_player_error(self, ctx: Context, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("Please include the player you would like dropped")
        # else:
        #     await self.bot.log_error(error, ctx.channel, ctx.command, ctx.kwargs)

    @commands.command(
        aliases=(
            "leaderboard",
            "lb",
            "standings",
        )
    )
    async def generate_leaderboard(self, ctx: Context, limit: int = 15):
        async with ctx.typing():
            answer = self.fantasy.fantasy_lb().head(limit)
            leaderboard = discord.Embed(title="Fantasy Leaderboard", color=0xFFFF00)
            for i, player in enumerate(answer.index):
                leaderboard.add_field(
                    name=f"{i+1}: {player}",
                    value=round(answer.loc[player]),
                    inline=False,
                )
        await ctx.send(embed=leaderboard)

    @commands.command(
        aliases=(
            "show",
            "team",
            "showteam",
        )
    )
    async def show_team(self, ctx: Context, *, author: str = "none"):
        async with ctx.typing():
            if author == "none" or author == "me":
                author = ctx.author.name

            author_id = self.session.fantasy.find_one({"username": author})
            if author_id == None:
                return await ctx.send(f"Couldn't find a fantasy account for {author}")
            else:
                author_id = author_id["discord_id"]

            try:
                answer = self.fantasy.show_team(author_id)
            except AccountNotFoundError:
                return await ctx.send(f"Couldn't find a fantasy account for {author}")

            team = discord.Embed(title=f"{author}'s team", color=0x008080)

            if answer["account_league"] != "":
                team.add_field(
                    name="Account League", value=answer["account_league"], inline=True
                )
            else:
                team.add_field(name="Account League", value="None", inline=True)

            for i in range(5):  # Get players and points and add to embed
                try:
                    player_id = answer["players"][i]
                    player: dict = self.session.players.find_one({"_id": player_id})
                    player_history: list = [
                        x for x in answer["player_history"] if x["Player"] == player_id
                    ]
                    # Gets points of most recent entry of player
                    points: int = round(player_history[-1]["Points"])

                    team.add_field(
                        name=f"Player {i+1}",
                        value=f"{player['username']} ({points})",
                        inline=True,
                    )

                except IndexError:
                    team.add_field(
                        name=f"Player {i+1}", value="Not Picked", inline=True
                    )

            team.add_field(
                name="Transfers Left", value=answer["transfers_left"], inline=True
            )
            team.add_field(name="Salary", value=answer["salary"], inline=True)
            team.add_field(name="Total Points", value=answer["points"], inline=True)
        await ctx.send(embed=team)

    # TODO: Add field to show how many teams the player is on
    @commands.command(
        aliases=(
            "player",
            "playerinfo",
            "info",
        )
    )
    async def player_info(self, ctx: Context, *, player):
        async with ctx.typing():
            pg = False
            if "pg" in player.split():
                player = player[:-3]
                pg = True
            if "me" in player.lower().split(" "):
                waitingMsg: discord.Message = await ctx.send(
                    "One second, retreiving discord ID and stats"
                )
                try:
                    discord_id = str(ctx.author.id)
                    player = self.bot.stats.get_me(discord_id)
                except FindMeError:
                    return await ctx.send(
                        "You don't appear to have an up-to-date discord id on record. Try using the name that shows up on the RLPC spreadsheet."
                    )
                await waitingMsg.delete()

            try:
                answer = self.fantasy.info(player, pg=pg)
            except PlayerNotFoundError:
                return await ctx.send(f"Couldn't find a player named {player}.")

            player_card = discord.Embed(title=f"{player}'s player info", color=0xFF0000)
            player_card.add_field(
                name="Region", value=answer["info"]["region"], inline=True
            )
            player_card.add_field(
                name="Platform", value=answer["info"]["platform"], inline=True
            )
            player_card.add_field(name="MMR", value=answer["info"]["mmr"], inline=True)
            if answer["info"]["team"] == None:
                player_card.add_field(name="Team", value="None")
            elif answer["info"]["team"] == "Not Playing":
                player_card.add_field(name="Team", value="Not Playing")
            elif answer["info"]["team"] == "Departed":
                player_card.add_field(name="Team", value="Departed")
            elif answer["info"]["team"] == "Free Agent":
                player_card.add_field(name="Team", value="Free Agent")
            else:
                team = self.session.teams.find_one({"_id": answer["info"]["team"]})[
                    "team"
                ]
                player_card.add_field(name="Team", value=team, inline=True)
            player_card.add_field(
                name="League", value=answer["info"]["league"], inline=True
            )
            player_card.add_field(
                name="Fantasy Value",
                value=answer["fantasy"]["fantasy_value"],
                inline=True,
            )
            player_card.add_field(
                name="Allowed?", value=answer["fantasy"]["allowed"], inline=True
            )
            player_card.add_field(
                name="Fantasy Points",
                value=answer["fantasy"]["fantasy_points"],
                inline=True,
            )
        await ctx.send(embed=player_card)

    @player_info.error
    async def player_info_error(self, ctx: Context, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("Please include a player")
        # else:
        #     await self.bot.log_error(error, ctx.channel, ctx.command, ctx.kwargs)

    @commands.command(
        aliases=(
            "playerlb",
            "player_lb",
            "playerslb",
        )
    )
    async def players(self, ctx: Context, *, message=None):
        async with ctx.typing():
            league = None
            num = 10
            pergame = False
            if message != None:
                for word in message.split():
                    word: str
                    if word.isdigit():
                        num = int(word)
                    elif word.lower() in leagues.keys():
                        league = leagues[word.lower()]

                if "pergame" in message or "pg" in message:
                    pergame = True

            lb = self.fantasy.player_lb(league=league, num=num, pergame=pergame)

            num = min(num, lb.size)

            message = f"**1)** {lb.index[0]} ({lb[lb.index[0]]})"
            for i in range(1, num):
                message = message + f"\n**{i+1})** {lb.index[i]} ({lb[lb.index[i]]})"

        await ctx.send(
            f"**Player Leaderboard for fantasy points**\n*Add 'pg' to the end of the command to divide points by the # of series played*"
        )
        try:
            await ctx.send(message)
        except:
            await ctx.send(
                "That exceeds discord's 2000 character limit. Please try again with fewer players."
            )

    @commands.command(
        aliases=(
            "fantasy",
            "fhelp",
            "f_help",
        )
    )
    async def fantasy_help(self, ctx: Context):
        from help_text.fantasy_help import fantasy_help_text
        return await ctx.send(fantasy_help_text)

    @commands.command(aliases=("searchplayers",))
    async def search(
        self,
        ctx: Context,
        arg1="",
        arg2="",
        arg3="",
        arg4="",
        arg5="",
        arg6="",
        arg7="",
        arg8="",
        arg9="",
        arg10="",
        arg11="",
        arg12="",
    ):
        async with ctx.typing():
            name = "none"
            minsalary = 0
            maxsalary = 700
            league = "all"
            team = "signed"
            maxdistance = 5
            argument_labels = [arg1, arg3, arg5, arg7, arg9, arg11]
            arguments = [arg2, arg4, arg6, arg8, arg10, arg12]
            for arg in argument_labels:
                index = argument_labels.index(arg)
                if arg.casefold() in [
                    "name",
                    "username",
                    "player",
                    "name:",
                    "username:",
                    "player:",
                ]:
                    name = arguments[index]
                elif arg.casefold() in [
                    "min",
                    "min:",
                    "minimum",
                    "minimum:",
                    "minsalary",
                    "minsalary:",
                    "min_salary",
                    "min_salary:",
                    "minimumsalary",
                    "minimumsalary:",
                    "minimum_salary:",
                    "minimum_salary",
                ]:
                    minsalary = int(arguments[index])
                elif arg.casefold() in [
                    "max",
                    "max:",
                    "maximum",
                    "maximum:",
                    "maxsalary",
                    "maxsalary:",
                    "max_salary",
                    "max_salary:",
                    "maximumsalary",
                    "maximumsalary:",
                    "maximum_salary:",
                    "maximum_salary",
                ]:
                    maxsalary = int(arguments[index])
                elif arg.casefold() in ["team", "team:"]:
                    team = arguments[index]
                elif arg.casefold() in ["league", "league:"]:
                    league = arguments[index]
                elif arg.casefold() in [
                    "maxdistance",
                    "difference",
                    "difference:",
                    "maxdistance:",
                    "strictness",
                    "strictness:",
                ]:
                    maxdistance = int(arguments[index])

            answer = self.fantasy.search(
                minsalary=minsalary,
                maxsalary=maxsalary,
                league=league,
                team=team,
                name=name,
                maxdistance=maxdistance,
            )

            embeds = []

            for player in answer:
                embed = discord.Embed(title=player["username"], color=0x000080)
                embed.add_field(name="Username", value=player["username"], inline=True)
                embed.add_field(name="MMR", value=player["info"]["mmr"], inline=True)
                try:
                    team = self.session.teams.find_one({"_id": player["info"]["team"]})[
                        "team"
                    ]
                except TypeError:
                    team = player["info"]["team"]
                    team = (
                        team if team else "None"
                    )  # Ensure team can't end up as NoneType
                embed.add_field(name="Team", value=team, inline=True)
                embed.add_field(
                    name="League", value=player["info"]["league"], inline=True
                )
                embed.add_field(
                    name="Fantasy Value",
                    value=player["fantasy"]["fantasy_value"],
                    inline=True,
                )
                embed.add_field(
                    name="Allowed?", value=player["fantasy"]["allowed"], inline=True
                )
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
