from __future__ import annotations
from typing import List
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import pytz

from tools.sheet import Sheet
from tools.mongo import Session, findCategory, statsCategories
from rlpc.players import *

from settings import valid_stats, leagues, sheet_p4, sheet_indy, power_rankings_sheet, gdstats_sheet, current_season

from errors.stats_errors import *
from errors.sheets_errors import GetSheetError, SheetToDfError
from errors.general_errors import *


dates = {1: '5/10/22 Data', 2: '5/12/22 Data', 3: '5/17/22 Data', 4: '5/19/22 Data', 5: '5/24/22 Data', 6: '5/26/22 Data', 7: '5/31/22 Data', 8: '6/2/22 Data', 9: '6/7/22 Data',
        10: '6/9/22 Data', 11: '6/14/22 Data', 12: '6/16/22 Data', 13: '6/21/22 Data', 14: '6/23/22 Data', 15: '6/28/22 Data', 16: '6/30/22 Data', 17: '7/5/22 Data', 18: '7/7/22 Data'}

def get_latest_gameday() -> int:
    day = datetime.now(tz=pytz.timezone("US/Eastern"))
    found_day = False
    
    # Go backwards day by day until a valid day is found (starting yesterday)
    while not found_day:
        day -= timedelta(days=1)
        day_string = f"{day.month}/{day.day}/{day.year - 2000} Data"
        if day_string in dates.values():
            found_day = True
            return list(dates.keys())[list(dates.values()).index(day_string)]
        elif datetime.strptime(list(dates.values())[0], "%m/%d/%y Data").astimezone(pytz.timezone("US/Eastern")) > day: # If the day is earlier than all possible days
            raise InvalidDayError(day=0)

def snakecase_stat(stat: str, reverse: bool = False) -> str:
    if reverse:
        if stat == 'mvps':
            return 'MVPs'
        return stat.replace('_', ' ').replace('num', '#').title()
    else:
        return stat.lower().replace(' ', '_').replace("#", "num")
        

