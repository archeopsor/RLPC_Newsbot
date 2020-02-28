import Google_Sheets as sheet
import pandas as pd
import RLPC_ELO as elo
from datetime import datetime
import time
import editdistance

prefix = '$'

# Pulls stats from a series from the spreadsheet, and analyzes it.
def import_games(league):
    if league.casefold() == "aaa" or league.casefold() == "aa" or league.casefold() == "a":
        league = league.upper()
    sheet_range = f'{league} Gamelogs!A1:J'
    gsheet = sheet.get_google_sheet(sheet.SPREADSHEET_ID, sheet_range)
    game_data = sheet.gsheet2df(gsheet)
    
    try: 
        if game_data == None:
            game_data = []
    except: pass
    
    return game_data

# Takes in the stats from parse_game_data and distributes them to both players and fantasy teams    
def update_player_stats(league, player, series_won, series_played, games_won, games_played, goals, assists, saves, shots):
    game_points = goals + assists
    
    # Import current stats data
    gsheet = sheet.get_google_sheet(sheet.SPREADSHEET_ID, 'Player Info!A1:I')
    current_stats = sheet.gsheet2df(gsheet)
    current_stats = current_stats.set_index('Username')
    
    # FANTASY POINTS FORMULA BELOW
    points = 0
    points += (series_won*15)
    points += (games_won*5)
    points += (goals*15)
    points += (assists*10)
    points += (saves*5)
    points += (shots*5)
    
    # Add fantasy points to accounts
    sheet_id = sheet.SPREADSHEET_ID
    sheet_range = "Fantasy Players!A1:O"
    gsheet2 = sheet.get_google_sheet(sheet_id, sheet_range)
    fantasy_players = sheet.gsheet2df(gsheet2)
    
    for row in fantasy_players.index:
        if player == fantasy_players.iloc[row,2]:
            current_slot_points = int(fantasy_players.iloc[row,9])
            new_slot_points = current_slot_points + points
            sheet.update_cell(sheet_id, f'Fantasy Players!J{row+2}', new_slot_points)
        elif player == fantasy_players.iloc[row,3]:
            current_slot_points = int(fantasy_players.iloc[row,10])
            new_slot_points = current_slot_points + points
            sheet.update_cell(sheet_id, f'Fantasy Players!K{row+2}', new_slot_points)
        elif player == fantasy_players.iloc[row,4]:
            current_slot_points = int(fantasy_players.iloc[row,11])
            new_slot_points = current_slot_points + points
            sheet.update_cell(sheet_id, f'Fantasy Players!L{row+2}', new_slot_points)
        elif player == fantasy_players.iloc[row,5]:
            current_slot_points = int(fantasy_players.iloc[row,12])
            new_slot_points = current_slot_points + points
            sheet.update_cell(sheet_id, f'Fantasy Players!M{row+2}', new_slot_points)
        elif player == fantasy_players.iloc[row,6]:
            current_slot_points = int(fantasy_players.iloc[row,13])
            new_slot_points = current_slot_points + points
            sheet.update_cell(sheet_id, f'Fantasy Players!N{row+2}', new_slot_points)
        else:
            pass
    
    # Updating Fantasy Points in spreadsheet
    points = float(current_stats.loc[player, 'Fantasy Points']) + float(points)
    
    # Pushing total stats to spreadsheet
    current_stats = current_stats.reset_index()
    player_row = current_stats.loc[current_stats['Username']==player].index[0] + 2
    sheet.update_cell(sheet_id, f'Player Info!I{player_row}',points)
    
