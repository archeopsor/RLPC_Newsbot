import datetime
import Google_Sheets as sheet
import fantasy_infrastructure as fantasy

today_day = datetime.datetime.today().weekday()

# RESET WEEKLY TRANSFERS 
# Do this on Friday morning only

if today_day == 4:
    gsheet = sheet.get_google_sheet(sheet.SPREADSHEET_ID,"Fantasy Players!H2:H")
    rows = gsheet['values']
    
    for i in range(len(rows)):
        cell = f'Fantasy Players!H{i+2}'
        sheet.update_cell(sheet.SPREADSHEET_ID, cell, 2)
    
# PARSE/UPLOAD GAME DATA
# Do this on Friday and Wednesday mornings only

if today_day == 2 or today_day == 4:
    fantasy.parse_game_data("major")
    fantasy.parse_game_data("AAA")
    fantasy.parse_game_data("AA")
    fantasy.parse_game_data("A")