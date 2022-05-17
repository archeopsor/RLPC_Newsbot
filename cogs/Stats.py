from errors.sheets_errors import GetSheetError
from discord.ext.commands.errors import MissingRequiredArgument
from discord.ext.commands.context import Context
import discord
from discord.ext import commands

import os
import pandas as pd
import numpy as np
import dataframe_image as dfi

from tools.mongo import Session
from rlpc import mmr
from rlpc.stats import StatsHandler, get_latest_gameday
from rlpc.players import PlayersHandler, Identifier, Teams
from tools.sheet import Sheet
from settings import (
    prefix,
    valid_stats,
    leagues,
    sheet_p4,
    sheet_indy,
    gdstats_sheet,
    divisions,
    leagues,
)

from errors.stats_errors import *
from errors.general_errors import *


class Stats(commands.Cog):  # pragma: no cover
    def __init__(
        self,
        bot: commands.Bot,
        session: Session = None,
        p4sheet: Sheet = None,
        indysheet: Sheet = None,
        gdsheet: Sheet = None,
        identifier: Identifier = None,
        players: PlayersHandler = None,
        stats: StatsHandler = None,
        teams: Teams = None,
    ):
        self.bot = bot

        if not session:
            self.session = Session()
        else:
            self.session = session
        if not p4sheet:
            self.p4sheet = Sheet(sheet_p4)
        else:
            self.p4sheet = p4sheet
        if not indysheet:
            self.indysheet = Sheet(sheet_indy)
        else:
            self.indysheet = indysheet
        if not gdsheet:
            self.gdsheet = Sheet(gdstats_sheet)
        else:
            self.gdsheet = gdsheet
        if not identifier:
            self.identifier = Identifier(session=self.session, p4sheet=self.p4sheet)
        else:
            self.identifier = identifier
        if not players:
            self.players = PlayersHandler(session=self.session, p4sheet=self.p4sheet)
        if not teams:
            self.teams = Teams(session=self.session)
        else:
            self.teams = teams
        if not stats:
            self.stats = StatsHandler(
                session=self.session,
                p4sheet=self.p4sheet,
                indysheet=self.indysheet,
                gdsheet=self.gdsheet,
                teams=self.teams,
                identifier=self.identifier,
            )
        else:
            self.stats = stats

    @commands.command(
        aliases=(
            "validstats",
            "valid_stats",
        )
    )
    async def valid(self, ctx: Context):
        await ctx.send(
            f"""**Valid stats** (may need to specify 'sheet' at the end of the command to use these): ['Series Played', 'Games Played', 'Goals', 'Assists', 'Saves', 'Shots', 'Points', 'Goals per game', 'Assists per game', 'Saves per game', 'Shooting %', 'Winning %', 'Wins', 'Points per Game', 'Shots Per Game'].

**Advanced stats** (may need to specify 'db' or 'advanced' at the end of the command to use these): {valid_stats}.

**Compound stats** (may need to specify 'db' or 'advanced' at the end of the command to use these):  ['Winning %', 'Shooting %', 'Shooting % Against', 'Points' *(Goals + Assists)*, 'MVP Rate' *(MVPs / Games Won)*, '% Time Slow', '% Time Boost', '% Time Supersonic', '% Time Ground', '% Time Low Air', '% Time High Air', '% Most Back', '% Most Forward', '% Goals Responsible' *(Conceded When Last / Goals Against)*, 'Position Ratio *(Time Infront Ball / Time Behind Ball)*]"""
        )

    @commands.command(
        aliases=(
            "power",
            "powerrankings",
            "power_rankings",
            "rankings",
            "ranking",
        )
    )
    async def pr(self, ctx: Context, league: str):
        async with ctx.typing():
            try:
                league = leagues[league.lower()]
            except KeyError:
                return await ctx.send(f"Couldn't understand league: `{league}`")
            try:
                rankings = self.stats.power_rankings(league)
            except PRSheetError as error:
                await ctx.send(
                    "There was an error getting power rankings data. This has been reported, and will hopefully be fixed soon."
                )
                return await self.bot.log_error(
                    error, ctx.channel, ctx.command, ctx.kwargs
                )
            except NoPRError:
                return await ctx.send("There are no power rankings available.")

            embed = discord.Embed(
                title=f"{league} Power Rankings",
                description=f"Official human-generated Power Rankings for {league}. For computer rankings, use $rank",
                color=0x000080,
            )

            value_response = ""
            for row in range(16):
                value_response += f"{row+1}: {rankings.index[row]}"
                if (
                    rankings.iloc[row] == rankings.iloc[(row + 1 if row < 15 else 0)]
                    or rankings.iloc[row] == rankings.iloc[(row - 1 if row > 0 else 15)]
                ):
                    value_response += f"ᵀ ({rankings.iloc[row]})\n"
                else:
                    value_response += f" ({rankings.iloc[row]})\n"

            embed.add_field(name="Rankings", value=value_response)

        await ctx.send(embed=embed)

    @pr.error
    async def prerror(self, ctx: Context, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("You haven't chosen a league.")
        else:
            return await self.bot.log_error(
                error.original, ctx.channel, ctx.command, ctx.kwargs
            )

    @commands.command()  # TODO: fix this, add error handling, etc
    async def mmr(self, ctx: Context, *, player: str):
        async with ctx.typing():
            return await ctx.send("This command isn't fully implemented and can't currently be used.")
            players = self.p4sheet.to_df("Players!A1:R")

            player, league = self.capitalize_username(player)

            mmrs = {}
            try:
                players.loc[player]
            except:
                await ctx.send(f"Coudn't find player {player}")
                return

            for url in players.loc[player, "Tracker"].split(", "):
                platform, name = url.split("/")[-2:]
                mmrs[name] = {}
                mmrs[name]["Duels"] = mmr.playlist(platform, name, "1s")
                mmrs[name]["Doubles"] = mmr.playlist(platform, name, "2s")
                mmrs[name]["Solo Standard"] = mmr.playlist(platform, name, "ss")
                mmrs[name]["Standard"] = mmr.playlist(platform, name, "3s")

                embed = discord.Embed(title=f"{player}'s MMRs", color=0xFFFFFF)
                for playlist in list(mmrs[name]):
                    embed.add_field(
                        name=playlist,
                        value=f'{mmrs[name][playlist]["rank"]} ({mmrs[name][playlist]["rating"]})',
                    )

                await ctx.send(embed=embed)

    @commands.command(
        aliases=(
            "getstats",
            "stats",
            "get_stats",
        )
    )
    async def get_player_stats(
        self, ctx: Context, player: str, *, args: str = None
    ):
        async with ctx.typing():

            advanced: bool = True
            stat: str = "all"
            pergame: bool = False

            if player == "me":
                waitingMsg: discord.Message = await ctx.send(
                    "One second, retreiving discord ID and stats"
                )
                discord_id = str(ctx.author.id)
                try:
                    player = self.stats.get_me(discord_id)
                    await waitingMsg.delete()
                except FindMeError as error:
                    await ctx.send(
                        "You don't appear to have an up-to-date discord id on record. Try using the name that shows up on the RLPC spreadsheet."
                    )
                    return await waitingMsg.delete()


            if args:
                args = args.split()
                # TODO: Replace with structural pattern matching
                remaining: list[str] = []
                for i, word in enumerate(args):
                    if word.lower() in ['db', 'advanced', 'adv']:
                        advanced = True
                    elif word.lower() in ['sheet', 'usesheet']:
                        advanced = False
                    elif word.lower() in ['pg', 'pergame', 'rate']:
                        pergame = True
                    elif word.lower() == "per" and args[i + 1].lower() == "game":
                        pergame = True
                        args.remove(args[i + 1])
                    else:
                        remaining.append(word)

                if len(remaining) > 0:
                    stat = ' '.join(remaining)

            try:
                if advanced:
                    answer = self.stats.get_player_stats_db(player, stat, pergame)
                else:
                    answer = self.stats.get_player_stats_sheet(player, stat)
            except InvalidStatError:
                return await ctx.send(
                    f"Couldn't understand stat `{stat}`. If this is part of a username, surround the username in quotes."
                )
            except (StatsError, KeyError, FindPlayersError, PlayerNotFoundError):
                return await ctx.send(
                    f"Couldn't find `{player}`'s stats. Contact arco if you think this is a bug."
                )

            embed = discord.Embed(
                title=f"{answer.values[0][0]}'s Stats", color=0x3333FF,
                description=f"Source: {'Fantasy Database' if advanced else 'Sheet'} {', Per Game: True' if pergame else ''}"
            )

            for i, col in enumerate(answer.columns[1:]):
                value = answer.values[0][i + 1]
                if not value:
                    value = 0
                try:
                    # Drop trailing zeros if possible
                    value = float(value)
                    if value % 1 == 0.0:
                        value = int(value)
                except (ValueError, TypeError):
                    value = value
                embed.add_field(name=col, value=value)

        await ctx.send(embed=embed)
        if advanced and stat == "all":
            return await ctx.send("Add 'boost', 'movement', or 'positioning' to the end of your command (but before 'pg' if you want to see per game stats) to see more stats.")

    @get_player_stats.error
    async def stats_error(self, ctx: Context, error):
        if isinstance(error, commands.TooManyArguments):
            return await ctx.send(
                'Too many arguments, there should only be two. Put names or stats in quotes ("test name") if it contains a space.'
            )
        # else:
        #     await self.bot.log_error(error.original, ctx.channel, ctx.command, ctx.kwargs)

    @commands.command(
        aliases=(
            "topstats",
            "statslb",
            "stats_lb",
        )
    )
    async def top(self, ctx: Context, *, msg):
        async with ctx.typing():
            # Default arguments
            useSheet = False
            league = "all"
            stat = "Points"
            limit = 10
            pergame = False
            asc = False

            msg: list[str] = msg.split()
            used_args = []

            for i, word in enumerate(msg):
                if word.isdigit():
                    limit = int(word)
                    used_args.append(word)
                    continue
                if word.lower() in leagues.keys():
                    league = leagues[word.lower()]
                    used_args.append(word)
                    continue
                elif word.lower() in ["pg", "pergame"]:
                    pergame = True
                    used_args.append(word)
                    continue
                elif word.lower() == "per" and msg[i + 1].lower() == "game":
                    pergame = True
                    used_args.append(word)
                    msg.remove(msg[i + 1])
                    continue
                elif word.lower() in [
                    "asc",
                    "ascending",
                    "reverse",
                    "least",
                    "bottom",
                    "bot",
                ]:
                    asc = True
                    used_args.append(word)
                    continue
                elif word.lower() in ["sheet", "usesheet"]:  # TODO: Fix sheet stats
                    useSheet = True
                    used_args.append(word)
                    continue
                elif word.lower() in ["db", "database", "fantasy", "fantasydb"]:
                    useSheet = False
                    used_args.append(word)
                    continue

            if len(msg) > len(
                used_args
            ):  # If there are still args left, it must be the stat
                for i in used_args:
                    msg.remove(i)
                stat = " ".join(msg)

            # For common misused stat names
            statsmap = {
                "Demos": "Demos Inflicted",
                "Goal": "Goals",
                "Assist": "Assists",
                "Save": "Saves",
                "Shot": "Shots",
                "Small Boosts": "# Small Boosts",
                "Small Boost": "# Small Boosts",
                "# Small Boost": "# Small Boosts",
                "Large Boosts": "# Large Boosts",
                "Large Boost": "# Large Boosts",
                "# Large Boost": "# Large Boosts",
                "Boost Steals": "# Boost Steals",
                "Boost Steal": "# Boost Steals",
                "# Boost Steal": "# Boost Steals",
                "Boost": "Boost Used",
                "Win %": "Winning %",
                "Shot %": "Shooting %",
            }
            if stat.title() in statsmap.keys():
                stat = statsmap[stat.title()]
            else:
                stat = stat.title()

            try:
                lb = self.stats.statlb(
                    useSheet=useSheet,
                    league=league,
                    stat=stat,
                    limit=limit,
                    pergame=pergame,
                    asc=asc,
                )
            except InvalidStatError as error:
                return await ctx.send(
                    f'Could not understand stat `{error.stat.title()}`. Try using "$valid" for a list of available stats.'
                )
            except StatsError as error:
                return await ctx.send(
                    f'To use stats from the sheet, you must specify a league.'
                )
            except (FindPlayersError, StatSheetError, GetSheetError) as error:
                await ctx.send(
                    f"There was an error getting player data. This has been reported, and will hopefully be fixed soon."
                )
                return await self.bot.log_error(
                    error, ctx.channel, ctx.command, ctx.kwargs
                )

            embed = discord.Embed(
                title=f'{stat} {"Per Game " if pergame else ""}Leaderboard',
                description=f"League: {league}, Source: {'Sheet' if useSheet else 'Fantasy Database'}",
            )
            for i, player in enumerate(lb.index):
                val = lb[player]
                if val % 1 == 0:
                    val = round(val)
                embed.add_field(name=f"{i+1}) {player}", value=val, inline=False)

        return await ctx.send(embed=embed)

    @commands.command(aliases=("gameday_stats",))
    async def gdstats(self, ctx: Context, *, msg):
        async with ctx.typing():
            player = "me"
            day = None
            stat = None
            pergame = False

            msg = msg.split(" ")
            used_args = []

            for i, arg in enumerate(msg):
                if arg in "123456789101112131415161718":
                    day = int(arg)
                    used_args.append(arg)
                    continue
                if arg == "me":
                    waitingMsg = await ctx.send(
                        "One second, retreiving discord ID and stats"
                    )
                    playerid = str(ctx.author.id)
                    try:
                        player = self.stats.get_me(playerid)
                    except FindMeError:
                        await waitingMsg.delete()
                        return await ctx.send(
                            "You don't appear to have an up-to-date discord id on record. Try using the name that shows up on the RLPC spreadsheet."
                        )
                    await waitingMsg.delete()
                    used_args.append(arg)
                elif "gd" in arg:
                    used_args.append(arg)
                elif arg == "pg":
                    pergame = True
                    used_args.append(arg)
                # First word of a stat
                elif arg.lower() in [x.split()[0].lower() for x in valid_stats]:
                    stat = arg.title()
                    used_args.append(arg)
                    if len(msg) == i + 1:  # If that was the last arg in the msg
                        break
                    if msg[i + 1].lower() in [
                        x.split()[1].lower() if len(x.split()) > 1 else None
                        for x in valid_stats
                    ]:  # Second word
                        stat = stat + " " + msg[i + 1].title()
                        used_args.append(msg[i + 1])
                        if (
                            len(msg) == i + 2
                        ):  # If the next arg is the last arg in the msg
                            break
                        if msg[i + 2].lower() in [
                            x.split()[2].lower() if len(x.split()) > 2 else None
                            for x in valid_stats
                        ]:  # Third word
                            stat = stat + " " + msg[i + 2].title()
                            used_args.append(msg[i + 2])

            if len(msg) > len(
                used_args
            ):  # If there are still args left, it must be the player
                for i in used_args:
                    msg.remove(i)
                player = " ".join(msg)

            if day == None:
                day = get_latest_gameday()

            try:
                data = self.stats.gdstats(player, day, stat=stat, pergame=pergame)
            except InvalidDayError:
                return await ctx.send(
                    f"`{day}` is not a valid gameday. Please enter a number between 1 and 18."
                )
            except (GDStatsSheetError, GetSheetError):
                return await ctx.send(
                    f"It doesn't look like there are any stats available for gameday `{day}`"
                )
            except PlayerNotFoundError:
                return await ctx.send(
                    f"Could not find stats for `{player}` on gameday `{day}`."
                )

            if stat == None:
                embed = discord.Embed(
                    title=f"{player}'s Stats on Gameday {day}", color=0x3333FF
                )
                embed.add_field(
                    name="Games Played", value=f'{data.loc["Games Played"]}'
                )
                embed.add_field(name="Goals", value=f"{data.loc['Goals']}")
                embed.add_field(name="Assists", value=f"{data.loc['Assists']}")
                embed.add_field(name="Saves", value=f"{data.loc['Saves']}")
                embed.add_field(name="Shots", value=f"{data.loc['Shots']}")
                embed.add_field(
                    name="Fantasy Points", value=f"{data.loc['Fantasy Points']}"
                )

                return await ctx.send(embed=embed)

            else:
                return await ctx.send(data.loc[stat.title()])

    @commands.command(
        aliases=(
            "ts",
            "statsteam",
            "teamstat",
        )
    )
    async def teamstats(self, ctx: Context, *, msg):
        async with ctx.typing():
            league = None
            team = None

            waitingMsg: discord.Message = await ctx.send("This may take a second")

            if msg.lower() in leagues.keys():
                league = leagues[msg.lower()]
            elif msg.title() in divisions.keys():
                team = msg.title()
            else:
                return await ctx.send(
                    f"Couldn't understand `{msg}`. Please specify either a league or a team."
                )

            if league != None:
                stats = self.stats.teamstats(league=league)
            else:
                stats = self.stats.teamstats(team=team)

            dfi.export(stats, "stats.png", table_conversion="matplotlib")
            path = os.path.abspath("stats.png")
            file = discord.File(path)
            await ctx.send(file=file)
            await waitingMsg.delete()

            try:
                return os.remove(path)
            except:
                return

    @commands.command(aliases=())  # TODO: Finish this
    async def statsrank(self, ctx: Context, *, msg):
        async with ctx.typing():
            pass

    @commands.command(aliases=("diff",))
    async def difference(self, ctx: Context, player: str, stat: str):
        async with ctx.typing():
            if player.lower() == "me":
                waitingMsg: discord.Message = await ctx.send(
                    "One second, retreiving discord ID and stats"
                )
                discord_id = str(ctx.author.id)
                await waitingMsg.delete()
                try:
                    player = self.stats.get_me(discord_id)
                except FindMeError as error:
                    await waitingMsg.delete()
                    return await ctx.send(
                        "You don't appear to have an up-to-date discord id on record. Try using the name that shows up on the RLPC spreadsheet."
                    )

            try:
                diff, total, recent = self.stats.difference(player, stat)
                diff = round(diff * 100)
            except InvalidStatError as e:
                return await ctx.send(
                    "Couldn't understand stat: "
                    + e.stat
                    + '. You may need to surround it in double quotes (") to be understood correctly.'
                )
            except PlayerNotFoundError as e:
                return await ctx.send(
                    "Couldn't understand player: "
                    + f"`{e.player}`"
                    + '. You may need to surround it in double quotes (") to be understood correctly.'
                )
            except (ZeroError, InvalidDayError):
                return await ctx.send(
                    "There don't appear to be any stats to compare to. Contact arco if you believe this is an error."
                )

            embed = discord.Embed(title=f"{player}: {stat.title()}")
            embed.add_field(name="Season Average", value=round(total, 2))
            embed.add_field(name="Last Series", value=round(recent, 2))
            embed.add_field(name="Difference", value=f"{diff}%")

            if diff > 0:
                embed.set_footer(
                    text=f"In their last series, {player} got {diff}% more {stat.lower()} than their season average."
                )
            elif diff < 0:
                embed.set_footer(
                    text=f"In their last series, {player} got {abs(diff)}% less {stat.lower()} than their season average."
                )
            else:
                embed.set_footer(
                    text=f"In their last series, {player} matched their season average for {stat.lower()}."
                )

        return await ctx.send(embed=embed)
