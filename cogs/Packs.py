from discord.ext import commands
import discord
from discord.ext.commands.context import Context
import numpy as np
import os
import sqlite3
from sqlalchemy import create_engine
import pandas as pd

from settings import prefix
client = commands.Bot(command_prefix = prefix)
engine = create_engine("sqlite:///cards.db")
path = './Image_templates/Player Cards'

class Packs(commands.Cog):
    
    def __init__(self, client):
        self.client = client
        
    @commands.command(aliases=("card",))
    async def random_card(self, ctx: Context):
        file = discord.File(path+'/'+np.random.choice(os.listdir(path)))
        await ctx.send(file=file)
        
    @commands.command(aliases=("open",))
    async def open_pack(self, ctx: Context):
        async with ctx.typing():
            # Single card pack
            with engine.connect() as conn, conn.begin():
                data = pd.read_sql_table('cards', conn).set_index("player")    
            

def setup(client):
    client.add_cog(Packs(client))