from rlpc.stats import StatsHandler
from fantasy_infrastructure import FantasyHandler
import os
from random import choice
from rlpc.players import Identifier, Players

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

from rlpc.elo import EloHandler

from tools.mongo import Session
from tools.sheet import Sheet

from settings import prefix, power_rankings_sheet, sheet_p4, sheet_indy, forecast_sheet, gdstats_sheet

client = commands.Bot(command_prefix = prefix)
client.remove_command('help')

# Instances of util and helper classes so only one exists for the entire bot
session = Session()
p4sheet = Sheet(sheet_p4)
fc_sheet = Sheet(forecast_sheet)
indysheet = Sheet(sheet_indy)
gdsheet = Sheet(gdstats_sheet)
pr_sheet = Sheet(power_rankings_sheet)
identifier = Identifier(session, p4sheet)
elo = EloHandler(session, identifier)
fantasy_handler = FantasyHandler(session)
players = Players(session, p4sheet)
stats = StatsHandler(session, p4sheet, indysheet, pr_sheet)

@client.event
async def on_ready():
    print('Logged in as')
    print(f"Username:  {client.user.name}")
    print(f"User ID:  {client.user.id}")
    print('---------------------------------')
    await client.change_presence(activity=discord.Game(f'{prefix}help for commands'))

@client.command()
async def ping(ctx: Context):
    await ctx.send(f'Pong! {round(client.latency * 1000)}ms')
    
@client.command(aliases=("alert","subscribe",))
@has_permissions(manage_channels=True)
async def alerts(ctx: Context):
    async with ctx.typing():
        with Session().admin as session:
            channels = session.find_one({'purpose': 'channels'})['channels']['upset_alerts']
        
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
async def alerts_error(ctx: Context, error):
    if isinstance(error, commands.CheckFailure):
        await ctx.send("You don't have admin perms for this server.")

@client.event
async def on_message(message: discord.Message):
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
            team1_rating = elo.get_elo(team1)
            team2_rating = elo.get_elo(team2)
            
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
            alert_message = f"""**UPSET ALERT**\n{team1} {team1_record} {choice(descriptors)} {team2} {team2_record} with a score of {team1_score} - {team2_score}"""
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


# Load cogs
cogs = []
cogs.append(ELO(client, session=session, identifier=identifier, fc_sheet=fc_sheet, elo=elo))
cogs.append(Fantasy(client, session=session, fantasy=fantasy_handler, p4sheet=p4sheet))
cogs.append(Help(client))
cogs.append(Links(client))
cogs.append(Reddit(client))
cogs.append(Stats(client, session=session, p4sheet=p4sheet, indysheet=indysheet, gdsheet=gdsheet, identifier=identifier, players=players, stats=stats))
for cog in cogs:
    client.add_cog(cog)

@client.command()
async def load(ctx: Context, extension: str):
    for cog in cogs:
        if cog.__name__ == extension:
            client.add_cog(cog)
            return await ctx.send(f"{extension} loaded")
    return await ctx.send(f"Couldn't find an extension named {extension}")
    
@client.command()
async def reload(ctx: Context, extension: str):
    cog = client.get_cog(extension)
    if cog == None:
        return await ctx.send(f"Couldn't find an extension named {extension}")
    else:
        client.remove_cog(cog)
        client.add_cog(cog)
        return await ctx.send(f"{extension} reloaded")
    
@client.command()
async def unload(ctx: Context, extension: str):
    client.remove_cog(extension)
    await ctx.send(f"{extension} unloaded")

try:
    from passwords import BOT_TOKEN
except:
    BOT_TOKEN = os.environ.get('BOT_TOKEN')

client.run(BOT_TOKEN)