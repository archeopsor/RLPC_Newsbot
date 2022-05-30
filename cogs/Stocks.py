import discord
from discord.ext import commands
from discord.ext.commands.context import Context
from discord import AllowedMentions
from datetime import datetime
import os

from settings import prefix

from tools.mongo import Session
from errors.stocks_errors import *

class Stocks(commands.Cog):
    def __init__(self,  bot: commands.Bot, session: Session = None):
        self.bot = bot
        if not session:
            self.session = Session()
        else:
            self.session = session

    @commands.command()
    async def sHelp(self, ctx: Context, specified: str = ""):
        async with ctx.typing():
            path = '/'.join(os.getcwd().split('\\')) + '/help_text/'

            if specified.lower() == 'commands':
                path = path + "Stocks_Commands.txt"
            else:
                path = path + "Stocks.txt"

            with open(path) as f:
                text = f.read()
                text = text.replace('{prefix}', prefix)

        return await ctx.send(text, allowed_mentions = AllowedMentions(users=False, everyone=False, roles=False, replied_user=True))

    @commands.command()
    async def sJoin(self, ctx: Context):
        async with ctx.typing():
            discord_id = str(ctx.author.id)

            # First check to see if there's already an account for this person
            cursor = self.session.stock_accounts.find({"_id": discord_id})
            if len(list(cursor)) > 0:
                return await ctx.send(f"You already have an account! If you recently changed your username, you may need to use `{prefix}sUpdate` to update it.")

            self.session.stock_accounts.insert_one({
                "_id": discord_id,
                "username": ctx.author.name,
                "balance": 1000,
                "portfolio_value": 1000,
                "value_history": {datetime.now().strftime("%D"): 1000},
                "portfolio": [],
                "transaction_history": []
            })

        return await ctx.send("Your account has been created! Use `$sHelp` to see what you can do with it.")

    @commands.command()
    async def sUpdate(self, ctx: Context):
        self.session.stock_accounts.update_one({"_id": str(ctx.author.id)}, {"$set": {"username": ctx.author.name}})
        return await ctx.send(f"Your RLPC Stocks account now has a username of `{ctx.author.name}`")

    @commands.command()
    async def sTaxes(self, ctx: Context):
        return await ctx.send("""
There are currently no taxes! Enjoy the freedom :)
"""
        )

    @commands.command(aliases=('port', 'sport', 'portfolio', 'bal', 'sBal'))
    async def sPortfolio(self, ctx: Context, user: str = "me"):
        async with ctx.typing():
            if user.lower() == "me":
                account = self.session.stock_accounts.find_one({"_id": str(ctx.author.id)})
            else:
                account = self.session.stock_accounts.find_one({"username": user})

            if not account:
                return await ctx.send(f"This person doesn't appear to have an RLPC Stocks account! `{prefix}sJoin` can be used to create one, or `{prefix}sUpdate can be used to change your account name.")

            embed = discord.Embed(
                title=f"{account['username']}'s Portfolio",
                description=f"Balance: {account['balance']}",
                color=0xCBCE32,
            )

            for stock in account['portfolio']:
                if (stock['num'] + stock['in_market']) > 0:
                    embed.add_field(name = stock['id'], value = f"{stock['num'] + stock['in_market']} ({stock['in_market']} being sold)")

        return await ctx.send(embed = embed)

    @commands.command()
    async def sSell(self, ctx: Context, item: str, num_shares: int, min_share_price: int):
        async with ctx.typing:
            account: dict = self.session.stock_accounts.find_one({"_id": str(ctx.author.id)})
            if not account:
                return await ctx.send(f"You don't have an RLPC Stocks account! Use `{prefix}sJoin` to create one.")
            if min_share_price <= 0 or num_shares <= 0:
                return await ctx.send(f"Sell order is invalid. Must sell at least 1 share for at least $1 per share.")

            # Make sure person has the stocks
            stock: dict = account['portfolio'].get(item)
            if not stock:
                return await ctx.send(f"You don't appear to own any shares of {item}. Make sure you spelled it correctly, with correct capitalization.")
            elif stock['num'] < num_shares:
                return await ctx.send(f"You only have {stock['num']} shares available to sell!")
            else:
                # See if there are any buy orders that can be filled with this sell order
                buy_orders = list(self.session.stock_orders.find({
                    "owner": {"$ne": account['_id']},
                    "type": "buy",
                    "stock": item,
                    "max_share_price": {"$gte": min_share_price},
                }).sort({"max_share_price": -1}))

                for order in buy_orders:
                    shares_available = order['shares']

                    # If the buy order is enough to completely fill the sell order and have shares leftover
                    if shares_available > num_shares:
                        self.pay(account['_id'], order['owner'], order['max_share_price']*num_shares)  # Transfer funds
                        self.session.stock_orders.update_one({"_id": order['_id']}, {"$inc": {"shares": 0 - num_shares}})   # Decrease shares available in buy order
                        self.session.stock_accounts.update_one({"_id": order['owner'], 'portfolio.id': item}, {"$inc": {'portfolio.$.num': num_shares}})    # Add shares to buyer's account
                        self.session.stock_accounts.update_one({"_id": account['_id'], 'portfolio.id': item}, {"$inc": {'portfolio.$.num': 0 - num_shares}})   # Remove shares from seller's account
                        if [stock for stock in account['portfolio'] if stock['id'] == item][0]['num'] == num_shares:
                            self.session.stock_accounts.update_one({"_id": account['_id'], 'portfolio.id': item}, {"$pull": {"portfolio": {"id": item}}})   # Remove stock from seller's portfolio if needed
                        await ctx.send(f"Your shares were automatically sold to {order['owner_name']} at a price of ${order['max_share_price']} per share.")
                        buyer: discord.User = self.bot.get_user(int(order['owner']))
                        await buyer.send(f"{num_shares} shares of your buy order for {item} was filled by {account['username']} at a price of ${order['max_share_price']} per share")
                        return
                    # If the buy order is exactly enough to fill the sell order TODO
                    elif shares_available == num_shares:
                        self.pay(account['_id'], order['owner'], order['max_share_price']*num_shares)  # Transfer funds
                        self.session.stock_orders.update_one({"_id": order['_id']}, {"$inc": {"shares": 0 - num_shares}})   # Decrease shares available in buy order
                        self.session.stock_orders.delete_one({"_id": order['_id']})   # Delete buy order
                        self.session.stock_accounts.update_one({"_id": order['owner'], 'portfolio.id': item}, {"$inc": {'portfolio.$.num': num_shares}}) # Add shares to buyer's account
                        self.session.stock_accounts.update_one({"_id": account['_id'], 'portfolio.id': item}, {"$inc": {'portfolio.$.num': 0 - num_shares}}) # Remove shares from seller's account
                        await ctx.send(f"Your shares were automatically sold to {order['owner_name']} at a price of ${order['max_share_price']} per share.")
                        buyer: discord.User = self.bot.get_user(int(order['owner']))
                        await buyer.send(f"Your buy order for {item} was filled by {account['username']} at a price of ${order['max_share_price']} per share")
                        return

                sell_order = {
                    "type": "sell",
                    "owner": account['_id'],
                    "owner_name": account['username'],
                    "stock": item,
                    "shares": num_shares,
                    "min_share_price": min_share_price
                }

            # TODO: Finish selling shares

    @commands.command()
    async def sBuy(self, ctx: Context, item: str, num_shares: int, max_share_price: int):
        async with ctx.typing:
            pass # TODO: Add buying shares

    def pay(self, payer: str, recipient: str, amount: int) -> None:
        payer_account: dict = self.session.stock_accounts.find_one({"_id": payer})
        recipient_account: dict = self.session.stock_accounts.find_one({"_id": recipient})

        if not payer_account or not recipient_account:
            raise AccountNotFoundError(id=(payer, recipient))
        elif payer_account['balance'] < amount:
            raise InsufficientFundsError()
        else:
            self.session.stock_accounts.update_one({"_id": payer}, {'$inc': {'balance': 0 - amount}})
            self.session.stock_accounts.update_one({"_id": recipient}, {'$inc': {'balance': amount}})

    def move_shares(self, giver: str, recipient: str, amount: int, from_market: True):
        pass