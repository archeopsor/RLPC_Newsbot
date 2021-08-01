import discord
from discord.ext import commands
from discord.ext.commands.context import Context

import numpy as np
import pandas as pd
import dataframe_image as dfi
import os
import matplotlib.pyplot as plt
from matplotlib.image import AxesImage


from settings import prefix, forecast_sheet, leagues

from rlpc.team_stats import PoissonDataHandler, SheetsPoisson
from rlpc.players import Identifier
from rlpc.elo import EloHandler

from tools.sheet import Sheet
from tools.mongo import Session

bot = commands.Bot(command_prefix=prefix)


class ELO(commands.Cog):

    def __init__(self, bot: commands.Bot, session: Session = None, identifier: Identifier = None, fc_sheet: Sheet = None, elo: EloHandler = None, poissonHandler: SheetsPoisson = None):
        self.bot = bot

        if not session:
            self.session = Session()
        else:
            self.session = session
        if not identifier:
            self.identifier = Identifier(self.session)
        else:
            self.identifier = identifier
        if not fc_sheet:
            self.fc_sheet = Sheet(forecast_sheet)
        else:
            self.fc_sheet = fc_sheet
        if not elo:
            self.elo = EloHandler(session=self.session,
                                  identifier=self.identifier)
        else:
            self.elo = elo
        if not poissonHandler:
            self.poissonHandler = SheetsPoisson()
        else:
            self.poissonHandler = poissonHandler

    @commands.command(aliases=("scorepredict", "predictscore", "score_predict", "predict_score",))
    async def predict(self, ctx: Context, team1: str, team2: str, bestof: float = 5.0):
        async with ctx.typing():
            bestof = float(bestof)
            answer = self.elo.predict(team1, team2, bestof)
        await ctx.send(answer)

    @predict.error
    async def predict_error(self, ctx: Context, error):
        if isinstance(error, commands.MissingRequiredArgument):
            if error.param.name in ['team1', 'team2']:
                await ctx.send('Please include two teams')
            await ctx.send(f'The format for this command is {prefix}predict [team 1] [team 2] [# of games *(optional)*]')
        # else:
        #     await self.bot.log_error(error.original, ctx.channel, ctx.command, ctx.kwargs)

    @commands.command(aliases=("rank",))
    async def rankteams(self, ctx: Context, league):
        async with ctx.typing():
            try:
                league = leagues[league.lower()]
            except KeyError:
                return await ctx.send("Couldn't understand league: "+league)
            answer = self.elo.rank_teams(league)
            standings = discord.Embed(title=f"{league} Rankings", color=0x000080,
                                      description=f"Computer-generated rankings for the {league} league, based on an internal Elo system. For the official, human-made rankings, use $pr")
            value_response = ""
            for i, team in enumerate(answer.index):
                value_response += f"{i+1}: {team} ({answer.loc[team, 'Elo']}) [{answer.loc[team, 'Elo'] - answer.loc[team, 'Previous']}]\n"
            standings.add_field(name="Rankings", value=value_response)
        await ctx.send(embed=standings)

    @rankteams.error
    async def rankteams_error(self, ctx: Context, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send('Please choose a league')

    @commands.command(aliases=("fc", "forecasts", "probs", "prob", "probability", "probabilities",))
    async def forecast(self, ctx: Context, *, msg):
        async with ctx.typing():
            msg = msg.split()
            league = "none"
            team = "none"
            part = "none"

            for word in msg:
                if word.casefold() in ["major", "aaa", "aa", "a", "independent", "indy", "mav", 'maverick', 'renegade', 'ren', 'paladin', 'pal']:
                    league = leagues[word.lower()].lower()
                elif word.casefold() in ['bulls', 'lions', 'panthers', 'sharks', 'cobras', 'ducks', 'eagles', 'hawks', 'ascension', 'flames', 'storm', 'whitecaps', 'kings', 'lumberjacks', 'pirates', 'spartans', 'bulldogs', 'tigers', 'bobcats', 'dolphins', 'vipers', 'geese', 'osprey', 'owls', 'entropy', 'heat', 'thunder', 'tundra', 'knights', 'pioneers', 'raiders', 'trojans', 'mustangs', 'lynx', 'jaguars', 'barracuda', 'pythons', 'herons', 'falcons', 'vultures', 'pulsars', 'inferno', 'lightning', 'avalanche', 'dukes', 'voyagers', 'bandits', 'warriors', 'stallions', 'cougars', 'leopards', 'gulls', 'rattlers', 'pelicans', 'ravens', 'cardinals', 'genesis', 'embers', 'tempest', 'eskimos', 'jesters', 'miners', 'wranglers', 'titans', 'admirals', 'dragons', 'beavers', 'cyclones', 'grizzlies', 'centurions', 'yellow jackets', 'galaxy', 'sockeyes', 'wolves', 'wildcats', 'rhinos', 'scorpions', 'thrashers', 'toucans', 'wizards', 'captains', 'yetis', 'otters', 'tides', 'pandas', 'samurai', 'hornets', 'solar', 'piranhas', 'terriers', 'jackrabbits', 'zebras', 'camels', 'raptors', 'macaws', 'mages', 'pilots', 'werewolves', 'wolverines', 'hurricanes', 'koalas', 'vikings', 'fireflies', 'comets', 'stingrays', 'hounds', 'warthogs', 'gorillas', 'coyotes', 'harriers', 'puffins', 'witches', 'sailors', 'griffins', 'badgers', 'quakes', 'cubs', 'ninjas', 'dragonflies', 'cosmos', 'hammerheads', 'foxes', 'jackals', 'wildebeests', 'roadrunners', 'buzzards', 'penguins', 'sorcerers']:
                    team = word
                elif word.casefold() in ["wins", "expected wins", "record", "playoffs", "playoff", "semifinals", "semifinal", "finals", "final", "finalist", "champions", "champion", "winners", "winner"]:
                    part = word
                    if part in ['playoff', 'semifinal', 'final', 'champion']:
                        part += 's'
                    elif part in ['wins', 'expected wins']:
                        part = 'record'
                    elif part == 'finalist':
                        part = 'finals'
                    elif part in ['winners', 'winner']:
                        part = 'champions'

            datarange: str

            if league == "none" and team == "none":
                return await ctx.send("You haven't chosen a league. You can also see all of the data here: <https://docs.google.com/spreadsheets/d/1GEFufHK5xt0WqThYC7xaK2gz3cwjinO43KOsb7HogQQ/edit?usp=sharing>")
            elif league == "none" and team != "none":
                waitingMsg: discord.Message = await ctx.send(f'Finding league for team "{team}"...', )
                league = self.identifier.find_league(team.title()).lower()
                waitingMsg.delete()
            elif league == "major":
                datarange = "Most Recent!A2:F18"
            elif league == "aaa":
                datarange = "Most Recent!A21:F37"
            elif league == "aa":
                datarange = "Most Recent!A40:F56"
            elif league == "a":
                datarange = "Most Recent!A59:F75"
            elif league == "independent":
                datarange = "Most Recent!A78:F94"
            elif league == "maverick":
                datarange = "Most Recent!A97:F113"
            elif league == "renegade":
                datarange = "Most Recent!A116:F132"
            elif league == "paladin":
                datarange = "Most Recent!A135:F151"

            data = self.fc_sheet.to_df(datarange).set_index('Teams')

            league = leagues[league]

            if team == "none" and part == "none":

                # Returns a stacked bar graph rather than image with numbers
                if 'graph' in [x.lower() for x in msg]:
                    new_data = pd.DataFrame(data.index).set_index("Teams")
                    new_data['Champions'] = data['Champions'].str.rstrip(
                        '%').astype(float)/100
                    new_data['Finals'] = data['Finals'].str.rstrip('%').astype(
                        float)/100 - data['Champions'].str.rstrip('%').astype(float)/100
                    new_data['Semifinals'] = data['Semifinals'].str.rstrip('%').astype(
                        float)/100 - data['Finals'].str.rstrip('%').astype(float)/100
                    new_data['Playoffs'] = data['Playoffs'].str.rstrip('%').astype(
                        float)/100 - data['Semifinals'].str.rstrip('%').astype(float)/100
                    new_data['No Playoffs'] = 1 - \
                        data['Playoffs'].str.rstrip('%').astype(float)/100
                    new_data = new_data.sort_values(
                        by="No Playoffs", ascending=False)
                    plot = new_data.plot(
                        kind='barh', stacked=True, title=f"{league} Forecast", colormap='YlGn_r')
                    plot.set_xlabel("Probability")
                    plot.xaxis.grid(True)
                    plot.figure.savefig('forecast.png')

                    path = os.path.abspath('forecast.png')

                    file = discord.File(path)

                    await ctx.send(file=file)
                    return os.remove(path)

                else:
                    data.rename(columns={
                                "Expected Wins": 'Record', 'Semifinals': 'Semis', 'Champions': 'Champs'}, inplace=True)
                    data['sort'] = data['Record'].astype(
                        float) + data['Champs'].str.rstrip('%').astype(float)
                    data = data.sort_values(by="sort", ascending=False)
                    data.drop(columns=['sort'], inplace=True)
                    data['Record'] = data['Record'].apply(
                        lambda x: f'({round(float(x), 1)} - {round(18-float(x), 1)})')
                    filename = "forecast.png"
                    dfi.export(data, filename, table_conversion='matplotlib')
                    path = os.path.abspath(filename)
                    file = discord.File(path)

                    await ctx.send(file=file)
                    return os.remove(path)

            elif team != "none" and part == "none":
                embed = discord.Embed(
                    title=f'{team.title()} Forecast', description="Average record and probability of making each part of playoffs throughout 100,000 simulations of the league.", color=0x000080)
                data = data.loc[team.title()]
                data['Expected Wins'] = f"({round(float(data['Expected Wins']), 1)} - {round(18-float(data['Expected Wins']), 1)})"
                data.rename({'Expected Wins': 'Record'}, inplace=True)

                for col in data.index:
                    embed.add_field(name=col, value=data[col], inline=False)
                return await ctx.send("See all of the data here: <https://docs.google.com/spreadsheets/d/1GEFufHK5xt0WqThYC7xaK2gz3cwjinO43KOsb7HogQQ/edit?usp=sharing>", embed=embed)

            elif team == "none" and part != "none":
                embed = discord.Embed(
                    title=f'{part.title()} Forecast', description="Average results of 100,000 simulations showing how likely each team was to make it to this point.", color=0x000080)
                if part == 'record':
                    data.rename(
                        columns={'Expected Wins': 'Record'}, inplace=True)
                    data['Record'] = data['Record'].astype(float)
                    data = data.sort_values(by='Record', ascending=False)
                    data['Record'] = data['Record'].apply(
                        lambda x: f'({round(float(x), 1)} - {round(18-float(x), 1)})')
                else:
                    data['sort'] = data[part.title()].str.rstrip(
                        '%').astype(float)
                    data = data.sort_values(by='sort', ascending=False)
                data = data[part.title()]

                for team in data.index:
                    embed.add_field(name=team, value=data[team], inline=False)
                return await ctx.send("See all of the data here: <https://docs.google.com/spreadsheets/d/1GEFufHK5xt0WqThYC7xaK2gz3cwjinO43KOsb7HogQQ/edit?usp=sharing>", embed=embed)

            elif team != "none" and part != "none":
                if part == 'record':
                    data = data.loc[team.title(), 'Expected Wins']
                    data = f'({round(float(data), 1)} - {round(18-float(data), 1)})'
                else:
                    data = data.loc[team.title(), part.title()]
                await ctx.send(data)
                return await ctx.send("See all of the data here: <https://docs.google.com/spreadsheets/d/1GEFufHK5xt0WqThYC7xaK2gz3cwjinO43KOsb7HogQQ/edit?usp=sharing>")

    @forecast.error
    async def forecast_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("You haven't chosen a league. You can also see all of the data here: https://docs.google.com/spreadsheets/d/1GEFufHK5xt0WqThYC7xaK2gz3cwjinO43KOsb7HogQQ/edit?usp=sharing")
        # else:
        #     await self.bot.log_error(error.original, ctx.channel, ctx.command, ctx.kwargs)

    @commands.command(aliases=())
    async def poisson(self, ctx: Context, team1: str, team2: str, numGames: int = 5, img: bool = False):
        async with ctx.typing():
            team1 = team1.title()
            team2 = team2.title()

            try:
                league = self.identifier.find_league(team1)
            except:
                return await ctx.send("Could not find the correct league")
            if league != self.identifier.find_league(team2):
                return await ctx.send("Teams must be from the same league")

            if numGames > 15:
                return await ctx.send("To avoid spam and rate limiting, 15 is the maximum number of games supported.")

            handler = self.poissonHandler

            if img:
                img: AxesImage = plt.imshow(handler.generatePoisson(team1, team2, league)[0])
                plt.title(f'Poisson Distribution: {team1} vs. {team2}', fontsize=16)
                cb = plt.colorbar(img, label="Probability of result")
                plt.xlabel(f"{team1} Goals", fontsize=10)
                plt.ylabel(f"{team2} Goals", fontsize=10)
                img.figure.savefig('poisson.png', bbox_inches='tight')
                cb.remove() # Remove the colorbar so that it doesn't stay for the next function call

                path = os.path.abspath('poisson.png')
                file = discord.File(path)
                await ctx.send(file=file)
                os.remove(path)

            team1Poisson, team2Poisson = handler.getOneWayPoisson(league, team1, team2)
            team1Wins = 0
            team2Wins = 0
            i = 1
            while i <= numGames:
                team1Goals = np.random.choice(
                    [0, 1, 2, 3, 4, 5], p=team1Poisson)
                team2Goals = np.random.choice(
                    [0, 1, 2, 3, 4, 5], p=team2Poisson)
                if team1Goals == team2Goals:
                    # Redo this loop if tied
                    continue
                elif team1Goals > team2Goals:
                    await ctx.send(f"**Game {i} result:** {team1} {team1Goals} - {team2Goals} {team2}")
                    team1Wins += 1
                elif team2Goals > team1Goals:
                    await ctx.send(f"**Game {i} result:** {team2} {team2Goals} - {team1Goals} {team1}")
                    team2Wins += 1

                i += 1
                if team1Wins > (numGames / 2):
                    return await ctx.send(f"{team1} has won the series with a score of {team1Wins} - {team2Wins}")
                elif team2Wins > (numGames / 2):
                    return await ctx.send(f"{team2} has won the series with a score of {team2Wins} - {team1Wins}")

        return await ctx.send(f"The series has ended in a {team1Wins} - {team2Wins} draw. Consider using an odd number of games")

    @poisson.error
    async def poisson_error(self, ctx: Context, error):
        if isinstance(error, commands.BadArgument):
            await ctx.send(f"An error occurred. You may have provided an invalid number of games, or an extra argument other than true or false at the end.")
        # else:
        #     await self.bot.log_error(error.original, ctx.channel, ctx.command, ctx.kwargs)

def setup(bot):
    bot.add_cog(ELO(bot))
