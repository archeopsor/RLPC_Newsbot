import pandas as pd
import Google_Sheets as sheet

sheet_id = sheet.SPREADSHEET_ID
gsheet = sheet.get_google_sheet(sheet_id, 'Player Info!A1:W')

def get_player_stats(player,stat="all"):
    all_player_stats = sheet.gsheet2df(gsheet)
    if stat not in list(all_player_stats):
        return("That stat could not be understood.")
    all_player_stats = all_player_stats.loc[all_player_stats['Username']==player]
    if stat != "all":
        all_player_stats = all_player_stats.loc[all_player_stats.index[0],stat]
    return(all_player_stats)