def parse_game_data(league):
    league = league.title()
    if league.casefold() == "aaa" or league.casefold() == "aa" or league.casefold() == "a":
        league = league.upper()
    total_games_data = import_games(league)
    
    if len(total_games_data) == 0:
        return(f"There were no games available for {league} league")
    
    T1_P1 = total_games_data.iat[0,2]
    T1_P2 = total_games_data.iat[1,2]
    T1_P3 = total_games_data.iat[2,2]
    T2_P1 = total_games_data.iat[3,2]
    T2_P2 = total_games_data.iat[4,2]
    T2_P3 = total_games_data.iat[5,2]
    stats = {'Player':[T1_P1,T1_P2,T1_P3,T2_P1,T2_P2,T2_P3], 'Series Won':[0,0,0,0,0,0], 'Series Played':[0,0,0,0,0,0], 'Games Won':[0,0,0,0,0,0], 'Games Played':[0,0,0,0,0,0], 'Goals':[0,0,0,0,0,0], 'Assists':[0,0,0,0,0,0], 'Saves':[0,0,0,0,0,0], 'Shots':[0,0,0,0,0,0]}
    game_stats = pd.DataFrame(data = stats).set_index('Player')
    
    # This uses one procedure for each individual series, and keeps repeating until there are no series left in the total_games_data dataframe
        
    while len(total_games_data)>0:
    
        # Gathering information to add to a dataframe for a game in the spreadsheet
        
        series_length = int(total_games_data.iat[0,4])*6
        game_data = total_games_data.head(series_length)
        game_winner = None
        game_loser = None
        if int(game_data.iat[0,5]) == 3 or int(game_data.iat[1,5]) == 3 or int(game_data.iat[2,5]) == 3:
            game_winner = game_data.iat[0,1]
            game_loser = game_data.iat[3,1]
        elif int(game_data.iat[3,5]) == 3 or int(game_data.iat[4,5]) == 3 or int(game_data.iat[5,5]) == 3:
            game_winner = game_data.iat[3,1]
            game_loser = game_data.iat[0,1]
        else:
            return "Error: Winner couldn't be found"
        
        # Game Data/Stats
        
        # Adding stats to gameday dataframe, called "game_stats"
        
        for row in game_data.index:
            player = game_data.loc[row, 'Player']
            if player != "Sub":
                if (True in game_stats.index.isin([player])) == False:
                    game_stats.loc[player] = {'Series Won':0, 'Series Played':0, 'Games Won':0, 'Games Played':0, 'Goals':0, 'Assists':0, 'Saves':0, 'Shots':0}
                if game_data.loc[row, 'Team'] == game_winner:
                    game_stats.loc[player, 'Series Won'] = int(game_data.loc[row, 'Series']) + int(game_stats.loc[player, 'Series Won'])
                game_stats.loc[player, 'Series Played'] = int(game_data.loc[row, 'Series']) + int(game_stats.loc[player, 'Series Played'])
                game_stats.loc[player, 'Games Won'] = int(game_data.loc[row, 'Games Won']) + int(game_stats.loc[player, 'Games Won'])
                game_stats.loc[player, 'Games Played'] = int(game_data.loc[row, 'Total Games']) + int(game_stats.loc[player, 'Games Played'])
                game_stats.loc[player, 'Goals'] = int(game_data.loc[row, 'Goals']) + int(game_stats.loc[player, 'Goals'])
                game_stats.loc[player, 'Assists'] = int(game_data.loc[row, 'Assists']) + int(game_stats.loc[player, 'Assists'])
                game_stats.loc[player, 'Saves'] = int(game_data.loc[row, 'Saves']) + int(game_stats.loc[player, 'Saves'])
                game_stats.loc[player, 'Shots'] = int(game_data.loc[row, 'Shots']) + int(game_stats.loc[player, 'Shots'])
                
                series_won = 0
                if game_data.loc[row, 'Team'] == game_winner: series_won = series_won + int(game_data.loc[row, 'Series']) 
                series_played = int(game_data.loc[row, 'Series'])
                games_won = int(game_data.loc[row, 'Games Won'])
                games_played = int(game_data.loc[row, 'Total Games'])
                goals = int(game_data.loc[row, 'Goals'])
                assists = int(game_data.loc[row, 'Assists'])
                saves = int(game_data.loc[row, 'Saves'])
                shots = int(game_data.loc[row, 'Shots'])
                
                # Trying not to overload Sheets API
                time.sleep(50)
                
                update_player_stats(league,player,series_won,series_played,games_won,games_played,goals,assists,saves,shots)
            
            else: pass
            
        total_games_data = total_games_data.iloc[series_length:]
        
        # Update ELO with this game's result
        
        score = f"3 - {series_length-3}"        
        elo.add_games_manual(league, game_winner, game_loser, game_winner, score)
        elo.save_data()
        
    return(game_stats)
    
