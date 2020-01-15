from datetime import datetime
import Google_Sheets as sheet

reset_executed = False

while True:

    today_day = datetime.today().weekday()
    today_hour = int(str(datetime.now().time())[:2])
    
    # Reset every Monday at 12:00 am (Midnight)
    if reset_executed == False and today_day == 0 and today_hour == 0:
        
        # This will be turned back to false at 1:00 am
        
        reset_executed = True
        
        gsheet = sheet.get_google_sheet(sheet.SPREADSHEET_ID,"Fantasy Players!H2:H")
        rows = gsheet['values']
        
        for i in range(len(rows)):
            
            cell = f'Fantasy Players!H{i+2}'
            sheet.update_cell(sheet.SPREADSHEET_ID, cell, 2)
    
    if reset_executed == True and today_day == 0 and today_hour == 1:
        reset_executed = False
    
    