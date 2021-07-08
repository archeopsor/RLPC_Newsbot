import discord
from discord.ext import commands
from discord.ext.commands.context import Context
from discord.ext.commands import has_permissions

from settings import prefix

class Misc(commands.Cog):

    def __init__(self, client):
        self.client = client

    @commands.command()
    async def ping(self, ctx: Context):
        await ctx.send(f'Pong! {round(self.client.latency * 1000)}ms')

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
            channels = self.client.session.admin.find_one({'purpose': 'channels'})[
                'channels']['upset_alerts']

            if ctx.channel.id in channels:
                self.client.session.admin.find_one_and_update({'purpose': 'channels'}, {
                    '$pull': {'channels.upset_alerts': ctx.channel.id}})
                return await ctx.send("This channel will no longer receive alerts.")
            else:
                self.client.session.admin.find_one_and_update({'purpose': 'channels'}, {
                    '$push': {'channels.upset_alerts': ctx.channel.id}})
                return await ctx.send("This channel will now receive alerts!")
        return

    @upset_alerts.error
    async def upset_alerts_error(self, ctx: Context, error: commands.CommandError):
        if isinstance(error, commands.CheckFailure):
            return await ctx.send("You don't have admin perms for this server.")