# Create a leaderboard of all fantasy accounts, and return it sorted by total points
def generate_leaderboard():
    gsheet = sheet.get_google_sheet(sheet.SPREADSHEET_ID,'Fantasy Players!A1:O')
    fantasy_players = sheet.gsheet2df(gsheet)
    fantasy_players = fantasy_players[['Username','Total Points']]
    fantasy_players['Total Points'] = fantasy_players['Total Points'].map(lambda a: int(a))
    lb = fantasy_players.sort_values(by=['Total Points'],ascending=False)
    lb = lb.reset_index(drop=True)
    return(lb)

# Creates an account for someone who wants to play, and sets their team of 5 all to "Not Picked"
def add_fantasy_player(person, league):
    if league.casefold() not in ["major","aaa","aa","a","none"]:
        return(f"{league} could not be understood")
    
    if league.casefold() == "major" or league.casefold() == "none":
        league = league.title()
    else:
        league = league.upper()
    
    sheet_id = sheet.SPREADSHEET_ID
    sheet_range = "Fantasy Players!A1:N"
    
    gsheet = sheet.get_google_sheet(sheet_id, sheet_range)
    players = sheet.gsheet2df(gsheet)
    
    player_check = players[players['Username']==person].index.values
    
    if len(player_check)!=0:
        return "You already have an account!"
    
    values = [[person],[league],["Not Picked"],["Not Picked"],["Not Picked"],["Not Picked"],["Not Picked"],[10],[0],[0],[0],[0],[0],[0]]
    body = {"majorDimension": "COLUMNS", 'values': values}
    
    sheet.append_data(sheet_id, sheet_range, body, "OVERWRITE")
    
    return f"Success! Your account has been created, with an ID of {person}. To add players, use {prefix}pick" 
    
# Adding an RLPC player to the player database
def add_rlpc_player(username, mmr, team, league):
    sheet_id = sheet.SPREADSHEET_ID
    sheet_range = "Player Info!A1:D"
    
    values = [[username], [mmr], [team], [league]]
    body = {"majorDimension": "COLUMNS", 'values': values}
    
    sheet.append_data(sheet_id, sheet_range, body, "OVERWRITE")
 
