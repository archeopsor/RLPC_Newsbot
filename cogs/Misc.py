import discord
from discord.ext import commands
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

from tools.sheet import Sheet
from tools.mongo import Session
from rlpc.players import Identifier, Teams

from settings import prefix, leagues, divisions, sheet_p4, sheet_indy, stream_sheet
from errors.player_errors import TeamNotFoundError


class Misc(commands.Cog):
    def __init__(
        self,
        bot,
        session: Session = None,
        identifier: Identifier = None,
        p4sheet: Sheet = None,
        indysheet: Sheet = None,
        teams: Teams = None,
    ):
        self.bot = bot

        if not session:
            self.session = Session()
        else:
            self.session = session
        if not identifier:
            self.identifier = Identifier()
        else:
            self.identifier = identifier
        if not p4sheet:
            self.p4sheet = Sheet(sheet_p4)
        else:
            self.p4sheet = p4sheet
        if not indysheet:
            self.indysheet = Sheet(sheet_indy)
        else:
            self.indysheet = indysheet
        if not teams:
            self.teams = Teams(session=self.session, p4sheet=self.p4sheet)
        else:
            self.teams = teams
        self.streamsheet = Sheet(stream_sheet)

    @commands.command()
    async def ping(self, ctx: Context):
        await ctx.send(f"Pong! {round(self.bot.latency * 1000)}ms")

    @commands.command(
        aliases=(
            "upset",
            "upsets",
        )
    )
    @has_permissions(manage_channels=True)
    async def upset_alerts(self, ctx: Context) -> str:
        """Subscribes the given channel to upset alerts

        Args:
            ctx (Context): discord context object

        Returns:
            str: response sent in discord
        """
        async with ctx.typing():
            channels = self.bot.session.admin.find_one({"purpose": "channels"})[
                "channels"
            ]["upset_alerts"]

            if ctx.channel.id in channels:
                self.bot.session.admin.find_one_and_update(
                    {"purpose": "channels"},
                    {"$pull": {"channels.upset_alerts": ctx.channel.id}},
                )
                return await ctx.send("This channel will no longer receive alerts.")
            else:
                self.bot.session.admin.find_one_and_update(
                    {"purpose": "channels"},
                    {"$push": {"channels.upset_alerts": ctx.channel.id}},
                )
                return await ctx.send("This channel will now receive alerts!")
        return

    @upset_alerts.error
    async def upset_alerts_error(self, ctx: Context, error: commands.CommandError):
        if isinstance(error, commands.CheckFailure):
            return await ctx.send("You don't have admin perms for this server.")
        # else:
        #     await self.bot.log_error(error.original, ctx.channel, ctx.command, ctx.kwargs)

    @commands.command(
        aliases=(
            "schedules",
            "scheduling",
        )
    )
    async def schedule(self, ctx: Context, *, team: str):
        async with ctx.typing():
            team: str = team.title()
            if team not in divisions.keys():
                return await ctx.send("Couldn't find team " + team)

            league: str = self.identifier.find_league(team)
            sheet: Sheet = (
                self.p4sheet
                if league.lower() in ["major", "aaa", "aa", "a"]
                else self.indysheet
            )

            all_games: pd.DataFrame = sheet.to_df(f"{league} Schedule!O4:X")
            if all_games.empty:
                return await ctx.send(
                    "Schedules couldn't be found, possibly because they aren't on the sheet. Contact arco if you believe this is an error."
                )

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
            await ctx.send(file=file)
            return os.remove(path)

    @schedule.error
    async def schedule_error(self, ctx: Context, error):
        if isinstance(error, MissingRequiredArgument):
            return await ctx.send("Please specify a team.")
        elif isinstance(error, FileNotFoundError):
            return
        # else:
        #     await self.bot.log_error(error.original, ctx.channel, ctx.command, ctx.kwargs)

    @commands.command(aliases=("rosters",))
    async def roster(self, ctx: Context, *, team: str):
        async with ctx.typing():
            try:
                data = self.teams.get_data(team)
            except TeamNotFoundError:
                return await ctx.send("Couldn't find team: " + team)

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

        return await ctx.send(embed=embed)

    @commands.command()
    async def stream(self, ctx: Context):
        async with ctx.typing():
            try:
                data = self.streamsheet.to_df("Sheet1!C3:I")
            except: # TODO Make this more specific
                return await ctx.send("Couldn't find the stream schedule :(")

            data = data.rename(columns={
                'Date:': "Date",
                "League:": "League",
                "Series:": "Series",
                "Time:": "Time",
                "Streamer:": "Streamer",
                "Play by Play:": "PBP",
                "Color:": "Color"
            })
            data = data[data["League"].str.lower().isin(leagues.keys())]  # Get rid of empty rows and TBD rows
            data['Date'] = pd.to_datetime(data['Date'], format='%m/%d/%y', errors="coerce")
            monday = datetime.today() - timedelta(days=datetime.today().weekday())
            week = timedelta(days=7)

            sched = data[data['Date'] > datetime.today()].set_index("Date")
            filename = "stream_schedule.png"
            dfi.export(sched, filename, table_conversion='matplotlib')
            path = os.path.abspath(filename)
            file = discord.File(path)

            await ctx.send(file=file)
        return os.remove(path)