class StatsHandler:
    def __init__(self, session: Session = None, p4sheet: Sheet = None, indysheet: Sheet = None, powerrankings: Sheet = None, gdsheet: Sheet = None, teams: TeamsHandler = None, identifier: Identifier = None):
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
            self.teams = TeamsHandler(session=self.session)
        else:
            self.teams = teams
        if not identifier:
            self.identifier = Identifier(self.session, self.p4sheet)
        else:
            self.identifier = identifier

    def capitalize_username(self, username: str) -> List[str]:
        try:
            players = self.p4sheet.to_df('Players!A1:I')
        except SheetToDfError:
            raise StatSheetError("Players!A1:I")

        lower_players = players['Username'].str.lower()
        if username.lower() in lower_players.values:
            pindex = lower_players[lower_players == username.lower()].index[0]
            player = players.loc[pindex][0]
        players = players.set_index("Username")
        try:
            league = players.loc[player, "League"]
        except UnboundLocalError:
            raise FindPlayersError(None, None)
        if type(league) == pd.Series:
            league = league[0]

        return player, league
    
    def get_player_stats_db(self, player: str, category: str = "all", pergame: bool = False) -> pd.DataFrame:

        player, league = self.capitalize_username(player)
        db_stats = self.session.all_players.find_one({'username': player})
        if db_stats == None:
            raise PlayerNotFoundError(player, 0)
        stats = pd.DataFrame()
        stats.loc[0, 'Player'] = player

        if category not in statsCategories.keys() and category != "all":
            raise InvalidStatError(category)

        games = 1
        if pergame:
            games = max(db_stats['seasons'][-1]['season_stats']['games_played'], 1)

        if category == "all":
            for stat in statsCategories['general']:
                stats.loc[0, stat] = round(db_stats['seasons'][-1]['season_stats'][snakecase_stat(stat)] / games, 1)
        else:
            keys = statsCategories[category]
            for key in keys:
                stats.loc[0, key] = round(db_stats['seasons'][-1]['season_stats'][snakecase_stat(key)] / games, 1)

        return stats

    def get_player_stats_sheet(self, player: str, stat: str = "all") -> pd.DataFrame:
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
        # TODO: Replace with structural pattern matching in python 3.10
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

        player, league = self.capitalize_username(player)

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
            raise StatsError(player=None, stat=stat)
        if league != "all":
            try:
                league = leagues[league.lower()]
            except:
                return f"Could not understand league {league}."

        compound_stats = {
            'Winning %': ['Games Won', 'Games Played'],
            'Shooting %': ['Goals', 'Shots'],
            'Shooting % Against': ['Goals Against', 'Shots Against'],
            'Points': ['Goals', 'Assists'],
            'MVP Rate': ['MVPs', 'Games Won'],
            '% Time Slow': ['Time Slow', 'Time Boost', 'Time Supersonic'],
            '% Time Boost': ['Time Slow', 'Time Boost', 'Time Supersonic'],
            '% Time Supersonic': ['Time Slow', 'Time Boost', 'Time Supersonic'],
            '% Time Ground': ['Time Ground', 'Time Low Air', 'Time High Air'],
            '% Time Low Air': ['Time Ground', 'Time Low Air', 'Time High Air'],
            '% Time High Air': ['Time Ground', 'Time Low Air', 'Time High Air'],
            '% Most Back': ['Time Most Back', 'Time Defensive Half', 'Time Offensive Half'],
            '% Most Forward': ['Time Most Forward', 'Time Defensive Half', 'Time Offensive Half'],
            '% Goals Responsible': ['Conceded When Last', 'Goals Against'],
            'Position Ratio': ['Time Infront Ball', 'Time Behind Ball'],
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
            if stat not in valid_stats and stat not in compound_stats.keys() and stat != 'Mvp Rate':
                raise InvalidStatError(stat)
            else:
                stat = stat.title()
                if stat == 'Mvp Rate':
                    stat = 'MVP Rate'

            players = self.session.players
            data = pd.Series(name=stat, dtype=float)

            if stat not in compound_stats.keys():
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
                necessary = compound_stats[stat]
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
                    elif stat == 'Shooting % Against':
                        datapoint = round((info['stats']['general']['Goals Against'] / info['stats']['general']['Shots Against']), 2)
                    elif stat == 'Points':
                        datapoint = round((info['stats']['general']['Goals'] + info['stats']['general']['Assists']), 2)
                        if pergame:
                            datapoint = round((datapoint / info['stats']['general']['Games Played']), 2)
                    elif stat == 'MVP Rate':
                        datapoint = round(info['stats']['general']['MVPs'] / info['stats']['general']['Games Won'], 2)
                    elif stat == '% Time Slow':
                        datapoint = round(
                            info['stats']['movement']['Time Slow'] / (info['stats']['movement']['Time Slow'] + info['stats']['movement']['Time Boost'] + info['stats']['movement']['Time Supersonic'])
                        , 2)
                    elif stat == '% Time Boost':
                        datapoint = round(
                            info['stats']['movement']['Time Boost'] / (info['stats']['movement']['Time Slow'] + info['stats']['movement']['Time Boost'] + info['stats']['movement']['Time Supersonic'])
                        , 2)
                    elif stat == '% Time Supersonic':
                        datapoint = round(
                            info['stats']['movement']['Time Boost'] / (info['stats']['movement']['Time Slow'] + info['stats']['movement']['Time Boost'] + info['stats']['movement']['Time Supersonic'])
                        , 2)
                    elif stat == '% Time Ground':
                        datapoint = round(
                            info['stats']['movement']['Time Ground'] / (info['stats']['movement']['Time Ground'] + info['stats']['movement']['Time Low Air'] + info['stats']['movement']['Time High Air'])
                        , 2)
                    elif stat == '% Time Low Air':
                        datapoint = round(
                            info['stats']['movement']['Time Low Air'] / (info['stats']['movement']['Time Ground'] + info['stats']['movement']['Time Low Air'] + info['stats']['movement']['Time High Air'])
                        , 2)
                    elif stat == '% Time High Air':
                        datapoint = round(
                            info['stats']['movement']['Time High Air'] / (info['stats']['movement']['Time Ground'] + info['stats']['movement']['Time Low Air'] + info['stats']['movement']['Time High Air'])
                        , 2)
                    elif stat == '% Most Back':
                        datapoint = round(
                            info['stats']['positioning']['Time Most Back'] / (info['stats']['positioning']['Time Defensive Half'] + info['stats']['positioning']['Time Offensive Half'])
                        , 2)
                    elif stat == '% Most Forward':
                        datapoint = round(
                            info['stats']['positioning']['Time Most Forward'] / (info['stats']['positioning']['Time Defensive Half'] + info['stats']['positioning']['Time Offensive Half'])
                        , 2)
                    elif stat == '% Goals Responsible':
                        datapoint = round(info['stats']['positioning']['Conceded When Last'] / info['stats']['general']['Goals Against'], 2)
                    elif stat == 'Position Ratio':
                        datapoint = round(info['stats']['positioning']['Time Infront Ball'] / info['stats']['positioning']['Time Behind Ball'], 2)
                    
                    data[info['username']] = datapoint
                
                return data.sort_values(ascending=asc).head(limit)

        return lb.sort_values(ascending=asc).head(limit)

    def get_me(self, discord_id: str) -> str:
        ids = self.p4sheet.to_df(
            'Trackers!A1:B').set_index('Discord ID')
        try: 
            player = ids.loc[discord_id, 'Username']
            if type(player) == pd.core.series.Series:
                player = player[0]
        except:
            raise FindMeError(discord_id)
        
        return player

    def gdstats(self, player: str, day: int = None, stat: str = None, pergame: bool = False) -> pd.DataFrame:
        if day == None:
            day = get_latest_gameday()
            
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

    def teamstats(self, team: str = None, league: str = None) -> pd.DataFrame:
        if team != None:
            team = team.title()
            roster = self.teams.get_roster(team)
            league = self.identifier.find_league(team)
        elif league != None:
            league = leagues[league.lower()]

        sheet: Sheet
        if league in ['Major', 'AAA', 'AA', 'A']:
            sheet = self.p4sheet
        elif league in ['Independent', 'Maverick', 'Renegade', 'Paladin']:
            sheet = self.indysheet
        else:
            raise LeagueNotFoundError(team)

        if not team:
            stats = sheet.to_df(f"{league} Stats!D5:Q9").set_index("")
            stats = stats.append(sheet.to_df(f"{league} Stats!D12:Q16").set_index(""))
            stats = stats.append(sheet.to_df(f"{league} Stats!D20:Q24").set_index(""))
            stats = stats.append(sheet.to_df(f"{league} Stats!D27:Q31").set_index(""))
            stats.rename(columns={
                'Record (Div Record)': 'Record',
                'Forfeits': "FFs", 
                'W/L Streak': 'Streak',
                'Winning %': 'Win %',
                'Goals | PG': 'Goals',
                'Assists | PG': 'Assists',
                'Saves | PG': 'Saves',
                'Shots | PG': 'Shots',
                r'%Goals Assisted': 'Assist %',
                'Shooting %': 'Shot %',
                'GA | PG': 'GA',
                'Shots Agnst  | PG': 'SA',
                'Opp Shooting %': 'Opp Shot %'
                }, inplace=True)
            return stats

        else:
            stats = pd.DataFrame()
            for player in roster:
                stats = stats.append(self.get_player_stats_sheet(player))
            
            stats.rename(columns={
                'Series Played': 'Series',
                'Games Played': 'Games',
                'Points (Goals+Assists)': 'Points',
                'Goals per game': 'GPG',
                'Assists per game': 'APG',
                'Saves per game': 'SPG',
                'Shooting %': 'Shot %',
                'Winning %': 'Win %',
                'Points per Game': 'PPG',
                'Shots Per Game': 'ShPG'
            }, inplace=True)

            return stats.set_index('Player')

    def difference(self, player: str, stat: str) -> List[float]:
        stat = stat.title()
        if stat not in valid_stats:
            raise InvalidStatError(stat)
        day = get_latest_gameday()

        player_info = self.session.players.find_one({'$text': {'$search': f"\"{player}\""}})
        if player_info == None:
            raise PlayerNotFoundError(player, 0)
        else:
            total_stat = player_info['stats'][findCategory(stat)][stat]
            games_played = player_info['stats']['general']['Games Played']
            total_stat /= games_played

        while day > 0:
            try:
                recent_stat = self.gdstats(player, day, stat, pergame=True).loc[stat.title()]
                break
            except PlayerNotFoundError:
                day -= 1
                continue
        
        if day == 0:
            # Raise error if player has no stats on gdstats sheet
            raise PlayerNotFoundError(player, 0)

        if recent_stat == 0:
            diff = -1
        elif total_stat == 0:
            raise ZeroError()
        else:
            diff = (recent_stat - total_stat) / total_stat

        return (diff, total_stat, recent_stat)





if __name__ == "__main__":
    StatsHandler().difference("four", "assists")