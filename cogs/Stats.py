import os
from discord.ext.commands.errors import MissingRequiredArgument
from discord.ext.commands.context import Context
import pandas as pd
from tools.mongo import Session
import discord
from discord.ext import commands
import numpy as np
import dataframe_image as dfi

from rlpc import mmr
from rlpc.stats import StatsHandler
from rlpc.players import Players, Identifier

from tools.sheet import Sheet

from settings import prefix, valid_stats, leagues, sheet_p4, sheet_indy, gdstats_sheet, divisions

client: commands.Bot = commands.Bot(command_prefix=prefix)


class Stats(commands.Cog):

    def __init__(self, client: commands.Bot, session: Session = None, p4sheet: Sheet = None, indysheet: Sheet = None, gdsheet: Sheet = None, identifier: Identifier = None, players: Players = None, stats: StatsHandler = None):
        self.client = client

        if not session:
            self.session = Session()
        else:
            self.session = session
        if not p4sheet:
            self.p4sheet = Sheet(sheet_p4)
        else:
            self.p4sheet = p4sheet
        if not indysheet:
            self.indysheet = Sheet(sheet_indy)
        else:
            self.indysheet = indysheet
        if not gdsheet:
            self.gdsheet = Sheet(gdstats_sheet)
        else:
            self.gdsheet = gdsheet
        if not identifier:
            self.identifier = Identifier(
                session=self.session, p4sheet=self.p4sheet)
        else:
            self.identifier = identifier
        if not players:
            self.players = Players(session=self.session, p4sheet=self.p4sheet)
        if not stats:
            self.stats = StatsHandler(
                session=self.session, p4sheet=self.p4sheet, indysheet=self.indysheet)
        else:
            self.stats = stats

    @commands.command(aliases=('validstats', 'valid_stats',))
    async def valid(self, ctx: Context):
        await ctx.send(f"""**Valid stats**: ['Series Played', 'Games Played', 'Goals', 'Assists', 'Saves', 'Shots', 'Points (Goals+Assists)', 'Goals per game', 'Assists per game', 'Saves per game', 'Shooting %', 'Winning %', 'Wins', 'Points per Game', 'Shots Per Game'].\n**Advanced stats** (may need to specify 'db' or 'advanced' in the command to use these): {valid_stats}.""")

    @commands.command(aliases=('power', 'powerrankings', 'power_rankings', 'rankings', 'ranking',))
    async def pr(self, ctx: Context, league: str):
        async with ctx.typing():
            if league.casefold() == "major":
                league = "Major"
            elif league.casefold() in ["indy", "independent"]:
                league = "Independent"
            elif league.casefold() in ['mav', 'maverick']:
                league = "Maverick"
            elif league.casefold() in ['ren', 'renegade']:
                league = "Renegade"
            elif league.casefold() in ['pal', 'paladin']:
                league = "Paladin"
            else:
                league = league.upper()
            rankings = self.stats.power_rankings(league)
            embed = discord.Embed(
                title=f'{league} Power Rankings', description=f"Official human-generated Power Rankings for {league}. For computer rankings, use $rank", color=0x000080)

            value_response = ''
            for row in range(16):
                value_response += f"{row+1}: {rankings.index[row]}"
                if rankings.iloc[row] == rankings.iloc[(row+1 if row < 15 else 0)] or rankings.iloc[row] == rankings.iloc[(row-1 if row > 0 else 15)]:
                    value_response += f"ᵀ ({rankings.iloc[row]})\n"
                else:
                    value_response += f" ({rankings.iloc[row]})\n"

            embed.add_field(name="Rankings", value=value_response)

            await ctx.send(embed=embed)

    @pr.error
    async def prerror(self, ctx: Context, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("You haven't chosen a league.")

    @commands.command()  # TODO: fix this
    async def mmr(self, ctx: Context, *, player: str):
        async with ctx.typing():
            players = self.p4sheet.to_df('Players!A1:R')

            # Remove case-sensitivity
            lower_players = players['Username'].str.lower()
            if player.casefold() in lower_players.values:
                pindex = lower_players[lower_players ==
                                       player.casefold()].index[0]
                player = players.loc[pindex][0]
            players = players.reset_index()

            mmrs = {}
            try:
                players.loc[player]
            except:
                await ctx.send(f"Coudn't find player {player}")
                return

            for url in players.loc[player, 'Tracker'].split(", "):
                platform, name = url.split('/')[-2:]
                mmrs[name] = {}
                mmrs[name]['Duels'] = mmr.playlist(platform, name, '1s')
                mmrs[name]['Doubles'] = mmr.playlist(platform, name, '2s')
                mmrs[name]['Solo Standard'] = mmr.playlist(
                    platform, name, 'ss')
                mmrs[name]['Standard'] = mmr.playlist(platform, name, '3s')

                embed = discord.Embed(title=f"{player}'s MMRs", color=0xffffff)
                for playlist in list(mmrs[name]):
                    embed.add_field(
                        name=playlist, value=f'{mmrs[name][playlist]["rank"]} ({mmrs[name][playlist]["rating"]})')

                await ctx.send(embed=embed)

    @commands.command(aliases=("getstats", "stats", "get_stats",))
    # TODO: Add database stats
    async def get_player_stats(self, ctx: Context, *, msg: str):
        async with ctx.typing():
            if msg.casefold() == "me":
                waitingMsg: discord.Message = await ctx.send("One second, retreiving discord ID and stats")
                msg = str(ctx.author.id)
                ids = self.p4sheet.to_df(
                    'PlayerIDs!A1:B').set_index('Discord ID')
                try:
                    msg = ids.loc[msg, 'Username']
                except:
                    return await ctx.send("You don't appear to have an up-to-date discord id on record. Try using the name that shows up on the RLPC spreadsheet.")
                await waitingMsg.delete(delay=5)
            first = " ".join(msg.split()[:-1])
            last = msg.split()[-1]
            try:
                answer = self.stats.get_player_stats(first, last)
                if answer == 'That stat could not be understood.':
                    raise Exception
            except:
                try:
                    answer = self.stats.get_player_stats(msg)
                except:
                    await ctx.send(f"Cound not find player {msg}")
                    return

            try:
                embed = discord.Embed(
                    title=f"{answer.values[0][0]}'s Stats", color=0x3333ff)
            except:
                return await ctx.send(f"Could not find {msg}'s stats. Contact arco if you think this is a bug")
            for i, col in enumerate(answer.columns[1:]):
                embed.add_field(name=col, value=answer.values[0][i+1])
        await ctx.send(embed=embed)

    @commands.command(aliases=("topstats", "statslb", "stats_lb",))
    async def top(self, ctx: Context, *, msg):
        async with ctx.typing():
            # Default arguments
            useSheet = False
            league = "all"
            stat = "Points Per Game"
            limit = 10
            pergame = False

            msg = msg.split()

            for i, word in enumerate(msg):
                try:
                    limit = int(word)
                except:
                    pass
                if word.lower() in leagues.keys():
                    league = leagues[word.lower()]
                elif word.lower() in ['pg', 'pergame']:
                    pergame = True
                elif word.lower() in ['sheet', 'usesheet']:
                    useSheet = True
                elif word.lower() in ['db', 'database', 'fantasy', 'fantasydb']:
                    useSheet = False
                # First word of a stat
                elif word.lower() in [x.split()[0].lower() for x in valid_stats]:
                    stat = word.title()
                    if len(msg) == i+1:  # If that was the last arg in the msg
                        break
                    if msg[i+1].lower() in [x.split()[1].lower() if len(x.split()) > 1 else None for x in valid_stats]:  # Second word
                        stat = stat + ' ' + msg[i+1].title()
                        if len(msg) == i+2:  # If the next arg is the last arg in the msg
                            break
                        if msg[i+2].lower() in [x.split()[2].lower() if len(x.split()) > 2 else None for x in valid_stats]:  # Third word
                            stat = stat + ' ' + msg[i+2].title()

            # For common misused stat names
            statsmap = {'Demos': 'Demos Inflicted'}
            if stat in statsmap.keys():
                stat = statsmap[stat]

            lb = self.stats.statlb(
                useSheet=useSheet, league=league, stat=stat, limit=limit, pergame=pergame)

            embed = discord.Embed(title=f'{stat} {"Per Game " if pergame else ""}Leaderboard',
                                  description=f"League: {league}, Source: {'Sheet' if useSheet else 'Fantasy Database'}")
            for i, player in enumerate(lb.index):
                embed.add_field(name=f'{i+1}) {player}',
                                value=lb[player], inline=False)

        return await ctx.send(embed=embed)

    @commands.command(aliases=("gameday_stats",))
    async def gdstats(self, ctx: Context, *, msg):
        async with ctx.typing():
            player = "me"
            day = '1'
            stat = None
            pergame = False

            msg = msg.split(' ')
            used_args = []

            for i, arg in enumerate(msg):
                try:
                    day = str(int(arg))  # Ensure that it's an integer
                    used_args.append(arg)
                    continue
                except:
                    pass
                if arg == 'me':
                    used_args.append(arg)
                elif 'gd' in arg:
                    try:
                        # Ensure that it's an integer
                        day = str(int(arg.split('gd')[-1]))
                        used_args.append(arg)
                    except:
                        pass
                elif arg == 'pg':
                    pergame = True
                    used_args.append(arg)
                # First word of a stat
                elif arg.lower() in [x.split()[0].lower() for x in valid_stats]:
                    stat = arg.title()
                    used_args.append(arg)
                    if len(msg) == i+1:  # If that was the last arg in the msg
                        break
                    if msg[i+1].lower() in [x.split()[1].lower() if len(x.split()) > 1 else None for x in valid_stats]:  # Second word
                        stat = stat + ' ' + msg[i+1].title()
                        used_args.append(msg[i+1])
                        if len(msg) == i+2:  # If the next arg is the last arg in the msg
                            break
                        if msg[i+2].lower() in [x.split()[2].lower() if len(x.split()) > 2 else None for x in valid_stats]:  # Third word
                            stat = stat + ' ' + msg[i+2].title()
                            used_args.append(msg[i+2])

            if len(msg) > len(used_args):  # If there are still args left, it must be the player
                for i in used_args:
                    msg.remove(i)
                player = ' '.join(msg)

            dates = {'1': '3/16/21 Data', '2': '3/18/21 Data', '3': '3/23/21 Data', '4': '3/25/21 Data', '5': '3/30/21 Data', '6': '4/1/21 Data', '7': '4/6/21 Data', '8': '4/8/21 Data', '9': '4/13/21 Data',
                     '10': '4/15/21 Data', '11': '4/20/21 Data', '12': '4/22/21 Data', '13': '4/27/21 Data', '14': '4/29/21 Data', '15': '5/4/21 Data', '16': '5/6/21 Data', '17': '5/11/21 Data', '18': '5/13/21 Data'}
            try:
                if 'gd' in day:
                    day = day.split('gd')[-1]
                datarange = dates[day]
            except:
                return await ctx.send(f'{day} is not a valid gameday. Please enter a number between 1 and 18.')

            try:
                data = self.gdsheet.to_df(datarange).set_index("Username")
            except:
                return await ctx.send(f'There was an error retrieving data from gameday {day}.')

            if player.lower() == "me":
                waitingMsg = await ctx.send("One second, retreiving discord ID and stats")
                playerid = str(ctx.author.id)
                ids = self.p4sheet.to_df(
                    'PlayerIDs!A1:B').set_index('Discord ID')
                try:
                    player = ids.loc[playerid, 'Username']
                except:
                    return await ctx.send("You don't appear to have an up-to-date discord id on record. Try using the name that shows up on the RLPC spreadsheet.")
                await waitingMsg.delete(delay=3)

            lower_players = data.index.str.lower()
            if player.lower() in lower_players.values:
                print("test")
                pindex = np.where(lower_players.to_numpy() == player.lower())
                player = data.index[pindex].values[0]
                print(player)
            else:
                return await ctx.send(f"Could not find stats for {player} on gameday {day}.")

            try:
                statsSeries = data.loc[player]
            except:
                return await ctx.send(f"Could not find stats for {player} on gameday {day}.")

            if pergame:
                statsSeries[3:-1] = statsSeries[3:-
                                    1].apply(lambda x: float(x)) / int(statsSeries['Games Played'])
                statsSeries[3:-1] = statsSeries[3:-1].apply(lambda x: round(x, 2))

            if stat == None:
                embed = discord.Embed(
                    title=f"{player}'s Stats on Gameday {day}", color=0x3333ff)
                embed.add_field(name='Games Played',
                                value=f'{statsSeries.loc["Games Played"]}')
                embed.add_field(name="Goals", value=f"{statsSeries.loc['Goals']}")
                embed.add_field(
                    name="Assists", value=f"{statsSeries.loc['Assists']}")
                embed.add_field(name="Saves", value=f"{statsSeries.loc['Saves']}")
                embed.add_field(name="Shots", value=f"{statsSeries.loc['Shots']}")
                embed.add_field(name="Fantasy Points",
                                value=f"{statsSeries.loc['Fantasy Points']}")

                return await ctx.send(embed=embed)

            else:
                try:
                    return await ctx.send(statsSeries.loc[stat.title()])
                except:
                    return await ctx.send(f'Could not understand stat "{stat}".')

    @gdstats.error
    async def gdstats_error(self, ctx: Context, error):
        if isinstance(error, commands.MissingRequiredArgument):
            return await ctx.send(error)

    @commands.command(aliases=("schedules", "scheduling",))
    async def schedule(self, ctx: Context, team: str):
        async with ctx.typing():
            team: str = team.title()
            if team not in divisions.keys():
                return await ctx.send("Couldn't find team" + team)

            league: str = self.identifier.find_league(team)
            sheet: Sheet = self.p4sheet if league.lower(
            ) in ['major', 'aaa', 'aa', 'a'] else self.indysheet
            all_games: pd.DataFrame = sheet.to_df(f"{league} Schedule!N4:V")
            if not all_games:
                return await ctx.send("Schedules couldn't be found, possibly because they aren't on the sheet. Contact arco if you believe this is an error.")

            all_games.columns.values[2] = "Team 1"
            all_games.columns.values[4] = "Team 2"
            all_games.columns.values[7] = "Logs"
            all_games.drop(
                columns=["Playoff", "Game Logs Processed"], inplace=True)

            schedule: pd.DataFrame = all_games.loc[(
                all_games['Team 1'] == team) | (all_games["Team 2"] == team)]
            schedule.set_index("Day", drop=True, inplace=True)

            dfi.export(schedule, "schedule.png", table_conversion='matplotlib')
            path = os.path.abspath("schedule.png")
            file = discord.File(path)
            await ctx.send(file=file)
            return os.remove(path)

    @schedule.error
    async def schedule_error(self, ctx: Context, error):
        if isinstance(error, MissingRequiredArgument):
            return await ctx.send("Please specify a team.")

    @commands.command(aliases=("teambuilder", "team_builder", "builder",))
    async def build(self, ctx: Context, *, players):
        pass


def setup(client: commands.Bot):
    client.add_cog(Stats(client))
