import os
from random import choice

import discord
from discord.ext import commands
from discord.ext.commands import has_permissions

from rlpc import elo

from tools.database import engine, select
from tools import sheet

from settings import prefix
client = commands.Bot(command_prefix = prefix)
client.remove_command('help')

@client.event
async def on_ready():
    print('Logged in as')
    print(f"Username:  {client.user.name}")
    print(f"User ID:  {client.user.id}")
    print('---------------------------------')
    await client.change_presence(activity=discord.Game(f'{prefix}help for commands'))

@client.command()
async def ping(ctx):
    await ctx.send(f'Pong! {round(client.latency * 1000)}ms')
    
@client.command()
async def load(ctx, extension):
    client.load_extension(f'cogs.{extension}')
    await ctx.send(f"{extension} loaded")
    
@client.command()
async def reload(ctx, extension):
    client.unload_extension(f'cogs.{extension}')
    client.load_extension(f'cogs.{extension}')
    await ctx.send(f"{extension} reloaded")
    
@client.command()
async def unload(ctx, extension):
    client.unload_extension(f'cogs.{extension}')
    await ctx.send(f"{extension} unloaded")
    
@client.command(aliases=("alert","subscribe",))
@has_permissions(administrator=True)
async def alerts(ctx):
    async with ctx.typing():
        channels = select("select id from alerts_channels")['id'].to_list()
        
        if isinstance(ctx.channel, discord.channel.DMChannel):
            pass
        
        if ctx.channel.id in channels:
            engine.execute(f"delete from alerts_channels where id={ctx.channel.id}")
            await ctx.send("This channel will no longer receive alerts.")
            return "finished"
        else:
            engine.execute(f"insert into alerts_channels (id) values ({ctx.channel.id})")
            await ctx.send("This channel will now receive alerts!")
            return "finished"
    return "finished"

@alerts.error
async def alerts_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        await ctx.send("You don't have admin perms for this server.")

@client.event
async def on_message(message):
    channels = {598237603254239238: "Major", 598237794762227713: "AAA", 598237830824591490: "AA", 598237861837537304: "A", 715549072936796180: "Indy", 715551351236722708: "Mav", 757714221759987792: "Ren", 757719107041755286: "Pal"}
    if int(message.channel.id) in list(channels):
        
        criteria, threshold = ("record", 4) # Criteria is either 'record' or 'rating', followed by the threshold for an upset
        
        print("Found channel")
        # Parse messages
        league = channels[message.channel.id]
        
        if 'forfeit' in message.content:
            return
        
        print("Splitting content")
        game = message.content.split("\n")[2:4]
        team1 = game[0].split(": ")[0]
        team1_score = int(game[0][-1])
        team2 = game[1].split(": ")[0]
        team2_score = int(game[1][-1])
        
        print("Getting records")
        # This is needed to put records in alert_message, even if using rating for the criteria
        records = sheet.gsheet2df(sheet.get_google_sheet("1Tlc_TgGMrY5aClFF-Pb5xvtKrJ1Hn2PJOLy2fUDDdFI","Team Wins!A1:AE17"))
        if league == "Major":
            records = records.iloc[:,0:3]
        elif league == "AAA":
            records = records.iloc[:,4:7]
        elif league == "AA":
            records = records.iloc[:,8:11]
        elif league == "A":
            records = records.iloc[:,12:15]
        elif league == "Indy":
            records = records.iloc[:,16:19]
        elif league == "Mav":
            records = records.iloc[:,20:23]
        elif league == "Ren":
            records = records.iloc[:,24:27]
        elif league == "Pal":
            records = records.iloc[:,28:31]
        records = records.set_index(f"{league} Teams")
        team1_record = f"({records.loc[team1, 'Wins']}-{records.loc[team1, 'Losses']})"
        team2_record = f"({records.loc[team2, 'Wins']}-{records.loc[team2, 'Losses']})"
        team1_wins = int(records.loc[team1, 'Wins'])
        team2_wins = int(records.loc[team2, 'Wins'])
        
        if criteria == "rating":
            print("Getting ratings")
            ratings = elo.recall_data(league).set_index("Team")
            team1_rating = int(ratings.loc[team1, 'elo'])
            team2_rating = int(ratings.loc[team2, 'elo'])
            
        upset = False
        if criteria == "record" and team2_wins - team1_wins >= threshold:
            upset = True
        elif criteria == "rating" and team2_rating - team1_rating >= threshold:
            upset = True
        
        descriptors = ["have taken down","have defeated","beat","were victorious over", "thwarted", "have upset", "have overpowered", "got the better of", "overcame", "triumphed over"]
        
        print("Reached if True")
        if upset:
            alert_message = f"""**UPSET ALERT**
{team1} {team1_record} {choice(descriptors)} {team2} {team2_record} with a score of {team1_score} - {team2_score}
            """
            # Send the message out to subscribed channels
            print("Waiting until ready")
            await client.wait_until_ready()
            send_to = select("alerts_channels").values
            print("Sending Messages")
            for channel in send_to:
                try:
                     channel = client.get_channel(channel[0])
                except:
                    continue
                new_message = alert_message
                print(channel)
                for role in channel.guild.roles:
                    if role.name.casefold() == "upset alerts":
                        new_message += f'\n{channel.guild.get_role(role.id).mention}'
                await channel.send(new_message)
                
    await client.process_commands(message)

