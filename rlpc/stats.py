import numpy as np
import pandas as pd

from tools.sheet import Sheet
from tools.mongo import Session, findCategory, teamIds, statsCategories
from rlpc.players import Teams

from settings import valid_stats, leagues, sheet_p4, sheet_indy, power_rankings_sheet, gdstats_sheet

from errors.stats_errors import *
from errors.sheets_errors import GetSheetError, SheetToDfError


class StatsHandler:
    def __init__(self, session: Session = None, p4sheet: Sheet = None, indysheet: Sheet = None, powerrankings: Sheet = None, gdsheet: Sheet = None, teams: Teams = None):
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
        if not powerrankings:
            self.powerrankings = Sheet(power_rankings_sheet)
        else:
            self.powerrankings = powerrankings
        if not gdsheet:
            self.gdsheet = Sheet(gdstats_sheet)
        else:
            self.gdsheet = gdsheet
        if not teams:
            self.teams = Teams(session=self.session)
        else:
            self.teams = teams

    def get_player_stats(self, player: str, stat: str = "all") -> pd.DataFrame:
        """
        Gets the stats from the RLPC Spreadsheet for a given player

        parameters
        ---------
        player: str
            The player's username, as spelled on the sheet (case insentive)
        stat: (optional) str
            What stat(s) to return. "all" returns all stats, but a single stat can be specified.

        returns
        ------
        stats: pd.DataFrame
            Series containing player's stats
        """
        # Make sure the program understands the specified stat if it's mis-capitalized or whatever
        if stat.lower() in ["sp", "series", "series_played", "series-played", "splayed", "seris", "sieries", "seiries"]:
            stat = "Series Played"
        elif stat.lower() in ["gp", "games", "games_played", "games-played", "gplayed"]:
            stat = "Games Played"
        elif stat.lower() in ["goals", "goal", "scores"]:
            stat = "Goals"
        elif stat.lower() in ['assists', 'assist', 'passes']:
            stat = "Assists"
        elif stat.lower() in ['saves', 'save']:
            stat = "Saves"
        elif stat.lower() in ['shots', 'shot']:
            stat = "Shots"
        elif stat.lower() in ['points', 'point', 'goals+assists', 'goals + assists', 'goals and assists']:
            stat = "Points (Goals+Assists)"
        elif stat.lower() in ['gpg', 'goals per game', 'goals pg', 'goals per']:
            stat = "Goals per game"
        elif stat.lower() in ['apg', 'assists per game', 'assists pg', 'assists per']:
            stat = "Assists per game"
        elif stat.lower() in ['spg', 'sapg', 'saves per game', 'saves pg', 'saves per']:
            stat = "Saves per game"
        elif stat.lower() in ['shot rate', 'shooting percent', 'shooting percentage', 'shot accuracy', 'shooting accuracy', 'shooting %', 'shot %']:
            stat = "Shooting %"
        elif stat.lower() in ['win rate', 'winning rate', 'winning percent', 'winning percentage']:
            stat = "Winning %"
        elif stat.lower() in ['wins', 'win']:
            stat = "Wins"
        elif stat.lower() in ['ppg', 'points per game', 'points pg', 'points per']:
            stat = "Points per Game"
        elif stat.lower() in ['shpg', 'shots per game', ' shots pg', 'shots per']:
            stat = "Shots Per Game"

        try:
            players = self.p4sheet.to_df('Players!A1:I')
        except SheetToDfError:
            raise StatSheetError("Players!A1:I")

        lower_players = players['Username'].str.lower()
        if player.lower() in lower_players.values:
            pindex = lower_players[lower_players == player.lower()].index[0]
            player = players.loc[pindex][0]
        players = players.set_index("Username")
        league = players.loc[player, "League"]
        if type(league) == pd.Series:
            league = league[0]

        try:
            stats = self.p4sheet.to_df(f"{league} League Stat Database!C3:R")
        except:
            raise StatSheetError(f"{league} League Stat Database!C3:R")

        if stat not in list(stats) and stat.lower() != "all":
            raise InvalidStatError(stat)

        stats = stats.loc[stats['Player'] == player]

        if stats.empty:
            raise StatsError(player, stat)

        if stat != "all":
            stats = stats[['Player', stat]]
        return stats

    def power_rankings(self, league: str) -> pd.DataFrame:
        """
        Gets the most recent power rankings for a given league from the power rankings sheet

        parameters
        ---------
        league: str
            What league to get power rankings for

        returns
        ---------
        rankings: pd.DataFrame
            Dataframe containing each team's rank and how many points they had
        """

        try:
            league = leagues[league.lower()]
        except:
            return "Could not understand league"

        start_rows = {'Major': 2, 'AAA': 21, 'AA': 40, 'A': 59,
                      'Independent': 78, 'Maverick': 97, 'Renegade': 116, 'Paladin': 135}
        data_range = f'Rankings History!A{start_rows[league]}:M{start_rows[league]+16}'
        try:
            data = self.powerrankings.to_df(data_range).set_index('')
        except GetSheetError or SheetToDfError:
            raise PRSheetError(league)
        if data.empty:
            raise NoPRError(league)

        column = 1
        for i in range(12):
            if data.iloc[:, i].values[0] == '':
                column = i-1
                break
            else:
                continue
        try:
            data.iloc[:, column] = data.iloc[:, column].apply(lambda x: int(x))
        except ValueError:
            raise NoPRError(league)
        rankings = data.iloc[:, column]
        rankings = rankings.sort_values(ascending=False)
        return rankings

    def statlb(self, useSheet: bool = False, league: str = "all", stat: str = "Goals", limit: int = 10, pergame: bool = False, asc: bool = False) -> pd.Series:
        """Gets a series containing a leaderboard for a given stat

        Args:
            useSheet (bool, optional): Whether to use stats from the sheet instead of database (League can't be "all" if True). Defaults to False.
            league (str, optional): Which league to get stats from. Defaults to "all".
            stat (str, optional): Which stat to look at. Defaults to "Goals".
            limit (int, optional): How many players to include on the leaderboard. Defaults to 10.
            pergame (bool, optional): Whether to divide stats by # games played. Defaults to False.

        Returns:
            pd.Series: Sorted series containing players and their stats
        """
        if useSheet == True and league == "all":
            return "Must choose a specific league to use sheet stats"
        if league != "all":
            try:
                league = leagues[league.lower()]
            except:
                return f"Could not understand league {league}."

        extended_stats = {
            'Winning %': ['Games Won', 'Games Played'],
            'Shooting %': ['Shots', 'Games Played'],
            'Points': ['Goals', 'Assists']
        }

        stat = stat.title()

        # Make sure the program understands the specified stat if it's mis-capitalized or whatever
        # SHEETS STATS
        if useSheet:
            if stat.lower() in ["sp", "series", "series_played", "series-played", "splayed", "seris", "sieries", "seiries"]:
                stat = "Series Played"
            elif stat.lower() in ["gp", "games", "games_played", "games-played", "gplayed"]:
                stat = "Games Played"
            elif stat.lower() in ["goals", "goal", "scores"]:
                stat = "Goals"
            elif stat.lower() in ['assists', 'assist', 'passes']:
                stat = "Assists"
            elif stat.lower() in ['saves', 'save']:
                stat = "Saves"
            elif stat.lower() in ['shots', 'shot']:
                stat = "Shots"
            elif stat.lower() in ['points', 'point', 'goals+assists', 'goals + assists', 'goals and assists']:
                stat = "Points (Goals+Assists)"
            elif stat.lower() in ['gpg', 'goals per game', 'goals pg', 'goals per']:
                stat = "Goals per game"
            elif stat.lower() in ['apg', 'assists per game', 'assists pg', 'assists per']:
                stat = "Assists per game"
            elif stat.lower() in ['spg', 'sapg', 'saves per game', 'saves pg', 'saves per']:
                stat = "Saves per game"
            elif stat.lower() in ['shot rate', 'shooting percent', 'shooting percentage', 'shot accuracy', 'shooting accuracy', 'shooting %', 'shot %']:
                stat = "Shooting %"
            elif stat.lower() in ['win rate', 'winning rate', 'winning percent', 'winning percentage']:
                stat = "Winning %"
            elif stat.lower() in ['wins', 'win']:
                stat = "Wins"
            elif stat.lower() in ['ppg', 'points per game', 'points pg', 'points per']:
                stat = "Points per Game"
            elif stat.lower() in ['shpg', 'shots per game', ' shots pg', 'shots per']:
                stat = "Shots Per Game"
            else:
                raise InvalidStatError(stat)
        
            try:
                if league.lower() in ['major', 'aaa', 'aa', 'a']:
                    data = self.p4sheet.to_df(
                        f'{league} League Stat Database!C3:R')
                elif league.lower() in ['independent', 'maverick', 'renegade', 'paladin']:
                    data = self.indysheet.to_df(
                        f'{league} Stat Database!C3:R')
            except SheetToDfError:
                raise StatSheetError('{league} League Stat Database!C3:R')

            data.set_index("Player", inplace=True)
            data.replace(to_replace='', value='0', inplace=True)
            # Turn number strings into ints and floats
            for col in data.columns:
                try:
                    data[col] = data[col].astype(int)
                except:
                    try:
                        data[col] = data[col].astype(float)
                    except:
                        data[col] = data[col].str.rstrip('%').astype(float)

            lb = data[stat.title()]
            lb: pd.Series = lb[lb > 0]
            games_played = data['Games Played']

            if pergame:
                if stat in ['Goals Per Game', 'Assists per game', 'Saves per game', 'Points per Game', 'Shots per Game', 'Winning %', 'Shooting %']:
                    pass  # These stats are already per game
                else:
                    lb = round(lb/games_played, 2)
        
        # DATABASE STATS
        else:
            if stat not in valid_stats and stat not in extended_stats.keys():
                raise InvalidStatError(stat)
            else:
                stat = stat.title()

            players = self.session.players
            data = pd.Series(name=stat, dtype=float)

            if stat not in extended_stats.keys():
                category = findCategory(stat)
                if not category:
                    raise InvalidStatError(stat)

                try:
                    if league != "all":
                        cursor = players.find({"info.league": league, f"stats.{category}.{stat}": {'$gt': 0}, "stats.general.Games Played": {'$gt': 0}})
                    else:
                        cursor = players.find({f"stats.{category}.{stat}": {'$gt': 0}, "stats.general.Games Played": {'$gt': 0}})
                except:
                    raise FindPlayersError(league, stat)

                # Iterate through cursor and get all players' stats
                while cursor.alive:
                    info = cursor.next()
                    if pergame:
                        data[info['username']] = round((info['stats'][category][stat] / info["stats"]["general"]["Games Played"]), 2)
                    else:
                        data[info['username']] = round(info['stats'][category][stat], 2)
                
                return data.sort_values(ascending=asc).head(limit)
            else:
                filter = {}
                if league != "all":
                    filter['info.league'] = league
                necessary = extended_stats[stat]
                for i in necessary:
                    filter[f'stats.{findCategory(i)}.{i}'] = {'$gt': 0}
                
                try:
                    cursor = players.find(filter)
                except:
                    raise FindPlayersError(league, stat)

                # Iterate throuch cursor and get all players' stats
                while cursor.alive:
                    info = cursor.next()
                    if stat == 'Winning %':
                        datapoint = round((info['stats']['general']['Games Won'] / info['stats']['general']['Games Played']), 2)
                    elif stat == 'Shooting %':
                        datapoint = round((info['stats']['general']['Goals'] / info['stats']['general']['Shots']), 2)
                    elif stat == 'Points':
                        datapoint = round((info['stats']['general']['Goals'] / info['stats']['general']['Assists']), 2)
                        if pergame:
                            datapoint = round((datapoint / info['stats']['general']['Games Played']), 2)
                    data[info['username']] = datapoint
                
                return data.sort_values(ascending=asc).head(limit)

        return lb.sort_values(ascending=asc).head(limit)

    def get_me(self, discord_id: str) -> str:
        ids = self.p4sheet.to_df(
            'PlayerIDs!A1:B').set_index('Discord ID')
        try:
            player = ids.loc[discord_id, 'Username']
        except:
            raise FindMeError(discord_id)
        
        return player

    def gdstats(self, player: str, day: int, stat: str = None, pergame: bool = False) -> pd.DataFrame:
        dates = {1: '7/20/21 Data', 2: '7/22/21 Data', 3: '7/27/21 Data', 4: '7/29//21 Data', 5: '8/3/21 Data', 6: '8/5/21 Data', 7: '8/10/21 Data', 8: '8/12/21 Data', 9: '8/17/21 Data',
                 10: '8/19/21 Data', 11: '8/24/21 Data', 12: '8/26/21 Data', 13: '8/31/21 Data', 14: '9/2/21 Data', 15: '9/7/21 Data', 16: '9/9/21 Data', 17: '9/14/21 Data', 18: '9/16/21 Data'}
        try:
            datarange = dates[day]
        except KeyError:
            raise InvalidDayError(day)

        try:
            data = self.gdsheet.to_df(datarange).set_index("Username")
        except SheetToDfError:
            raise GDStatsSheetError(day)

        lower_players: pd.Index = data.index.str.lower()
        if player.lower() in lower_players.values:
            pindex = np.where(lower_players.to_numpy() == player.lower())
            player = data.index[pindex].values[0]
        else:
            raise PlayerNotFoundError(player, day)

        stats_series = data.loc[player]

        if pergame:
            stats_series[3:-1] = stats_series[3:-
                                              1].apply(lambda x: float(x)) / int(stats_series['Games Played'])
            stats_series[3:-1] = stats_series[3:-
                                              1].apply(lambda x: round(x, 2))

        return stats_series

    def teamstats(self, team: str):
        team = team.title()
        roster = self.teams.get_roster(team)


if __name__ == "__main__":
    StatsHandler().power_rankings("major")