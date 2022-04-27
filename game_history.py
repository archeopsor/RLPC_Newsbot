from tools.sheet import Sheet


# Processing data from each sheet in order to get as many historical RLPC series as possible
# Want the team names, series score, and players on each team/score of each game in the series 

# For seasons without gamelogs but the schedule is available, it's assumed that all four players on a team play all the games, and each game is a 1-0 win

def season2():
    s2_sheet = Sheet('1fjXBT93zTRSHSWnG01G7Q1EAxIeXOiftGHfNAqU09a4')
    games = []

    # Get Major players on each team
    major_players = s2_sheet.to_df('Major League Player Sheet !A4:K51')
    for row in major_players.index:
        if major_players.loc[row, "Team Name"] == "":
            major_players.loc[row, "Team Name"] = major_players.loc[row-1, "Team Name"]
    major_players['Team Name'] = major_players['Team Name'].str.strip()
    major_players = major_players.loc[(major_players['Gamertag'] != '') & (major_players['ODC Confirmed'] != "Coach") & (major_players['Sub'] != "Yes")]
    major_players['MMR'] = major_players['MMR'].str.replace(',', '').astype(int)
    major_players = major_players.loc[major_players['MMR'] > 805]

    # Get Major schedule
    major_schedule = s2_sheet.to_df('Major League Schedule!A3:D102')
    major_schedule = major_schedule.loc[major_schedule['Score'].str.len() == 3]
    major_schedule['Winner'] = major_schedule['Winner'].str.strip()
    major_schedule['Teams Playing'] = major_schedule['Teams Playing'].str.strip()

    for i in major_schedule.index:
        row = major_schedule.loc[i]
        teams = row['Teams Playing'].split(' vs. ')
        if i == 2:
            teams = row['Teams Playing'].split(' vs ') # Annoying misspelling
        game_3 = row['Score'][-1] == 1
        winner = row['Winner']
        loser = teams[1] if teams[0] == row['Winner'] else teams[0]

        series = {
            'league': 'major',
            'teams': teams,
            'score': {winner: 2, loser: 1 if game_3 else 0},
            'games': [],
        }

        # Games 1 and 2 are the winner's wins
        series['games'].append({
            'winner': winner,
            teams[0]: {
                'players': list(major_players.loc[major_players['Team Name']==teams[0], 'Gamertag'].values),
                'goals': 1 if winner == teams[0] else 0
            },
            teams[1]: {
                'players': list(major_players.loc[major_players['Team Name']==teams[1], 'Gamertag'].values),
                'goals': 1 if winner == teams[1] else 0
            }
        })

        # Do this again for game 2
        series['games'].append({
            'winner': winner,
            teams[0]: {
                'players': list(major_players.loc[major_players['Team Name']==teams[0], 'Gamertag'].values),
                'goals': 1 if winner == teams[0] else 0
            },
            teams[1]: {
                'players': list(major_players.loc[major_players['Team Name']==teams[1], 'Gamertag'].values),
                'goals': 1 if winner == teams[1] else 0
            }
        })

        # Add the loser's game if it went to game 3
        if game_3:
            series['games'].append({
                'winner': teams[1] if teams[0] == winner else teams[0],
                teams[0]: {
                    'players': list(major_players.loc[major_players['Team Name']==teams[0], 'Gamertag'].values),
                    'goals': 1 if winner == teams[1] else 0
                },
                teams[1]: {
                    'players': list(major_players.loc[major_players['Team Name']==teams[1], 'Gamertag'].values),
                    'goals': 1 if winner == teams[0] else 0
                }
            })

        games.append(series)

    # Get Minor players on each team
    minor_players = s2_sheet.to_df('Minor League Player Sheet!A4:K51')
    for row in minor_players.index:
        if minor_players.loc[row, "Team Name"] == "":
            minor_players.loc[row, "Team Name"] = minor_players.loc[row-1, "Team Name"]
    minor_players['Team Name'] = minor_players['Team Name'].str.strip()
    minor_players = minor_players.loc[(minor_players['Gamertag'] != '') & (minor_players['ODC Confirmed'] != "Coach") & (minor_players['Sub'] != "Yes")]
    minor_players['MMR'] = minor_players['MMR'].str.replace(',', '').astype(int)

    # Get Minor schedule
    minor_schedule = s2_sheet.to_df('Minor League Schedule!A3:D102')
    minor_schedule = minor_schedule.loc[minor_schedule['Score'].str.len() == 3]
    minor_schedule['Winner'] = minor_schedule['Winner'].str.strip()
    minor_schedule['Teams Playing'] = minor_schedule['Teams Playing'].str.strip()

    for i in minor_schedule.index:
        row = minor_schedule.loc[i]
        teams = row['Teams Playing'].split(' vs. ')
        if '.' not in row['Teams Playing']:
            teams = row['Teams Playing'].split(' vs ') # Annoying misspelling
        game_3 = row['Score'][-1] == 1
        winner = row['Winner']
        loser = teams[1] if teams[0] == row['Winner'] else teams[0]

        series = {
            'league': 'minor',
            'teams': teams,
            'score': {winner: 2, loser: 1 if game_3 else 0},
            'games': [],
        }

        # Games 1 and 2 are the winner's wins
        series['games'].append({
            'winner': winner,
            teams[0]: {
                'players': list(minor_players.loc[minor_players['Team Name']==teams[0], 'Gamertag'].values),
                'goals': 1 if winner == teams[0] else 0
            },
            teams[1]: {
                'players': list(minor_players.loc[minor_players['Team Name']==teams[1], 'Gamertag'].values),
                'goals': 1 if winner == teams[1] else 0
            }
        })

        # Do this again for game 2
        series['games'].append({
            'winner': winner,
            teams[0]: {
                'players': list(minor_players.loc[minor_players['Team Name']==teams[0], 'Gamertag'].values),
                'goals': 1 if winner == teams[0] else 0
            },
            teams[1]: {
                'players': list(minor_players.loc[minor_players['Team Name']==teams[1], 'Gamertag'].values),
                'goals': 1 if winner == teams[1] else 0
            }
        })

        # Add the loser's game if it went to game 3
        if game_3:
            series['games'].append({
                'winner': teams[1] if teams[0] == winner else teams[0],
                teams[0]: {
                    'players': list(minor_players.loc[minor_players['Team Name']==teams[0], 'Gamertag'].values),
                    'goals': 1 if winner == teams[1] else 0
                },
                teams[1]: {
                    'players': list(minor_players.loc[minor_players['Team Name']==teams[1], 'Gamertag'].values),
                    'goals': 1 if winner == teams[0] else 0
                }
            })

        games.append(series)

    return games


if __name__ == '__main__':
    print(season2())