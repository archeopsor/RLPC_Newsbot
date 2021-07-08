from typing_extensions import Literal
import os
from random import choice

import discord
from discord.ext import commands
from discord.ext.commands import has_permissions
from discord.ext.commands.context import Context

# Cogs
from cogs.ELO import ELO
from cogs.Fantasy import Fantasy
from cogs.Help import Help
from cogs.Links import Links
from cogs.Reddit import Reddit
from cogs.Stats import Stats

from fantasy_infrastructure import FantasyHandler
from rlpc.elo import EloHandler
from rlpc.stats import StatsHandler
from rlpc.players import Identifier, Players
from tools.mongo import Session
from tools.sheet import Sheet

from settings import prefix, power_rankings_sheet, sheet_p4, sheet_indy, forecast_sheet, gdstats_sheet

try:
    from passwords import BOT_TOKEN
except:
    BOT_TOKEN = os.environ.get('BOT_TOKEN')


class Newsbot(commands.Bot):
    def __init__(self, token: Literal = BOT_TOKEN):
        super().__init__(command_prefix=prefix, help_command=None)

        self.session = Session()
        self.p4sheet = Sheet(sheet_p4)
        self.fc_sheet = Sheet(forecast_sheet)
        self.indysheet = Sheet(sheet_indy)
        self.gdsheet = Sheet(gdstats_sheet)
        self.pr_sheet = Sheet(power_rankings_sheet)
        self.identifier = Identifier(self.session, self.p4sheet)
        self.elo = EloHandler(self.session, self.identifier)
        self.fantasy = FantasyHandler(self.session)
        self.players = Players(self.session, self.p4sheet)
        self.stats = StatsHandler(
            self.session, self.p4sheet, self.indysheet, self.pr_sheet)

        self.token = token

        self.COGS = [
            ELO(self, session=self.session, identifier=self.identifier,
                fc_sheet=self.fc_sheet, elo=self.elo),
            Fantasy(self, session=self.session,
                    fantasy=self.fantasy, p4_sheet=self.p4sheet),
            Help(self),
            Links(self),
            Reddit(self),
            Stats(self, session=self.session, p4sheet=self.p4sheet, indysheet=self.indysheet,
                  gdsheet=self.gdsheet, identifier=self.identifier, players=self.players, stats=self.stats)
        ]

        self.load_cogs()

    def load_cogs(self) -> None:
        for cog in self.COGS:
            self.add_cog(cog)

    # TODO: Add more error handling
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.NoPrivateMessage):
            await ctx.send('This command cannot be used in private messages.')
        elif isinstance(error, commands.DisabledCommand):
            await ctx.send('Sorry. This command is disabled and cannot be used.')
        elif isinstance(error, commands.CommandInvokeError):
            await ctx.send('There was an unknown error using this command.')

    async def on_ready(self):
        print('Logged in as')
        print(f"Username:  {self.user.name}")
        print(f"User ID:  {self.user.id}")
        print('---------------------------------')
        await self.change_presence(activity=discord.Game(f'{prefix}help for commands'))

    async def on_message(self, message: discord.Message):
        channels = {598237603254239238: "Major", 598237794762227713: "AAA", 598237830824591490: "AA", 598237861837537304: "A",
                    715549072936796180: "Indy", 715551351236722708: "Mav", 757714221759987792: "Ren", 757719107041755286: "Pal"}
        if int(message.channel.id) in list(channels):

            # Criteria is either 'record' or 'rating', followed by the threshold for an upset
            criteria, threshold = ("record", 4)

            # Parse messages
            league = channels[message.channel.id]

            if 'forfeit' in message.content:
                return

            game = message.content.split("\n")[2:4]
            team1 = game[0].split(": ")[0]
            team1_score = int(game[0][-1])
            team2 = game[1].split(": ")[0]
            team2_score = int(game[1][-1])

            # This is needed to put records in alert_message, even if using rating for the criteria
            records = self.pr_sheet.to_df("Team Wins!A1:AE17")
            if league == "Major":
                records = records.iloc[:, 0:3]
            elif league == "AAA":
                records = records.iloc[:, 4:7]
            elif league == "AA":
                records = records.iloc[:, 8:11]
            elif league == "A":
                records = records.iloc[:, 12:15]
            elif league == "Indy":
                records = records.iloc[:, 16:19]
            elif league == "Mav":
                records = records.iloc[:, 20:23]
            elif league == "Ren":
                records = records.iloc[:, 24:27]
            elif league == "Pal":
                records = records.iloc[:, 28:31]
            records = records.set_index(f"{league} Teams")
            team1_record = f"({records.loc[team1, 'Wins']}-{records.loc[team1, 'Losses']})"
            team2_record = f"({records.loc[team2, 'Wins']}-{records.loc[team2, 'Losses']})"
            team1_wins = int(records.loc[team1, 'Wins'])
            team2_wins = int(records.loc[team2, 'Wins'])

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
            await gamescores_channel.send(f'**{league} result**\n{team1} {team1_record}: {team1_score}\n{team2} {team2_record}: {team2_score}')

            descriptors = ["have taken down", "have defeated", "beat", "were victorious over", "thwarted",
                           "have upset", "have overpowered", "got the better of", "overcame", "triumphed over"]

            if upset:
                UPSET_ALERT_MESSAGE = f"""**UPSET ALERT**\n{team1} {team1_record} {choice(descriptors)} {team2} {team2_record} with a score of {team1_score} - {team2_score}"""

                # Send the message out to subscribed channels
                await self.wait_until_ready()
                with Session().admin as session:
                    send_to = session.find_one({'purpose': 'channels'})[
                        'upset_alerts']

                for channel in send_to:
                    channel: discord.TextChannel = self.get_channel(channel[0])

                    if channel == None:
                        continue

                    new_message = UPSET_ALERT_MESSAGE

                    for role in channel.guild.roles:
                        if role.name.casefold() == "upset alerts":
                            new_message += f'\n{channel.guild.get_role(role.id).mention}'
                    await channel.send(new_message)

        await self.process_commands(message)

    @commands.command(aliases=("upset", "upsets",))
    @has_permissions(manage_channels=True)
    async def upset_alerts(self, ctx: Context) -> str:
        """Subscribes the given channel to upset alerts

        Args:
            ctx (Context): discord context object

        Returns:
            str: response sent in discord
        """
        async with ctx.typing():
            channels = self.session.admin.find_one({'purpose': 'channels'})[
                'channels']['upset_alerts']

            if ctx.channel.id in channels:
                self.session.admin.find_one_and_update({'purpose': 'channels'}, {
                    '$pull': {'channels.upset_alerts': ctx.channel.id}})
                return await ctx.send("This channel will no longer receive alerts.")
            else:
                self.session.admin.find_one_and_update({'purpose': 'channels'}, {
                    '$push': {'channels.upset_alerts': ctx.channel.id}})
                return await ctx.send("This channel will now receive alerts!")
        return

    @upset_alerts.error
    async def upset_alerts_error(self, ctx: Context, error: commands.CommandError):
        if isinstance(error, commands.CheckFailure):
            return await ctx.send("You don't have admin perms for this server.")

    @commands.command()
    async def load(self, ctx: Context, extension: str):
        for cog in self.COGS:
            if cog.__name__ == extension:
                self.add_cog(cog)
                return await ctx.send(f"{extension} loaded")
        return await ctx.send(f"Couldn't find an extension named {extension}")

    @commands.command()
    async def reload(self, ctx: Context, extension: str):
        cog = self.get_cog(extension)
        if cog == None:
            return await ctx.send(f"Couldn't find an extension named {extension}")
        else:
            self.remove_cog(cog)
            self.add_cog(cog)
            return await ctx.send(f"{extension} reloaded")

    @commands.command()
    async def unload(self, ctx: Context, extension: str):
        self.remove_cog(extension)
        await ctx.send(f"{extension} unloaded")

    async def close(self):
        await super().close()
        await self.session.close()

    def run(self):
        super().run(self.token, reconnect=True)


if __name__ == "__main__":
    bot = Newsbot(BOT_TOKEN)
    bot.run()
