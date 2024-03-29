from typing_extensions import Literal
import os
from random import choice
import asyncio
from dotenv import load_dotenv
load_dotenv('.env')

import discord
from discord.ext import commands
from discord.ext.commands.context import Context

# Cogs
try:
    from cogs.ELO import Elo
    from cogs.Fantasy import Fantasy
    from cogs.Help import Help
    from cogs.Links import Links
    from cogs.Reddit import Reddit
    from cogs.Stats import Stats
    from cogs.Misc import Misc
    from cogs.Stocks import Stocks
except ImportError:
    pass

from rlpc.fantasy_infrastructure import FantasyHandler
from rlpc.elo import EloHandler
from rlpc.stats import StatsHandler
from rlpc.players import Identifier, PlayersHandler, TeamsHandler
from tools.mongo import Session
from tools.sheet import Sheet

from settings import (
    prefix,
    power_rankings_sheet,
    sheet_p4,
    sheet_indy,
    forecast_sheet,
    gdstats_sheet,
)

# This will get actual bot token in production but test bot in testing
BOT_TOKEN = os.environ.get("BOT_TOKEN")


class Newsbot(commands.Bot):
    def __init__(self, token: Literal = BOT_TOKEN):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix=prefix, intents=intents, help_command=None, case_insensitive=True)

        self.session = Session()
        self.p4sheet = Sheet(sheet_p4, refresh_cooldown=60)
        self.fc_sheet = Sheet(forecast_sheet)
        self.indysheet = Sheet(sheet_indy, refresh_cooldown=60)
        self.gdsheet = Sheet(gdstats_sheet)
        self.pr_sheet = Sheet(power_rankings_sheet)
        self.identifier = Identifier(self.session, self.p4sheet)
        self.elo = EloHandler(self.session, self.identifier)
        self.fantasy = FantasyHandler(self.session)
        self.players = PlayersHandler(self.session, self.p4sheet, self.identifier)
        self.teams = TeamsHandler(session=self.session)
        self.stats = StatsHandler(
            session=self.session,
            p4sheet=self.p4sheet,
            indysheet=self.indysheet,
            powerrankings=self.pr_sheet,
            teams=self.teams,
            identifier=self.identifier,
        )

        self.token = token

        self.COGS = [
            Elo(
                self,
                session=self.session,
                identifier=self.identifier,
                fc_sheet=self.fc_sheet,
                elo=self.elo,
            ),
            # Fantasy(
            #     self, session=self.session, fantasy=self.fantasy, p4_sheet=self.p4sheet
            # ),
            Help(self),
            Links(self),
            Reddit(self),
            Stats(
                self,
                session=self.session,
                p4sheet=self.p4sheet,
                indysheet=self.indysheet,
                gdsheet=self.gdsheet,
                identifier=self.identifier,
                players=self.players,
                stats=self.stats,
                teams=self.teams,
            ),
            Stocks(
                self,
                session=self.session,
            ),
            Misc(
                self,
                session=self.session,
                identifier=self.identifier,
                p4sheet=self.p4sheet,
                indysheet=self.indysheet,
                teams=self.teams,
            ),
        ]

    async def setup_hook(self):
        await self.load_cogs()

    async def load_cogs(self) -> None:
        for cog in self.COGS:
            await self.add_cog(cog)

    async def on_command_error(
        self, ctx: Context, error: discord.errors.DiscordException
    ):
        if isinstance(error, commands.NoPrivateMessage):
            await ctx.send("This command cannot be used in private messages.")
        elif isinstance(error, commands.DisabledCommand):
            await ctx.send("Sorry. This command is disabled and cannot be used.")
        elif isinstance(error, commands.CommandInvokeError):
            if isinstance(error.original, discord.errors.Forbidden):
                return await ctx.send(
                    "This bot doesn't have adequate permissions in this channel or server. You may need to re-invite the bot to your server: https://discord.com/api/oauth2/authorize?client_id=635188576446840858&permissions=380104723520&scope=applications.commands%20bot"
                )
            else:
                await self.log_error(
                    error.original, ctx.channel, ctx.command, ctx.kwargs
                )

    async def log_error(
        self,
        error: commands.CommandInvokeError,
        channel: discord.ChannelType,
        command: commands.Command,
        args: dict,
    ):
        await channel.send("There was an unexpected error using this command.")
        error_channel: discord.TextChannel = self.get_channel(862730357371305995)
        if isinstance(channel, discord.TextChannel):
            await error_channel.send(
                "**" + str(type(error)) + " in " + f"<#{channel.id}>" + "**"
            )
        elif isinstance(channel, discord.DMChannel):
            await error_channel.send(
                "**" + str(type(error)) + " in DM with " + channel.recipient.name + "**"
            )
        await error_channel.send(f"*Command: {command.name}*")
        await error_channel.send(error)
        await error_channel.send(args)

    async def on_ready(self):
        print("Logged in as")
        print(f"Username:  {self.user.name}")
        print(f"User ID:  {self.user.id}")
        print("---------------------------------")
        await self.change_presence(activity=discord.Game(f"Commands are slash commands now!"))

    async def on_message(self, message: discord.Message):
        if message.type.value == 0:
            if message.content.split()[0] in (
                '$schedule', '$stats', '$top', '$ts', '$gdstats'
            ):
                await message.reply("This bot has converted all commands to slash commands! Type '/' to see all of the slash commands available in this server. If you don't see any slash commands, you may need to reinvite the bot to your server: https://discord.com/api/oauth2/authorize?client_id=635188576446840858&permissions=380104723520&scope=applications.commands%20bot")

        channels = {
            598237603254239238: "Major",
            598237794762227713: "AAA",
            598237830824591490: "AA",
            598237861837537304: "A",
            715549072936796180: "Indy",
            715551351236722708: "Mav",
            757714221759987792: "Ren",
            757719107041755286: "Pal",
        }
        if int(message.channel.id) in list(channels):

            # Criteria is either 'record' or 'rating', followed by the threshold for an upset
            criteria, threshold = ("record", 4)

            # Parse messages
            league = channels[message.channel.id]

            if "forfeit" in message.content:
                return

            game = message.content.split("\n")[2:4]
            team1 = game[0].split(": ")[0]
            team1_score = int(game[0][-1])
            team2 = game[1].split(": ")[0]
            team2_score = int(game[1][-1])

            # This is needed to put records in alert_message, even if using rating for the criteria
            records = self.pr_sheet.to_df("Team Wins!A1:AE17")
            records = {
                "Major": records.iloc[:, 0:3],
                "AAA": records.iloc[:, 4:7],
                "AA": records.iloc[:, 8:11],
                "A": records.iloc[:, 12:15],
                "Indy": records.iloc[:, 16:19],
                "Mav": records.iloc[:, 20:23],
                "Ren": records.iloc[:, 24:27],
                "Pal": records.iloc[:, 28:31]
            }[league]

            records = records.set_index(f"{league} Teams")
            team1_record = (
                f"({records.loc[team1, 'Wins']}-{records.loc[team1, 'Losses']})"
            )
            team2_record = (
                f"({records.loc[team2, 'Wins']}-{records.loc[team2, 'Losses']})"
            )
            team1_wins = int(records.loc[team1, "Wins"])
            team2_wins = int(records.loc[team2, "Wins"])

            if criteria == "rating":
                team1_rating = self.elo.get_elo(team1)
                team2_rating = self.elo.get_elo(team2)

            upset = False
            if criteria == "record" and team2_wins - team1_wins >= threshold:
                upset = True
            elif criteria == "rating" and team2_rating - team1_rating >= threshold:
                upset = True

            # Send to #game-scores channel
            gamescores_channel = self.get_channel(836784966221430805)
            await gamescores_channel.send(
                f"**{league} result**\n{team1} {team1_record}: {team1_score}\n{team2} {team2_record}: {team2_score}"
            )

            descriptors = [
                "have taken down",
                "have defeated",
                "beat",
                "were victorious over",
                "thwarted",
                "have upset",
                "have overpowered",
                "got the better of",
                "overcame",
                "triumphed over",
            ]

            if upset:
                UPSET_ALERT_MESSAGE = f"""**UPSET ALERT**\n{team1} {team1_record} {choice(descriptors)} {team2} {team2_record} with a score of {team1_score} - {team2_score}"""

                # Send the message out to subscribed channels
                await self.wait_until_ready()
                send_to = self.session.admin.find_one({"purpose": "channels"})[
                    "channels"
                ]["upset_alerts"]

                for channel in send_to:
                    channel: discord.TextChannel = self.get_channel(int(channel))

                    if channel == None:
                        continue

                    new_message = UPSET_ALERT_MESSAGE

                    for role in channel.guild.roles:
                        role: discord.Role
                        if role.name.lower() == "upset alerts":
                            new_message += (
                                f"\n{role.mention}"
                            )
                    #await channel.send(new_message) (TEMPORARILY DISABLED)
        await self.process_commands(message)

    async def close(self):
        await super().close()
        self.session.close()

    def run(self):
        # return await super().start(self.token, reconnect=True)
        super().run(self.token, reconnect=True)


if __name__ == "__main__":
    bot = Newsbot(BOT_TOKEN)
    bot.run()
