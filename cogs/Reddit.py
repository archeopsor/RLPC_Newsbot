from discord.ext import commands
import discord

from tools import reddit

from settings import prefix
client = commands.Bot(command_prefix = prefix)

class Reddit(commands.Cog):
    
    def __init__(self,client):
        self.client = client
        
    @commands.command(aliases=("top","listtop","listop",))
    async def list_top(self, ctx, limit=5):
        async with ctx.typing():
            if limit > 10:
                limit = 10
            posts = reddit.list_top(limit)
            for post in range(len(posts[0])):
                embed = discord.Embed(title=f'{post+1}. {posts[0][post]}', color=0xff8000)
                embed.add_field(name="Author:", value=posts[1][post], inline=False)
                embed.add_field(name="Upvotes:", value=posts[2][post], inline=False)
                embed.add_field(name="Downvotes:", value=posts[3][post], inline=False)
                embed.add_field(name="Comments:", value=posts[4][post], inline=False)
                await ctx.send(embed=embed)
                
        await ctx.send(f"Use '{prefix}get top [number]' to get the contents of any specific post")
                
    @commands.command(aliases=("hot","listhot",))
    async def list_hot(self, ctx, limit=5):
        async with ctx.typing():
            if limit > 10:
                limit = 10
            posts = reddit.list_hot(limit)
            for post in range(len(posts[0])):
                embed = discord.Embed(title=f'{post+1}. {posts[0][post]}', color=0xff8000)
                embed.add_field(name="Author:", value=posts[1][post], inline=False)
                embed.add_field(name="Upvotes:", value=posts[2][post], inline=False)
                embed.add_field(name="Downvotes:", value=posts[3][post], inline=False)
                embed.add_field(name="Comments:", value=posts[4][post], inline=False)
                await ctx.send(embed=embed)
                
        await ctx.send(f"Use '{prefix}get hot [number]' to get the contents of any specific post")
                
    @commands.command(aliases=("listnew",))
    async def list_new(self, ctx, limit=5):
        async with ctx.typing():
            if limit > 10:
                limit = 10
            posts = reddit.list_new(limit)
            for post in range(len(posts[0])):
                embed = discord.Embed(title=f'{post+1}. {posts[0][post]}', color=0xff8000)
                embed.add_field(name="Author:", value=posts[1][post], inline=False)
                embed.add_field(name="Upvotes:", value=posts[2][post], inline=False)
                embed.add_field(name="Downvotes:", value=posts[3][post], inline=False)
                embed.add_field(name="Comments:", value=posts[4][post], inline=False)
                await ctx.send(embed=embed)
                
        await ctx.send(f"Use '{prefix}get new [number]' to get the contents of any specific post")
    
    @commands.command(aliases=("get",))
    async def get_post(self, ctx, type, number):
        number = int(number)
        if number < 1:
            await ctx.send("Please choose an integer number greater than 1.")
        else: 
            pass
        async with ctx.typing():
            post = reddit.get_post(type, number)
        await ctx.send(f'**Title: {post[0]}, author: {post[1]}, score: {post[2]-post[3]}**')
        if len(post[4]) > 2000:
            await ctx.send(f'{post[4][0:1000]}... \n\n *This post is too long for discord, see the full post at: https://www.reddit.com{post[5]}*')
        await ctx.send(post[4])
        
    @commands.command(aliases=("newpost", "getnew", "newest",))
    async def get_newest(self, ctx):
        async with ctx.typing():
            post = reddit.get_post("new", 1)
        await ctx.send(f'**Title: {post[0]}, author: {post[1]}, score: {post[2]-post[3]}**')
        if len(post[4]) > 2000:
            await ctx.send(f'{post[4][0:1000]}... \n\n *This post is too long for discord, see the full post at: https://www.reddit.com{post[5]}*')
        await ctx.send(post[4])

def setup(client):
    client.add_cog(Reddit(client))