# Picks a player to be added to an account
def pick_player(person,player,slot=0):
    
    if slot not in [0, 1, 2, 3, 4, 5]:
        return("Please pick a slot between 1 and 5.")
    
    # Don't allow transfers on Tuesday or Thursday
    if datetime.today().weekday() in [1,3]:
        return("You are not allowed to make transfers on game days!")
    
    sheet_id = sheet.SPREADSHEET_ID
    sheet_range = "Fantasy Players!A1:P"
    
    gsheet = sheet.get_google_sheet(sheet_id, sheet_range)
    fantasy_players = sheet.gsheet2df(gsheet)
    
    gsheet2 = sheet.get_google_sheet(sheet_id,"Player Info!A1:I")
    rlpc_players = sheet.gsheet2df(gsheet2)
    lower_players = rlpc_players['Username'].str.lower()
    
    try: fantasy_players.loc[fantasy_players['Username']==person,"Player 1"]
    except: return(f"You don't currently have an account! Use {prefix}newplayer [league] to make an account")
    
    if slot == 0:
        if fantasy_players.loc[fantasy_players['Username']==person,f"Player 1"].values[0] == "Not Picked":
            slot = 1
        elif fantasy_players.loc[fantasy_players['Username']==person,f"Player 2"].values[0] == "Not Picked":
            slot = 2
        elif fantasy_players.loc[fantasy_players['Username']==person,f"Player 3"].values[0] == "Not Picked":
            slot = 3
        elif fantasy_players.loc[fantasy_players['Username']==person,f"Player 4"].values[0] == "Not Picked":
            slot = 4
        elif fantasy_players.loc[fantasy_players['Username']==person,f"Player 5"].values[0] == "Not Picked":
            slot = 5
        else: return("Please pick a slot to replace, your team is full")
    
    # If "None" is chosen, drop the player in the selected slot
    drop = False
    if player.casefold() in ["none","not picked","nobody","drop","empty"]:
        drop = True
    
    # Make it not case sensitive, and return if the player doesn't exist
    if player.casefold() in lower_players.values and drop == False:
        pindex = lower_players[lower_players == player.casefold()].index[0]
        player = rlpc_players.loc[pindex][0]
    elif drop == False:
        return("That player couldn't be found on the sheet. Make sure you spelled their name correctly")
    
    account_check = fantasy_players[fantasy_players['Username']==person].index.values
    current_occupant = fantasy_players.loc[fantasy_players['Username']==person,f"Player {slot}"].values[0]
    if drop != True:
        global player_check
        global permission_check
        global cap_check
        player_check = rlpc_players[rlpc_players['Username']==player].index.values   
        permission_check = rlpc_players.loc[rlpc_players['Username']==player,'Allowed?'].values[0]     
        cap_check = rlpc_players.loc[rlpc_players['Username']==player,'Fantasy Value'].values[0]
        cap_check = int(cap_check) + int(fantasy_players.loc[fantasy_players['Username']==person,'Salary'].values[0])
    
    # Check if this is a transfer
    transfer = False
    if current_occupant != "Not Picked" and drop != True:
        transfer = True
        global transfers_left
        transfers_left = fantasy_players.loc[fantasy_players['Username']==person,'Transfers Left'].values[0]
        transfers_left = int(transfers_left)
        
    if transfer == True and transfers_left == 0:
        return("You have already used your two transfers for this week!")
    
    # Check to make sure the account exists, the specified player exists, and they are allowed to be picked
    if len(account_check) == 0:
        return("You don't currently have an account! Use {prefix}newaccount to create an account")
    else:
        pass
    
    if drop == True:
        player_check = []
        permission_check = "Yes"
        cap_check = 0
    
    if len(player_check) == 0 and drop != True:
        return("That player isn't in the database! Make sure to enter the name exactly like it is on the sheet. If you think this is an error, please contact @arco.")
    else:
        pass
    
    if permission_check != "Yes" and drop != True:
        return("This player has requested to be excluded from the fantasy league")
    else:
        pass
    
    # Check to make sure this player isn't already on the fantasy team
    existing_check = fantasy_players.loc[fantasy_players['Username']==person]
    existing_check = existing_check[['Player 1','Player 2','Player 3','Player 4','Player 5']]
    existing_check = existing_check.values
    if player in existing_check:
        return("You already have this player on your team!")
    else:
        pass
    
    # Check to make sure it doesn't break the salary cap
    salary_cap = 800
    if cap_check > salary_cap and transfer == False:
        return(f"This player would cause you to exceed the salary cap of {salary_cap}. Please choose a different player, or drop a player by picking 'None' in the desired slot")
    elif transfer == True:
        old_player_salary = rlpc_players.loc[rlpc_players['Username']==current_occupant,'Fantasy Value'].values[0]
        cap_check = cap_check - int(old_player_salary)
        if cap_check > salary_cap:
            return(f"This player would cause you to exceed the salary cap of {salary_cap}.")
    
    if transfer == True and transfers_left > 0:
        row = account_check[0]+2
        cell = f"Fantasy Players!H{row}"
        value = transfers_left - 1
        sheet.update_cell(sheet_id,cell,value)
    
    # Create the cell address to be update in account database
    row = account_check[0]+2
    global column
    column = ""
    
    def column_set(slot=slot):
        global column
        if slot == 1:
            column = "C"
        elif slot == 2:
            column = "D"
        elif slot == 3:
            column = "E"
        elif slot == 4:
            column = "F"
        elif slot == 5:
            column = "G"
            
    column_set(slot)
    cell = f'Fantasy Players!{column}{row}'
    
    # Log the changes just in case
    timestamp = str(datetime.now())
    account = person
    player_in = player
    if drop == True:
        player_in = "DROP"
        player_out = current_occupant
    else:
        player_out = current_occupant    
    values = [[timestamp], [account], [player_in], [player_out]]
    body = {"majorDimension": "COLUMNS", 'values': values}
    sheet.append_data(sheet_id, "Transfer Logs!A1:D", body)
    
    if drop == True:
        sheet.update_cell(sheet_id,cell,"Not Picked")
        return(f'You have dropped {current_occupant}')
    
    # Check to make sure the player isn't in the same league as the account
    # if rlpc_players.loc[rlpc_players['Username']==player,'League'].values[0] == fantasy_players.loc[fantasy_players['Username']==person,'Account League'].values[0]:
    #     return("You must select a player in a league other than your own")
    # else:
    #     pass
    
    sheet.update_cell(sheet_id,cell,player)
    
    # Check to make sure the specified slot is empty, otherwise say a player was replaced
    if current_occupant == "Not Picked":
        return(f'Success! {player} has been added to your team')
    elif current_occupant != "Not Picked":
        return(f'Success! {current_occupant} has been replaced with {player}')
    else:
        return(f"You already have {fantasy_players.loc[fantasy_players['Username']==person,f'Player {slot}'].values[0]} in this slot. They have been replaced by {player}.")
    
