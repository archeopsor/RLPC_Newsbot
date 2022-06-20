import discord
from discord import app_commands
from discord.ext import commands
from discord.ext.commands.context import Context

import numpy as np
import pandas as pd
import dataframe_image as dfi
import os
import matplotlib.pyplot as plt
from matplotlib.image import AxesImage


from settings import prefix, forecast_sheet, leagues, divisions

from rlpc.team_stats import PoissonDataHandler, SheetsPoisson
from rlpc.players import Identifier
from rlpc.elo import EloHandler

from tools.sheet import Sheet
from tools.mongo import Session

class Elo(commands.Cog):
    def __init__(
        self,
        bot: commands.Bot,
        session: Session = None,
        identifier: Identifier = None,
        fc_sheet: Sheet = None,
        elo: EloHandler = None,
        poissonHandler: SheetsPoisson = None,
    ):
        self.bot = bot

        self.session = session if session else Session()
        self.identifier = identifier if identifier else Identifier(self.session)
        self.fc_sheet = fc_sheet if fc_sheet else Sheet(forecast_sheet)
        self.elo = elo if elo else EloHandler(session=self.session, identifier=self.identifier)
        self.poissonHandler = poissonHandler if poissonHandler else SheetsPoisson()

    @app_commands.command(name="predict")
    async def predict(self, interaction: discord.Interaction, team1: str, team2: str, bestof: int = 5):
        """Predicts the series score between two teams in the same league based on elo

        Args:
            team1 (str): Team name
            team2 (str): Team name
            bestof (float, optional): Number of games to play.
        """
        async with interaction.channel.typing():
            answer = self.elo.predict(team1, team2, bestof)
        await interaction.response.send_message(answer)

    @app_commands.command(name="rank")
    async def rankteams(self, interaction: discord.Interaction, league: str):
        """Shows the computer-generated elo rankings for any league

        Args:
            league (str): League name
        """
        async with interaction.channel.typing():
            try:
                league = leagues[league.lower()]
            except KeyError:
                return await interaction.response.send_message(f"Couldn't understand league: {league}", ephemeral=True)
            answer = self.elo.rank_teams(league)
            standings = discord.Embed(
                title=f"{league} Rankings",
                color=0x000080,
                description=f"Computer-generated rankings for the {league} league, based on an internal Elo system. For the official, human-made rankings, use $pr",
            )
            value_response = ""
            for i, team in enumerate(answer.index):
                value_response += f"{i+1}: {team} ({answer.loc[team, 'Elo']}) [{answer.loc[team, 'Elo'] - answer.loc[team, 'Previous']}]\n"
            standings.add_field(name="Rankings", value=value_response)
        await interaction.response.send_message(embed=standings)

    @app_commands.command(name="forecast")
    async def forecast(self, interaction: discord.Interaction, league: str, team: str = None, graph: bool = False):
        """Shows the most recent RLPC Forecast, with predicted records and the probability to make it to any point in the playoffs

        Args:
            league (str): Name of a league
            team (str, optional): Name of a team, if you only want to look at one team's results
            graph (bool, optional): Whether or not to show results as a bar graph rather than pure numbers

        Returns:
            _type_: _description_
        """
        async with interaction.channel.typing():

            team = team.title() if team else None
            if league not in leagues:
                return await interaction.response.send_message(f"Could not understand league: {league}", ephemeral = True)
            else:
                league = leagues[league].lower()
            await interaction.response.defer()

            datarange = {
                "major": "Most Recent!A2:F18",
                "aaa": "Most Recent!A21:F37",
                "aa": "Most Recent!A40:F56",
                "a": "Most Recent!A59:F75",
                "independent": "Most Recent!A78:F94",
                "maverick": "Most Recent!A97:F113",
                "renegade": "Most Recent!A116:F132",
                "paladin": "Most Recent!A135:F151",
            }[league]

            data = self.fc_sheet.to_df(datarange).set_index("Teams")
            if '' in data.values:
                return await interaction.followup.send("There don't seem to be any forecasts currently available for this league.")

            league = leagues[league]

            if not team:
                if graph:
                    new_data = pd.DataFrame(data.index).set_index("Teams")
                    new_data["Champions"] = (
                        data["Champions"].str.rstrip("%").astype(float) / 100
                    )
                    new_data["Finals"] = (
                        data["Finals"].str.rstrip("%").astype(float) / 100
                        - data["Champions"].str.rstrip("%").astype(float) / 100
                    )
                    new_data["Semifinals"] = (
                        data["Semifinals"].str.rstrip("%").astype(float) / 100
                        - data["Finals"].str.rstrip("%").astype(float) / 100
                    )
                    new_data["Playoffs"] = (
                        data["Playoffs"].str.rstrip("%").astype(float) / 100
                        - data["Semifinals"].str.rstrip("%").astype(float) / 100
                    )
                    new_data["No Playoffs"] = (
                        1 - data["Playoffs"].str.rstrip("%").astype(float) / 100
                    )
                    new_data = new_data.sort_values(by="No Playoffs", ascending=False)
                    plot = new_data.plot(
                        kind="barh",
                        stacked=True,
                        title=f"{league} Forecast",
                        colormap="YlGn_r",
                    )
                    plot.set_xlabel("Probability")
                    plot.xaxis.grid(True)
                    plot.figure.savefig("forecast.png")

                    path = os.path.abspath("forecast.png")

                    file = discord.File(path)

                    await interaction.followup.send(file=file)
                    file.close()
                    return os.remove(path)

                else:
                    data.rename(
                        columns={
                            "Expected Wins": "Record",
                            "Semifinals": "Semis",
                            "Champions": "Champs",
                        },
                        inplace=True,
                    )
                    data["sort"] = data["Record"].astype(float) + data[
                        "Champs"
                    ].str.rstrip("%").astype(float)
                    data = data.sort_values(by="sort", ascending=False)
                    data.drop(columns=["sort"], inplace=True)
                    data["Record"] = data["Record"].apply(
                        lambda x: f"({round(float(x), 1)} - {round(18-float(x), 1)})"
                    )
                    filename = "forecast.png"
                    dfi.export(data, filename, table_conversion="matplotlib")
                    path = os.path.abspath(filename)
                    file = discord.File(path)

                    await interaction.followup.send(file=file)
                    file.close()
                    return os.remove(path)

            elif team:
                embed = discord.Embed(
                    title=f"{team} Forecast",
                    description="Average record and probability of making each part of playoffs throughout 1,000,000 simulations of the league.",
                    color=0x000080,
                    url="https://docs.google.com/spreadsheets/d/1GEFufHK5xt0WqThYC7xaK2gz3cwjinO43KOsb7HogQQ/edit?usp=sharing",
                )
                try:
                    data = data.loc[team]
                except KeyError:
                    return await interaction.followup.send(f"Could not understand team: {team}", ephemeral = True)
                data[
                    "Expected Wins"
                ] = f"({round(float(data['Expected Wins']), 1)} - {round(18-float(data['Expected Wins']), 1)})"
                data.rename({"Expected Wins": "Record"}, inplace=True)

                for col in data.index:
                    embed.add_field(name=col, value=data[col], inline=False)
                return await interaction.followup.send(embed=embed)

    @app_commands.command(name="poisson")
    async def poisson(
        self, interaction: discord.Interaction, team1: str, team2: str, num_games: int = 5, image: bool = False
    ):
        """Predicts a series between two teams using a poisson process

        Args:
            team1 (str): Team name
            team2 (str): Team name
            numGames (int, optional): Number of games in the series (up to 15 games)
            image (bool, optional): Whether or not to include a visualization of the poisson distribution
        """
        async with interaction.channel.typing():

            await interaction.response.defer()

            team1 = team1.title()
            team2 = team2.title()

            try:
                league = self.identifier.find_league(team1)
            except TypeError:
                return await interaction.followup.send(f"Could not understand team: {team1}", ephemeral = True)
            try:
                if league != self.identifier.find_league(team2):
                    return await interaction.followup.send("Teams must be from the same league", ephemeral = True)
            except TypeError:
                return await interaction.followup.send(f"Couldn't understand team: {team2}")

            if num_games > 15:
                return await interaction.followup.send("To avoid spam and rate limiting, 15 is the maximum number of games supported.", ephemeral = True)

            handler = self.poissonHandler

            if image:
                img: AxesImage = plt.imshow(
                    handler.generatePoisson(team1, team2, league)[0]
                )
                plt.title(f"Poisson Distribution: {team1} vs. {team2}", fontsize=16)
                cb = plt.colorbar(img, label="Probability of result")
                plt.xlabel(f"{team1} Goals", fontsize=10)
                plt.ylabel(f"{team2} Goals", fontsize=10)
                img.figure.savefig("poisson.png", bbox_inches="tight")
                cb.remove()  # Remove the colorbar so that it doesn't stay for the next function call

                path = os.path.abspath("poisson.png")
                file = discord.File(path)
                await interaction.followup.send(file=file)
                file.close()
                os.remove(path)

            if not interaction.response.is_done():
                await interaction.followup.send(f"{team1} vs. {team2}")

            team1Poisson, team2Poisson = handler.getOneWayPoisson(league, team1, team2)
            team1Wins = 0
            team2Wins = 0
            i = 1
            while i <= num_games:
                team1Goals = np.random.choice([0, 1, 2, 3, 4, 5], p=team1Poisson)
                team2Goals = np.random.choice([0, 1, 2, 3, 4, 5], p=team2Poisson)
                if team1Goals == team2Goals:
                    # Redo this loop if tied
                    continue
                elif team1Goals > team2Goals:
                    await interaction.channel.send(
                        f"**Game {i} result:** {team1} {team1Goals} - {team2Goals} {team2}"
                    )
                    team1Wins += 1
                elif team2Goals > team1Goals:
                    await interaction.channel.send(
                        f"**Game {i} result:** {team2} {team2Goals} - {team1Goals} {team1}"
                    )
                    team2Wins += 1

                i += 1
                if team1Wins > (num_games / 2):
                    return await interaction.channel.send(
                        f"{team1} has won the series with a score of {team1Wins} - {team2Wins}"
                    )
                elif team2Wins > (num_games / 2):
                    return await interaction.channel.send(
                        f"{team2} has won the series with a score of {team2Wins} - {team1Wins}"
                    )

        return await interaction.channel.send(
            f"The series has ended in a {team1Wins} - {team2Wins} draw. Consider using an odd number of games"
        )
