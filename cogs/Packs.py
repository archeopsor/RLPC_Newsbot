from discord.ext import commands
import discord
import numpy as np
import os
import sqlite3
from sqlalchemy import create_engine

prefix = '$'
client = commands.Bot(command_prefix = prefix)
engine = create_engine("sqlite:///cards.db")
connection = sqlite3.connect("cards.db")
cursor = connection.cursor()
path = './Image_templates/Player Cards'

class Packs(commands.Cog):
    
    def __init__(self,client):
        self.client = client
        
    @commands.command(aliases=("card",))
    async def random_card(self, ctx):
        file = discord.File(path+'/'+np.random.choice(os.listdir(path)))
        await ctx.send(file=file)
        
    @commands.command()
    async def open_pack(self, ctx):
        await with ctx.typing():
            # Single card pack
            pass
            

def setup(client):
    client.add_cog(Packs(client))
    
    
# with closing(sqlite3.connect("aquarium.db")) as connection:
#     with closing(connection.cursor()) as cursor:
#         rows = cursor.execute("SELECT 1").fetchall()
#         print(rows)