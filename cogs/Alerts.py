from discord.ext import commands
from database import engine, select
import RLPC_ELO as elo
import Google_Sheets as sheet
from random import choice
import pandas as pd

class Alerts(commands.Cog):
    
    def __init__(self,client):
        self.client = client
        
    @commands.command(aliases=("alert","subscribe",))
    async def alerts(self, ctx):
        async with ctx.typing():
            channels = select("select id from alerts_channels")['id'].to_list()
            if ctx.channel.id in channels:
                engine.execute(f"delete from alerts_channels where id={ctx.channel.id}")
                await ctx.send("This channel will no longer receive alerts.")
                return
            else:
                engine.execute(f"insert into alerts_channels (id) values ({ctx.channel.id})")
                await ctx.send("This channel will now receive alerts!")
                return
            
    @commands.Cog.listener()
    async def on_message(self, message):
        client = self.client
        channels = {501552099373350926: "Major", 598237603254239238: "Major", 598237794762227713: "AAA", 598237830824591490: "AA", 598237861837537304: "A"}
        if message.channel.id in list(channels):
                        
            # Parse messages
            league = channels[message.channel.id]
            
            if 'forfeit' in message.content:
                return
            
            game = message.content.split("\n")[2:4]
            team1 = game[0].split(": ")[0]
            team1_score = int(game[0][-1])
            team2 = game[1].split(": ")[0]
            team2_score = int(game[1][-1])
            
            records = sheet.gsheet2df(sheet.get_google_sheet("1Tlc_TgGMrY5aClFF-Pb5xvtKrJ1Hn2PJOLy2fUDDdFI","Team Wins!A1:O17"))
            if league == "Major":
                records = records.iloc[:,0:3]
            elif league == "AAA":
                records = records.iloc[:,4:7]
            elif league == "AA":
                records = records.iloc[:,8:11]
            elif league == "A":
                records = records.iloc[:,12:15]
            records = records.set_index(f"{league} Teams")
            team1_record = f"({records.loc[team1, 'Wins']}-{records.loc[team1, 'Losses']})"
            team2_record = f"({records.loc[team2, 'Wins']}-{records.loc[team2, 'Losses']})"
            
            ratings = elo.recall_data(league).set_index("teams")
            team1_rating = int(ratings.loc[team1, 'ELO'])
            team2_rating = int(ratings.loc[team2, 'ELO'])
            
            descriptors = ["have taken down","have defeated","beat","were victorious over", "thwarted", "have upset", "have overpowered", "got the better of", "overcame", "triumphed over"]
            
            if team2_rating - team1_rating > 60:
                message = f"""**UPSET ALERT**
{team1} {team1_record} {choice(descriptors)} {team2} {team2_record} with a score of {team1_score} - {team2_score}
                """
                
                # Send the message out to subscribed channels
                await client.wait_until_ready()
                channels = select("alerts_channels")
                for channel in channels:
                    channel = client.get_channel(channel[0])
                    await channel.send(message)
        
def setup(client):
    client.add_cog(Alerts(client))