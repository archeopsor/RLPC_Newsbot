import os
from random import choice

import discord
from discord.ext import commands
from discord.ext.commands import has_permissions

from rlpc import elo

from tools.mongo import Session
from tools.sheet import Sheet

from settings import prefix, power_rankings_sheet

client = commands.Bot(command_prefix = prefix)
client.remove_command('help')

pr_sheet = Sheet(power_rankings_sheet)

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
@has_permissions(manage_channels=True)
async def alerts(ctx):
    async with ctx.typing():
        with Session().admin as session:
            channels = session['channels']['upset_alerts']
        
        if isinstance(ctx.channel, discord.channel.DMChannel): # I don't really think this is necessary
            pass

        if ctx.channel.id in channels:
            with Session().admin as session:
                session.find_one_and_update({'purpose': 'channels'}, {'$pull': {'channels.upset_alerts': ctx.channel.id}})
            return await ctx.send("This channel will no longer receive alerts.")
        else:
            with Session().admin as session:
                session.find_one_and_update({'purpose': 'channels'}, {'$push': {'channels.upset_alerts': ctx.channel.id}})
            return await ctx.send("This channel will now receive alerts!")
    return

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
        records = pr_sheet.to_df("Team Wins!A1:AE17")
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
            ratings = elo.recall_data(league).set_index("Team")
            team1_rating = int(ratings.loc[team1, 'elo'])
            team2_rating = int(ratings.loc[team2, 'elo'])
            
        upset = False
        if criteria == "record" and team2_wins - team1_wins >= threshold:
            upset = True
        elif criteria == "rating" and team2_rating - team1_rating >= threshold:
            upset = True
        
        # Send to #game-scores channel
        gamescores_channel = client.get_channel(836784966221430805)
        await gamescores_channel.send(f'**{league} result**\n{team1} {team1_record}: {team1_score}\n{team2} {team2_record}: {team2_score}')
        
        
        descriptors = ["have taken down","have defeated","beat","were victorious over", "thwarted", "have upset", "have overpowered", "got the better of", "overcame", "triumphed over"]
        
        if upset:
            alert_message = f"""**UPSET ALERT**
{team1} {team1_record} {choice(descriptors)} {team2} {team2_record} with a score of {team1_score} - {team2_score}
            """
            # Send the message out to subscribed channels
            await client.wait_until_ready()
            with Session().admin as session:
                send_to = session.find_one({'purpose': 'channels'})['upset_alerts']
            for channel in send_to:
                try:
                     channel = client.get_channel(channel[0])
                except:
                    continue
                new_message = alert_message
                for role in channel.guild.roles:
                    if role.name.casefold() == "upset alerts":
                        new_message += f'\n{channel.guild.get_role(role.id).mention}'
                await channel.send(new_message)
                
    await client.process_commands(message)


for filename in os.listdir('./cogs'):
    if filename.endswith('.py'):
        client.load_extension(f'cogs.{filename[:-3]}')

try:
    from passwords import BOT_TOKEN
except:
    BOT_TOKEN = os.environ.get('BOT_TOKEN')

client.run(BOT_TOKEN)