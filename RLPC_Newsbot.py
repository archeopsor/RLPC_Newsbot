import discord
import os
from discord.ext import commands

client = commands.Bot(command_prefix = '.')
client.remove_command('help')

@client.event
async def on_ready():
    print('Bot is ready.')
    await client.change_presence(activity=discord.Game('.help for commands'))
    
@client.command()
async def ping(ctx):
    await ctx.send(f'Pong! {round(client.latency * 1000)}ms')
    
@client.command()
async def load(ctx, extension):
    client.load_extension(f'cogs.{extension}')
    
@client.command()
async def reload(ctx, extension):
    client.unload_extension(f'cogs.{extension}')
    client.load_extension(f'cogs.{extension}')
    
@client.command()
async def unload(ctx, extension):
    client.unload_extension(f'cogs.{extension}')
    
@client.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.send('Invalid command used.')

@client.command(pass_context = True)
async def help(ctx):
    message_author = ctx.message.author
    
    help_message1 = """
Hello! This is a bot primarily meant to run a fantasy league for RLPC, but it has some other functions as well!
If you have any questions, notice any issues or bugs, or have any suggestions, please feel free to contact <@160901864072806401>

**__FANTASY COMMANDS__**

**.fantasy_help** - Repeats much of this information, also includes important information about the fantasy league such as rules
**.new_fantasy_player** - Creates a fantasy team linked to your discord account. Please include the league you play in, or 'none'.
    *Example: .new_fantasy_player major*
**.team** - Shows the current fantasy team of any fantasy player. ".team" will display your own team, although you can include any discord account name (Don't use nicknames')
    *Example: .team arco
**.info** - Gives important information about a player, such as their salary and a variety of stats.
    *Example: .info arco*
**.pick_player** - Adds a player to your fantasy team, in one of 5 player slots. Please specify which player you want, as well as which slot.
    *Example: .pick_player arco 4*
**.drop_player** - Can also be done with '.pick_player drop [slot]', drops the player in the specified slot, replacing them with 'Not Picked'.
**.leaderboard** - Displays the current leaderboard of points
    """
    help_message2 = """
**__NEWS/STATS COMMANDS__**

*Note: RLPC News tracks an ELO ranking of each team based on each team's wins and losses and the strength of the opposing team. This is used for predicting scores and generating rankings*

**.predict** - Predicts the score of a hypothetical match between two teams, based on the teams' current ELO. Include the league (major, AAA, etc), two teams, and number of games.
    *Example: .predict major allusion evolution 5*
**.rankteams** - Ranks all the teams in a league based on their current ELO.
    *Example: .rankteams major*
    
**__LINKS__**

**rlpclink** - Shows an invite link for the RLPC Server
**rlpcnewslink** - Shows an invite link for the RLPC News Server
**reddit** - Links to the RLPC Reddit Page, where RLPC News articles are posted
**apply** - Shows a link to apply to become a part of RLPC News
    """
    
    await message_author.send(help_message1)
    await message_author.send(help_message2)

for filename in os.listdir('./cogs'):
    if filename.endswith('.py'):
        client.load_extension(f'cogs.{filename[:-3]}')

client.run('NjM1MTg4NTc2NDQ2ODQwODU4.XhtcHw.n1k7IKXxDbrt1sbQE4wzCaqb7xc')