# Display a player's team
def show_team(person):
    sheet_id = sheet.SPREADSHEET_ID
    sheet_range = 'Fantasy Players!A1:O'
    gsheet = sheet.get_google_sheet(sheet_id, sheet_range)
    fantasy_teams = sheet.gsheet2df(gsheet)
    for row in fantasy_teams.index:
        fantasy_teams.loc[row,'Username'] = fantasy_teams.loc[row,'Username'].upper()
    person = person.upper()
    fantasy_teams = fantasy_teams.set_index("Username")
    return(fantasy_teams.loc[person])

def info(player):
    sheet_id = sheet.SPREADSHEET_ID
    sheet_range = 'Player Info!A1:I'
    gsheet = sheet.get_google_sheet(sheet_id, sheet_range)
    players = sheet.gsheet2df(gsheet)
    lower_players = players['Username'].str.lower()
    if player.casefold() in lower_players.values:
        pindex = lower_players[lower_players == player.casefold()].index[0]
        player = players.loc[pindex][0]
    for row in players.index:
        players.loc[row,'Username'] = players.loc[row,'Username'].upper()
    player = player.upper()
    players = players.set_index("Username")
    return(players.loc[player])

def search(minsalary=0, maxsalary=800, league="all", team="all", name="none", maxdistance=5):
    sheet_id = sheet.SPREADSHEET_ID
    sheet_range = 'Player Info!A1:I'
    gsheet = sheet.get_google_sheet(sheet_id, sheet_range)
    players = sheet.gsheet2df(gsheet)
    players = players.sort_values(by='Username')
    players = players.reset_index(drop=True)
    
    if team.casefold() in ["all","none","no","idc"]:
        team = "all"
    if league.casefold() in ["all","none","no","idc"]:
        league = "all"
    if league.casefold() not in ['major','aaa','aa','a','all']:
        return("League could not be understood")
    if league.casefold() == "major":
        league = "Major"
    if team.casefold() not in ['all','FA']:
        team = team.title()
    
    for row in players.index:
        salary = int(players.loc[row,'Fantasy Value'])
        players.loc[row,'Fantasy Value'] = salary
    
    players = players.loc[players['Fantasy Value'] >= minsalary]
    players = players.loc[players['Fantasy Value'] <= maxsalary]
    if league != "all":
        players = players.loc[players['League'] == league]
    if team != "all":
        players = players.loc[players['Team'] == team]
        
    if len(players.index) == 0:
        return("There were no players that matched those parameters")
    
    if name == "none":
        if len(players.index) > 4:
            return(players.sample(5))
        else:
            num = len(players.index)
            return(players.sample(num))
    
    # Search names by assigning an editdistance value 
    players['editdistance'] = 0
    for row in players.index:
        username = players.loc[row,'Username']
        username = username.casefold()
        name = name.casefold()
        distance = editdistance.eval(name, username)
        length = abs(len(name)-len(username))
        players.loc[row,'editdistance'] = (distance-length)/2
    
    if name != "none":
        players = players.sort_values(by='editdistance')
        players = players.loc[players['editdistance'] <= maxdistance]
        players = players.drop('editdistance',axis=1)
        return(players.head(5))