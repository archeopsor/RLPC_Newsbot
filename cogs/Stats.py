import discord
from discord import app_commands
from discord.ext.commands.errors import MissingRequiredArgument
from discord.ext.commands.context import Context
from discord.ext import commands

import os
import pandas as pd
import numpy as np
import dataframe_image as dfi
from RLPC_Newsbot import Newsbot

from tools.mongo import Session
from rlpc import mmr
from rlpc.stats import StatsHandler, get_latest_gameday
from rlpc.players import PlayersHandler, Identifier, TeamsHandler
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

from errors.sheets_errors import GetSheetError
from errors.stats_errors import *
from errors.general_errors import *


class Stats(commands.Cog):  # pragma: no cover
    def __init__(
        self,
        bot: Newsbot,
        session: Session = None,
        p4sheet: Sheet = None,
        indysheet: Sheet = None,
        gdsheet: Sheet = None,
        identifier: Identifier = None,
        players: PlayersHandler = None,
        stats: StatsHandler = None,
        teams: TeamsHandler = None,
    ):
        self.bot = bot

        self.session = session if session else Session()
        self.p4sheet = p4sheet if p4sheet else Sheet(sheet_p4)
        self.indysheet = indysheet if indysheet else Sheet(sheet_indy)
        self.gdsheet = gdsheet if gdsheet else Sheet(gdstats_sheet)
        self.identifier = identifier if identifier else Identifier(session=self.session, p4sheet=self.p4sheet)
        self.players = players if players else PlayersHandler(session=self.session, p4sheet=self.p4sheet, identifier=self.identifier)
        self.teams = teams if teams else TeamsHandler(session=self.session)
        self.stats = stats if stats else StatsHandler(session=self.session, p4sheet=self.p4sheet, indysheet=self.indysheet, gdsheet=self.gdsheet, teams=self.teams, identifier=self.identifier)

    @app_commands.command(name="valid")
    async def valid(self, interaction: discord.Interaction):
        """Shows a list of stats that can be used by the Newsbot"""
        await interaction.response.send_message(
            f"""**Valid stats** (may need to specify 'sheet' at the end of the command to use these): ['Series Played', 'Games Played', 'Goals', 'Assists', 'Saves', 'Shots', 'Points', 'Goals per game', 'Assists per game', 'Saves per game', 'Shooting %', 'Winning %', 'Wins', 'Points per Game', 'Shots Per Game'].

**Advanced stats** (may need to specify 'db' or 'advanced' at the end of the command to use these): {valid_stats}.

**Compound stats** (may need to specify 'db' or 'advanced' at the end of the command to use these):  ['Winning %', 'Shooting %', 'Shooting % Against', 'Points' *(Goals + Assists)*, 'MVP Rate' *(MVPs / Games Won)*, '% Time Slow', '% Time Boost', '% Time Supersonic', '% Time Ground', '% Time Low Air', '% Time High Air', '% Most Back', '% Most Forward', '% Goals Responsible' *(Conceded When Last / Goals Against)*, 'Position Ratio *(Time Infront Ball / Time Behind Ball)*]"""
        , ephemeral=True)

    @app_commands.command(name="power_rankings")
    async def pr(self, interaction: discord.Interaction, league: str):
        """Gets the most recent power rankings from the power rankings sheet

        Args:
            league (str): League name
        """
        async with interaction.channel.typing():

            try:
                league = leagues[league.lower()]
            except KeyError:
                return await interaction.response.send_message(f"Couldn't understand league: `{league}`", ephemeral=True)

            await interaction.response.defer()

            try:
                rankings = self.stats.power_rankings(league)
            except PRSheetError as error:
                await interaction.followup.send(
                    "There was an error getting power rankings data. This has been reported, and will hopefully be fixed soon.", ephemeral=True
                )
                return await self.bot.log_error(
                    error, interaction.channel, interaction.command, None
                )
            except NoPRError:
                return await interaction.followup.send("There are no power rankings available.", ephemeral=True)

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

        await interaction.followup.send(embed=embed)

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

    @app_commands.command(name="stats")
    async def get_player_stats(
        self, interaction: discord.Interaction, player: str, use_sheet: bool = False, stat: str = "all", pergame: bool = False
    ):
        """Gets this season's stats for any player

        Args:
            player (str): Player's name
            use_sheet (bool, optional): If you want to get stats from the RLPC sheet rather than from the Newsbot's database 
            stat (str, optional): If you want to look at a specific stat, or a category of stats. 
            pergame (bool, optional): If you want to look at per-game stats. 
        """
        async with interaction.channel.typing():

            await interaction.response.defer()

            if player == "me":
                discord_id = str(interaction.user.id)
                try:
                    player = self.stats.get_me(discord_id)
                except FindMeError as error:
                    await interaction.followup.send(
                        "You don't appear to have an up-to-date discord id on record. Try using the name that shows up on the RLPC spreadsheet."
                    )

            try:
                if use_sheet:
                    answer = self.stats.get_player_stats_sheet(player, stat)
                else:
                    answer = self.stats.get_player_stats_db(player, stat, pergame)
            except InvalidStatError:
                return await interaction.followup.send(
                    f"Couldn't understand stat `{stat}`. If this is part of a username, surround the username in quotes."
                )
            except (StatsError, KeyError, FindPlayersError, PlayerNotFoundError):
                return await interaction.followup.send(
                    f"Couldn't find `{player}`'s stats. If there are spaces in the username, surround the username in quotes. Contact arco if you think this is a bug."
                )

            embed = discord.Embed(
                title=f"{answer.values[0][0]}'s Stats", color=0x3333FF,
                description=f"Source: {'Sheet' if use_sheet else 'Newsbot Database'}{', Per Game: True' if pergame else ''}"
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

        await interaction.followup.send(embed=embed)
        if not use_sheet and stat == "all":
            return await interaction.followup.send("Add 'boost', 'movement', or 'positioning' to the end of your command (but before 'pg' if you want to see per game stats) to see more stats.")
        else:
            return

    @app_commands.command(name="top")
    async def top(self, interaction: discord.Interaction, stat: str, league: str = "all", use_sheet: bool = False, per_game: bool = False, limit: int = 10, ascending: bool = False):
        """Shows the leaderboards for any stat

        Args:
            stat (str): Name of stat to use (all stats are listed in /valid)
            league (str, optional): League name
            use_sheet (bool, optional): If you want to pull stats from the rlpc spreadsheet rather than the newsbot database
            per_game (bool, optional): If you want per-game stats
            limit (int, optional): How many people should be shown in the leaderboard
            ascending (bool, optional): If you want to show the lowest values on the leaderboard
        """
        async with interaction.channel.typing():

            await interaction.response.defer()

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
                    useSheet=use_sheet,
                    league=league,
                    stat=stat,
                    limit=limit,
                    pergame=per_game,
                    asc=ascending,
                )
            except InvalidStatError as error:
                return await interaction.followup.send(
                    f'Could not understand stat `{error.stat.title()}`. Try using "/valid" for a list of available stats.'
                )
            except StatsError as error:
                return await interaction.followup.send(
                    f'To use stats from the sheet, you must specify a league.'
                )
            except (FindPlayersError, StatSheetError, GetSheetError) as error:
                await interaction.followup.send(
                    f"There was an error getting player data. This has been reported, and will hopefully be fixed soon."
                )
                return await self.bot.log_error(
                    error, interaction.channel, interaction.command, None
                )

            embed = discord.Embed(
                title=f'{stat} {"Per Game " if per_game else ""}Leaderboard',
                description=f"League: {league}, Source: {'Sheet' if use_sheet else 'Newsbot Database'}",
            )
            for i, player in enumerate(lb.index):
                val = lb[player]
                if val % 1 == 0:
                    val = round(val)
                embed.add_field(name=f"{i+1}) {player}", value=val, inline=False)

        return await interaction.followup.send(embed=embed)

    @app_commands.command(name="gd_stats")
    async def gdstats(self, interaction: discord.Interaction, player: str, day: int = 0, stat: str = "None", per_game: bool = False):
        """Shows a player's stats from any gameday

        Args:
            player (str): Player name
            day (int, optional): Which gameday you want to get stats for (1 - 18)
            stat (str, optional): If you want to look at a specific stat
            per_game (bool, optional): If you want per-game stats
        """
        async with interaction.channel.typing():

            await interaction.response.defer()
            
            if day == 0:
                day = get_latest_gameday()

            try:
                data = self.stats.gdstats(player, day, stat=stat, pergame=per_game)
            except InvalidDayError:
                return await interaction.followup.send(
                    f"`{day}` is not a valid gameday. Please enter a number between 1 and 18."
                )
            except (GDStatsSheetError, GetSheetError):
                return await interaction.followup.send(
                    f"It doesn't look like there are any stats available for gameday `{day}`"
                )
            except PlayerNotFoundError:
                return await interaction.followup.send(
                    f"Could not find stats for `{player}` on gameday `{day}`."
                )

            # Try to round data points
            for i in data.index[1:-1]:
                if data[i] % 1 == 0:
                    data[i] = int(data[i])

            if stat == "None":
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

                return await interaction.followup.send(embed=embed)

            else:
                return await interaction.followup.send(data.loc[stat.title()])

    @app_commands.command(name="team_stats")
    async def teamstats(self, interaction: discord.Interaction, league_or_team: str):
        """Shows stats for all players on a team, or all teams in a league. 

        Args:
            league_or_team (str): League name or Team name
        """
        async with interaction.channel.typing():

            await interaction.response.defer()
            val = league_or_team.lower()
            league = None
            team = None

            if val in leagues.keys():
                league = leagues[val]
            elif val.title() in divisions.keys():
                team = val.title()
            else:
                return await interaction.followup.send(
                    f"Couldn't understand `{league_or_team}`. Please specify either a league or a team."
                )

            if league:
                stats = self.stats.teamstats(league=league)
            else:
                stats = self.stats.teamstats(team=team)

            dfi.export(stats, "stats.png", table_conversion="matplotlib")
            path = os.path.abspath("stats.png")
            file = discord.File(path)
            await interaction.followup.send(file=file)

            file.close()
            return os.remove(path)

    @commands.command(aliases=())  # TODO: Finish this
    async def statsrank(self, ctx: Context, *, msg):
        async with ctx.typing():
            pass

    @app_commands.command(name="difference")
    async def difference(self, interaction: discord.Interaction, player: str, stat: str):
        """Shows how a player improved or worsened for any stat in their most recent series

        Args:
            player (str): Player name
            stat (str): Name of a stat. Use /valid for a list of stats
        """
        async with interaction.channel.typing():

            await interaction.response.defer()

            if player.lower() == "me":
                discord_id = str(interaction.user.id)
                try:
                    player = self.stats.get_me(discord_id)
                except FindMeError as error:
                    return await interaction.followup.send(
                        "You don't appear to have an up-to-date discord id on record. Try using the name that shows up on the RLPC spreadsheet."
                    )

            try:
                diff, total, recent = self.stats.difference(player, stat)
                diff = round(diff * 100)
            except InvalidStatError as e:
                return await interaction.followup.send(
                    "Couldn't understand stat: "
                    + e.stat
                    + '. You may need to surround it in double quotes (") to be understood correctly.'
                )
            except PlayerNotFoundError as e:
                return await interaction.followup.send(
                    "Couldn't understand player: "
                    + f"`{e.player}`"
                    + '. You may need to surround it in double quotes (") to be understood correctly.'
                )
            except (ZeroError, InvalidDayError):
                return await interaction.followup.send(
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

        return await interaction.followup.send(embed=embed)
