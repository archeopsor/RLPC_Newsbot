import discord
from discord.ext import commands
from discord import app_commands
from discord.ext.commands.context import Context
from discord.ext.commands import has_permissions
from discord.ext.commands.errors import (
    CommandRegistrationError,
    MissingRequiredArgument,
)
import pandas as pd
import dataframe_image as dfi
from datetime import datetime, timedelta
import os
from RLPC_Newsbot import Newsbot

from tools.sheet import Sheet
from tools.mongo import Session
from rlpc.players import Identifier, TeamsHandler

from settings import prefix, leagues, divisions, sheet_p4, sheet_indy, stream_sheet
from errors.player_errors import TeamNotFoundError
from errors.sheets_errors import SheetToDfError


class Misc(commands.Cog, name = "Misc"):
    def __init__(
        self,
        bot: Newsbot,
        session: Session = None,
        identifier: Identifier = None,
        p4sheet: Sheet = None,
        indysheet: Sheet = None,
        teams: TeamsHandler = None,
    ):
        self.bot = bot

        self.session = session if session else Session()
        self.identifier = identifier if identifier else Identifier()
        self.p4sheet = p4sheet if p4sheet else Sheet(sheet_p4)
        self.indysheet = indysheet if indysheet else Sheet(sheet_indy)
        self.teams = teams if teams else TeamsHandler(session = self.session, p4sheet = self.p4sheet)
        self.streamsheet = Sheet(stream_sheet)

        super().__init__()

    @commands.command()
    @commands.is_owner()
    async def sync(self, ctx: Context) -> None:
        await self.bot.tree.sync()
        # await self.bot.tree.sync(guild=self.bot.get_guild(224552524173148171))
        await ctx.send("Synced!")

    @app_commands.command(name="ping")
    async def ping(self, interaction: discord.Interaction):
        """Shows the bot's latency"""
        await interaction.response.send_message(f"Pong! {round(self.bot.latency * 1000)}ms", ephemeral=True)

    @app_commands.command(name="upset_alerts")
    @has_permissions(manage_channels=True)
    async def upset_alerts(self, interaction: discord.Interaction) -> str:
        """Subscribes the given channel to upset alerts

        Args:
            ctx (Context): discord context object

        Returns:
            str: response sent in discord
        """
        async with interaction.channel.typing():
            channels = self.bot.session.admin.find_one({"purpose": "channels"})[
                "channels"
            ]["upset_alerts"]

            if interaction.channel_id in channels:
                self.bot.session.admin.find_one_and_update(
                    {"purpose": "channels"},
                    {"$pull": {"channels.upset_alerts": interaction.channel_id}},
                )
                return await interaction.response.send_message("This channel will no longer receive alerts.")
            else:
                self.bot.session.admin.find_one_and_update(
                    {"purpose": "channels"},
                    {"$push": {"channels.upset_alerts": interaction.channel_id}},
                )
                return await interaction.response.send_message("This channel will now receive alerts!")
        return

    @upset_alerts.error
    async def upset_alerts_error(self, ctx: Context, error: commands.CommandError):
        if isinstance(error, commands.CheckFailure):
            return await ctx.send("You don't have manage_channel perms for this server.")

    @app_commands.command(name="schedule")
    async def schedule(self, interaction: discord.Interaction, *, team: str):
        """Shows the schedule for any team.

        Args:
            team (str): Team name
        """
        async with interaction.channel.typing():
            team: str = team.title()

            if team not in divisions.keys():
                return await interaction.response.send_message(f"Couldn't find team `{team}`", ephemeral = True)

            league: str = self.identifier.find_league(team)

            sheet: Sheet = (
                self.p4sheet
                if league.lower() in ["major", "aaa", "aa", "a"]
                else self.indysheet
            )

            try:
                all_games: pd.DataFrame = sheet.to_df(f"{league} Schedule!O4:X188")
            except SheetToDfError:
                return await interaction.response.send_message("Couldn't find a schedule for this team.")
            if all_games.empty:
                return await interaction.response.send_message(
                    "Schedules couldn't be found, possibly because they aren't on the sheet. Contact arco if you believe this is an error."
                )

            # If any non-preseason results are in, get rid of the preseason games
            if 'N' in all_games[all_games['Score'] != ""]['Preseason'].values:
                all_games = all_games[all_games['Preseason'] == "N"]

            all_games.columns.values[3] = "Team 1"
            all_games.columns.values[5] = "Team 2"
            all_games.columns.values[8] = "Logs"
            all_games.drop(
                columns=["Preseason", "Playoff", "Game Logs Processed"], inplace=True
            )

            schedule: pd.DataFrame = all_games.loc[
                (all_games["Team 1"] == team) | (all_games["Team 2"] == team)
            ]
            schedule.set_index("Day", drop=True, inplace=True)

            dfi.export(schedule, "schedule.png", table_conversion="matplotlib")
            path = os.path.abspath("schedule.png")
            file = discord.File(path)
            await interaction.response.send_message(file=file)
            file.close()
            return os.remove(path)

    @app_commands.command(name="roster")
    async def roster(self, interaction: discord.Interaction, *, team: str):
        """Shows a team's roster as well as other useful information about the team

        Args:
            team (str): Team name
        """
        async with interaction.channel.typing():
            try:
                data = self.teams.get_data(team)
            except TeamNotFoundError:
                return await interaction.response.send_message(f"Couldn't find team: {team}", ephemeral=True)

            embed = discord.Embed(title=team.title(), color=0x00008B)
            embed.set_thumbnail(url=self.teams.get_logo_url(data))
            embed.add_field(name="**GM**", value=self.teams.get_gm(data), inline=True)
            embed.add_field(name="**AGM**", value=self.teams.get_agm(data), inline=True)
            embed.add_field(
                name="**Captain**", value=self.teams.get_captain(data), inline=True
            )
            embed.add_field(
                name="**Org**", value="\n".join(self.teams.get_org(data)["Teams"])
            )
            embed.add_field(
                name="**Roster**", value="\n".join(self.teams.get_roster(team))
            )
            embed.add_field(
                name="**League**", value=self.teams.get_league(data), inline=True
            )

        for i, field in enumerate(embed.fields):
            if field.value == "":
                embed.set_field_at(i, name=field.name, value="-")

        return await interaction.response.send_message(embed=embed)

    @app_commands.command()
    async def stream(self, interaction: discord.Interaction):
        """Shows the upcoming stream schedule"""
        async with interaction.channel.typing():
            try:
                data = self.streamsheet.to_df("S17 Stream Schedule!D3:K")
            except: 
                return await interaction.response.send_message("Couldn't find the stream schedule :(")

            data = data.rename(
                columns={
                    "Date:": "Date",
                    "League:": "League",
                    "Series:": "Series",
                    "Time:": "Time",
                    "Streamer:": "Streamer",
                    "Play by Play:": "PBP",
                    "Color:": "Color",
                }
            )
            data = data[
                (data["League"].str.lower().isin(leagues.keys())) & (data['Series'].str.strip() != "-") & (data['Date'].str.strip() != "")
            ]  # Get rid of empty rows and TBD rows
            data["Date"] = pd.to_datetime(
                data["Date"], format="%m/%d/%y", errors="coerce"
            )
            monday = datetime.today() - timedelta(days=datetime.today().weekday())
            week = timedelta(days=7)

            sched = data[data["Date"] > datetime.today()].set_index("Date")
            filename = "stream_schedule.png"
            dfi.export(sched, filename, table_conversion="matplotlib")
            path = os.path.abspath(filename)
            file = discord.File(path)

            await interaction.response.send_message(file=file)
        return os.remove(path)