@client.command(pass_context = True)
async def help(ctx,specified="none"):
    message_author = ctx.message.author
    
    specified = specified.casefold()
    
    fantasy_help_message = """
**Command: fantasy**

Displays a help message with rules and commands for the RLPC Fantasy League
    """
    new_account_message = """
**Command: new**

Creates a fantasy account linked to your discord username. If you change your username, message arco to regain access to your account.
In addition to the command, you must also include the league you play in (major, aaa, aa, a, or none) to help prevent match fixing.

Usage: {prefix}new
    """
    team_message = f"""
**Command: team**

Displays a player's current fantasy team. You must also include the discord username (case sensitive, without discriminator) of the player.
Leave [username] blank if you want to display your own team.

Usage: {prefix}team [username]
    """
    info_message = f"""
**Command: info**

Display's a player's mmr, team, league, and salary/fantasy value. Make sure the player's name is spelled the same as on the spreadsheet

Usage: {prefix}info [player]
    """
    pick_message = f"""
**Command: pick**

Adds a player to your fantasy team. Include the player's name (as spelled on the sheet) and which of the five slots you'd like to replace if your team is already full.
Use {prefix}team to see which players are already in each slot

Usage: {prefix}pick [player] [slot (optional)]
    """
    drop_message = f"""
**Command: drop**

Drops a player from your team, replacing them with "Not Picked". You must specify which slot you'd like to empty. Use $team to show which player is in each slot.

Usage: {prefix}drop [slot]
    """
    lb_message = """
**Command: lb**

Displays the current fantasy leaderboard.
    """
    search_message = f"""
**Command: search**

Finds the five players that best meet the specified requirements. Can specify a minimum salary, maximum salary, team, league, and name. 
Input the arguments as two words, with one word to specify which argument you're using (ex: min: or team:) and then the desired argument (ex: 100 or Bulls)
You don't need to use every argument, just doing {prefix}search will display the first five players by alphabetical order.

Usage: {prefix}search [type] [argument]

*[type] can be min, max, team, league, name, or strictness*
*[argument] is where you put the search parameter*
*You can use anywhere from 0 to 6 of the type/argument pairs*

Example: {prefix}search name: arco league: Major team: Hawks
    """
    predict_message = f"""
**Command: predict**

Uses an ELO system to give every team a rating, and predicts the score of a hypothetical matchup between two teams.
Include the league and two teams. You may also include how many games would be played, or leave [# of games] blank for the probability out of 100 that each team wins.

Usage: {prefix}predict [team 1] [team 2] [# of games (optional)]
    """
    rank_message = f"""
**Command: rank**

Uses an ELO system to give every team a rating, and displays a list ranking each team in a league. Include the league you want to rank.

Usage: {prefix}rank [league]
    """
    links_message = f"""
Different links can be found using this bot.

**{prefix}rlpc** shows a link to the RLPC discord server
**{prefix}rlpcnews** shows a link to the RLPC News discord server, with all sorts of news/power rankings and other things
**{prefix}reddit** shows a link to the RLPC Subreddit, where news articles are posted
**{prefix}apply** shows a link to apply to become a part of RLPC News!
**{prefix}invite** shows a link to invite the RLPC Newsbot to your own server!
    """
    players_message = f"""
**Command: players**

Shows a leaderboard of players based on the fantasy points they have earned since the start of the season.

Usage: {prefix}players [league (optional)]
    """
    top_message = f"""
**Command: top**

Displays the top x posts of all time on the RLPC subreddit.

Usage: {prefix}top [# of posts (optional)]
    """
    hot_message = f"""
**Command: hot**

Displays the x most popular recent posts on the RLPC subreddit.

Usage: {prefix}hot [# of posts (optional)]
    """
    listnew_message = f"""
**Command: listnew**

Displays the x newest posts on the RLPC subreddit.

Usage: {prefix}top [# of posts (optional)]
    """
    get_message = f"""
**Command: get**

Gets the text of a reddit post from one of the other three reddit commands. Use the format {prefix}get [type] [#] where type is "top", "hot", or "new" and # is where it is on the list

Usage: {prefix}get [type] [#]
    """
    newest_message = """
**Command: newest**

Displays the newest post on the RLPC subreddit.
    """
    pr_message = f"""
**Command: pr**

Gets the most recent power rankings for any given league. These are made by the power ranking team, rather than a computer.

Usage: {prefix}pr [league]
    """
    stats_message = f"""
**Command: stats**

Displays a player's stats from the RLPC Spreadsheet. You can choose a specific stat, or display all stats.

Usage: {prefix}stats [player] [stat (optional)]
    """
    forecast_message = f"""
**Command: forecast**

Shows an MCMC simulation-based forecast for any given league or team, and links to the forecast spreadsheet.

Usage: {prefix}forecast [league] [team (optional)]
    """
    help_message1 = f"""
Hello! This is a bot primarily meant to run a fantasy league for RLPC, but it has some other functions as well!
If you have any questions, notice any issues or bugs, or have any suggestions, please feel free to contact <@160901864072806401>

**__FANTASY COMMANDS__**

**{prefix}fantasy** - Repeats much of this information, also includes important information about the fantasy league such as rules
**{prefix}new** - Creates a fantasy team linked to your discord account.
    *Example: {prefix}new*
**{prefix}team** - Shows the current fantasy team of any fantasy player. "{prefix}team" will display your own team, although you can include any discord account name (Don't use nicknames')
    *Example: {prefix}team arco
**{prefix}info** - Gives important information about a player, such as their salary and a variety of stats.
    *Example: {prefix}info arco*
**{prefix}pick** - Adds a player to your fantasy team, in one of 5 player slots. Please specify which player you want, as well as which slot.
    *Example: {prefix}pick arco 4*
**{prefix}drop** - Can also be done with '{prefix}pick drop [slot]', drops the player in the specified slot, replacing them with 'Not Picked'.
**{prefix}lb** - Displays the current leaderboard of points
**{prefix}search** - Finds the five players that best meet the specified requirements. Can specify a minimum salary, maximum salary, team, league, and name, although you can use as many or as few of these parameters as you want.
    *Example: {prefix}search name: arco min: 100 max: 200 team: FA league: AA*
**{prefix}players** - Shows a leaderboard of players based on the fantasy points they have earned since the start of the season.
    """
    help_message2 = f"""
**__NEWS/STATS COMMANDS__**

*Note: RLPC News tracks an ELO ranking of each team based on each team's wins and losses and the strength of the opposing team. This is used for predicting scores and generating rankings*

**{prefix}predict** - Predicts the score of a hypothetical match between two teams, based on the teams' current ELO. Include two teams and an optional number of games.
    *Example: {prefix}predict hawks eagles 5*
**{prefix}rank** - Ranks all the teams in a league based on their current ELO.
    *Example: {prefix}rank major*
**{prefix}pr** - Gets the most recent power rankings for any given league. These are made by the power ranking team, rather than a computer.
**{prefix}stats** - Displays a player's stats. You can choose a specific stat, or display all stats.
    *Example: {prefix}stats arco ppg
**{prefix}forecast** - Shows an MCMC simulation-based forecast for any given league or team, and links to the forecast spreadsheet.
    *Example: {prefix}forecast major Hawks*
    
**__REDDIT COMMANDS__**

**{prefix}top** - Displays the top x posts of all time on the RLPC subreddit. Use {prefix}top [#] to return a specified number of posts.
**{prefix}hot** - Displays the x most popular recent posts on the RLPC subreddit. Use {prefix}hot [#] to return a specified number of posts.
**{prefix}listnew** - Displays the x newest posts on the RLPC subreddit. Use {prefix}list_new [#] to return a specified number of posts.
**{prefix}get** - Gets the text of a reddit post from one of the previous three commands. Use the format {prefix}get [type] [#] where type is "top", "hot", or "new" and # is where it is on the list
    *Example: {prefix}get top 3*
**{prefix}newest** - Same function as {prefix}get new 1, displays the most recent post.
    
**__LINKS__**

**{prefix}rlpc** - Shows an invite link for the RLPC Server
**{prefix}rlpcnews** - Shows an invite link for the RLPC News Server
**{prefix}reddit** - Links to the RLPC Reddit Page, where RLPC News articles are posted
**{prefix}apply** - Shows a link to apply to become a part of RLPC News
**{prefix}invite** - Shows a link to invite the RLPC Newsbot to a server
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
    elif specified in ["players", 'playerlb']:
        await message_author.send(players_message)
    elif specified in ['top', 'listtop', 'list_top']:
        await message_author.send(top_message)
    elif specified in ['hot', 'listhot', 'list_hot']:
        await message_author.send(hot_message)
    elif specified in ['listnew', 'list_new']:
        await message_author.send(listnew_message)
    elif specified in ['get', 'getpost']:
        await message_author.send(get_message)
    elif specified in ['newest']:
        await message_author.send(newest_message)
    elif specified in ['pr', 'powerrankings', 'power_rankings']:
        await message_author.send(pr_message)
    elif specified in ['stats', 'getstats', 'stat']:
        await message_author.send(stats_message)
    elif specified in ['forecast']:
        await message_author.send(forecast_message)
    else:
        await ctx.send(f"'{specified} doesn't seem to be a valid command'")
        
    await ctx.send("A DM has been sent! If you have any further questions, please DM Arco.")

for filename in os.listdir('./cogs'):
    if filename.endswith('.py'):
        client.load_extension(f'cogs.{filename[:-3]}')

try:
    from passwords import BOT_TOKEN
except:
    BOT_TOKEN = os.environ.get('BOT_TOKEN')

client.run(BOT_TOKEN)