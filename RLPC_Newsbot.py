import discord
import os
from discord.ext import commands
from datetime import datetime

prefix = '$'
client = commands.Bot(command_prefix = prefix)
client.remove_command('help')

@client.event
async def on_ready():
    print('Bot is ready.')
    await client.change_presence(activity=discord.Game(f'{prefix}help for commands'))

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

@client.command(pass_context = True)
async def help(ctx,specified="none"):
    message_author = ctx.message.author
    
    specified = specified.casefold()
    
    fantasy_help_message = f"""
**Command: fantasy_help**
*Aliases: fantasy_help, fantasy, fhelp, f_help*

Displays a help message with rules and commands for the RLPC Fantasy League
    """
    new_account_message = """
**Command: new_fantasy_player**
*Aliases: createaccount, create_account, newplayer, new_player, newaccount, new_account, add_fantasy_player*

Creates a fantasy account linked to your discord username. If you change your username, message arco to regain access to your account.
In addition to the command, you must also include the league you play in (major, aaa, aa, a, or none) to help prevent match fixing.

Usage: {prefix}createaccount [league]
    """
    team_message = f"""
**Command: team**
*Aliases: show, showteam*

Displays a player's current fantasy team. You must also include the discord username (case sensitive, without discriminator) of the player.
Leave [username] blank if you want to display your own team.

Usage: {prefix}team [username]
    """
    info_message = f"""
**Command: playerinfo**
*Aliases: info, player, player_info*

Display's a player's mmr, team, league, and salary/fantasy value. Make sure the player's name is spelled the same as on the spreadsheet (case sensitive)

Usage: {prefix}info [player]
    """
    pick_message = f"""
**Command: pick_player**
*Aliases: pick, pick_player, pickplayer, addplayer, add_player*

Adds a player to your fantasy team. Include the player's name (as spelled on the sheet, case sensitive) and which of the five slots you'd like to use.
Use ~team to see which players are already in each slot

Usage: {prefix}pick [player] [slot]
    """
    drop_message = f"""
**Command: drop_player**
*Aliases: drop, dropplayer, drop_player, removeplayer, remove_player*

Drops a player from your team, replacing them with "Not Picked". You must specify which slot you'd like to empty.

Usage: {prefix}drop [slot]
    """
    lb_message = f"""
**Command: leaderboard**
*Aliases: lb, standings*

Displays the current fantasy leaderboard.
    """
    search_message = f"""
**Command: search**
*Aliases: searchplayers*

Finds the five players that best meet the specified requirements. Can specify a minimum salary, maximum salary, team, league, and name. 
Input the arguments as two words, with one word to specify which argument you're using (ex: min: or team:) and then the desired argument (ex: 100 or Bulls)
You don't need to use every argument, just doing {prefix}search will display the first five players by alphabetical order.

Usage: {prefix}search [type] [argument]

*[type] can be min, max, team, league, name, or strictness*
*[argument] is where you put the search parameter*
*You can use anywhere from 0 to 6 of the type/argument pairs*
    """
    predict_message = f"""
**Command: predict**
*Aliases: predict, scorepredict, predictscore, score_predict, predict_score*

Uses an ELO system to give every team a rating, and predicts the score of a hypothetical matchup between two teams.
Include the league and two teams. You may also include how many games would be played, or leave [# of games] blank for the probability out of 100 that each team wins.

Usage: {prefix}predict [league] [team 1] [team 2] [# of games]
    """
    rank_message = f"""
**Command: rank**
*Aliases: rankteams*

Uses an ELO system to give every team a rating, and displays a list ranking each team in a league. Include the league you want to rank.

Usage: {prefix}rank [league]
    """
    links_message = f"""
Different links can be found using this bot.

**{prefix}rlpc** shows a link to the RLPC discord server
**{prefix}rlpcnews** shows a link to the RLPC News discord server, with all sorts of news/power rankings and other things
**{prefix}reddit** shows a link to the RLPC Subreddit, where news articles are posted
**{prefix}apply** shows a link to apply to become a part of RLPC News!
    """
    help_message1 = f"""
Hello! This is a bot primarily meant to run a fantasy league for RLPC, but it has some other functions as well!
If you have any questions, notice any issues or bugs, or have any suggestions, please feel free to contact <@160901864072806401>

**__FANTASY COMMANDS__**

**{prefix}fantasy_help** - Repeats much of this information, also includes important information about the fantasy league such as rules
**{prefix}new_fantasy_player** - Creates a fantasy team linked to your discord account. Please include the league you play in, or 'none'.
    *Example: {prefix}new_fantasy_player major*
**{prefix}team** - Shows the current fantasy team of any fantasy player. "{prefix}team" will display your own team, although you can include any discord account name (Don't use nicknames')
    *Example: {prefix}team arco
**{prefix}info** - Gives important information about a player, such as their salary and a variety of stats.
    *Example: {prefix}info arco*
**{prefix}pick_player** - Adds a player to your fantasy team, in one of 5 player slots. Please specify which player you want, as well as which slot.
    *Example: {prefix}pick_player arco 4*
**{prefix}drop_player** - Can also be done with '{prefix}pick_player drop [slot]', drops the player in the specified slot, replacing them with 'Not Picked'.
**{prefix}leaderboard** - Displays the current leaderboard of points
**{prefix}search** - Finds the five players that best meet the specified requirements. Can specify a minimum salary, maximum salary, team, league, and name, although you can use as many or as few of these parameters as you want.
    *Example: {prefix}search name: arco min: 100 max: 200 team: FA league: AA*
    """
    help_message2 = f"""
**__NEWS/STATS COMMANDS__**

*Note: RLPC News tracks an ELO ranking of each team based on each team's wins and losses and the strength of the opposing team. This is used for predicting scores and generating rankings*

**{prefix}predict** - Predicts the score of a hypothetical match between two teams, based on the teams' current ELO. Include the league (major, AAA, etc), two teams, and number of games.
    *Example: {prefix}predict major allusion evolution 5*
**{prefix}rank** - Ranks all the teams in a league based on their current ELO.
    *Example: {prefix}rank major*
**{prefix}stats** - Displays a player's stats. You can choose a specific stat, or display all stats.
    *Example: {prefix}stats arco ppg
    
**__REDDIT COMMANDS__**

**{prefix}top** - Displays the top x posts of all time on the RLPC subreddit. Use {prefix}top [#] to return a specified number of posts.
**{prefix}hot** - Displays the x most popular recent posts on the RLPC subreddit. Use {prefix}hot [#] to return a specified number of posts.
**{prefix}list_new** - Displays the x newest posts on the RLPC subreddit. Use {prefix}list_new [#] to return a specified number of posts.
**{prefix}get** - Gets the text of a reddit post from one of the previous three commands. Use the format {prefix}get [type] [#] where type is "top", "hot", or "new" and # is where it is on the list
    *Example: {prefix}get top 3
**{prefix}newest** - Same function as {prefix}get new 1, displays the most recent post.
    
**__LINKS__**

**{prefix}rlpclink** - Shows an invite link for the RLPC Server
**{prefix}rlpcnewslink** - Shows an invite link for the RLPC News Server
**{prefix}reddit** - Links to the RLPC Reddit Page, where RLPC News articles are posted
**{prefix}apply** - Shows a link to apply to become a part of RLPC News
    """
    if specified == "none":
        await message_author.send(help_message1)
        await message_author.send(help_message2)
    elif specified in ["fantasy_help","fantasy","fhelp","f_help"]:
        await message_author.send(fantasy_help_message)
    elif specified in ["new_fantasy_player","createaccount","create_account","newplayer", "new_player","newaccount","new_account","add_fantasy_player"]:
        await message_author.send(new_account_message)
    elif specified in ["show","team","showteam"]:
        await message_author.send(team_message)
    elif specified in ["info","player","playerinfo","player_info"]:
        await message_author.send(info_message)
    elif specified in ["pick","pick_player","pickplayer","addplayer","add_player"]:
        await message_author.send(pick_message)
    elif specified in ["drop","dropplayer","drop_player","removeplayer","remove_player"]:
        await message_author.send(drop_message)
    elif specified in ["leaderboard","lb","standings","generate_leaderboard"]:
        await message_author.send(lb_message)
    elif specified in ["search","searchplayers","searchplayer"]:
        await message_author.send(search_message)
    elif specified in ["predict","scorepredict","predictscore","score_predict","predict_score"]:
        await message_author.send(predict_message)
    elif specified in ["rankteams","rank"]:
        await message_author.send(rank_message)
    elif specified in ["links","rlpc","rlpclink","rlpcnews","rlpcnewslink","reddit","redditlink","apply","applylink"]:
        await message_author.send(links_message)
    else:
        await ctx.send(f"'{specified} doesn't seem to be a valid command'")
        
    await ctx.send("A DM has been sent! If you have any further questions, please DM Arco.")

for filename in os.listdir('./cogs'):
    if filename.endswith('.py'):
        client.load_extension(f'cogs.{filename[:-3]}')

from passwords import BOT_TOKEN
client.run(BOT_TOKEN) #Replace with BOT_TOKEN