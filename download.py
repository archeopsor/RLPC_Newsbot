from selenium import webdriver
import time
from datetime import datetime, timedelta
import pytz

from rlpc import elo

# To prevent download dialog
profile = webdriver.FirefoxProfile()
profile.set_preference('browser.download.folderList', 2) # custom location
profile.set_preference('browser.download.manager.showWhenStarting', False)
profile.set_preference('browser.download.dir', '/tmp')
profile.set_preference('browser.helperApps.neverAsk.saveToDisk', 'application/octet-stream, application/zip')

browser = webdriver.Firefox(profile, executable_path=r'C:\Users\Simi\Documents\geckodriver.exe')
browser.get("https://rlpcgamelogs.com/")

browser.find_element_by_xpath("/html/body/app-root/div/app-main/div/div[1]/div[4]").click() # Click "Status" tab
time.sleep(3)
browser.find_element_by_xpath("/html/body/app-root/div/app-main/div/div[2]/div[1]").click() # Click "Logs" tab
time.sleep(3)
browser.find_element_by_xpath("/html/body/app-root/div/app-main/div/app-logs-status/div/div[2]/p-dropdown/div/label").click()
time.sleep(3)

dates = browser.find_elements_by_xpath('/html/body/app-root/div/app-main/div/app-logs-status/div/div[2]/p-dropdown[1]/div/div[4]/div/ul/li')
target_date = datetime.now(tz=pytz.timezone("US/Eastern")) - timedelta(days=1)
for date in dates[::-1]:
    if date.text == target_date.strftime('%m/%d/%Y'): # Click the date for yesterday
        date.click()
        break
time.sleep(3)

browser.find_element_by_xpath('/html/body/app-root/div/app-main/div/app-logs-status/div/div[2]/p-dropdown[2]/div/label').click() # Click "League" tab
time.sleep(3)
leagues = browser.find_elements_by_xpath('/html/body/app-root/div/app-main/div/app-logs-status/div/div[2]/p-dropdown[2]/div/div[4]/div/ul/li')

scores = ""

for i in range(1, len(leagues)+1): # Does the below for every league that shows up on the website
    browser.find_element_by_xpath('/html/body/app-root/div/app-main/div/app-logs-status/div/div[2]/p-dropdown[2]/div/label').click() # Click "League" tab
    time.sleep(3)
    try:
        browser.find_element_by_xpath(f'/html/body/app-root/div/app-main/div/app-logs-status/div/div[2]/p-dropdown[2]/div/div[4]/div/ul/li[{i}]').click() # Click appropriate league on drop-down list
    except:
        browser.find_element_by_xpath('/html/body/app-root/div/app-main/div/app-logs-status/div/div[2]/p-dropdown[2]/div/label').click() # Click "League" tab
        browser.find_element_by_xpath(f'/html/body/app-root/div/app-main/div/app-logs-status/div/div[2]/p-dropdown[2]/div/div[4]/div/ul/li[{i}]').click() # Click appropriate league on drop-down list
    
    table = browser.find_elements_by_xpath('/html/body/app-root/div/app-main/div/app-logs-status/div/div[3]/table/tbody/tr')
    for row in table:
        if row.text == 'Team Team Deadline Passed': # Logs not submitted table
            continue
        
        winner = row.find_element_by_xpath('td[1]').text
        
        if winner == 'Winning Team': # First row of the table
            continue
        
        winnerScore = row.find_element_by_xpath('td[2]').text
        loser = row.find_element_by_xpath('td[3]').text
        try: 
            loserScore = row.find_element_by_xpath('td[4]').text
        except:
            continue
        
        if winnerScore == 'FF' or loserScore == 'FF':
            continue
        
        try:
            row.find_element_by_xpath('td[7]/div').click() # Download logs
        except:
            pass # If no logs are available
        
        score = f'{winner} {winnerScore}-{loserScore} {loser}'
        if scores != '': # Add new line if this isn't the first score being added
            scores += '\n'
        scores += score
        
    time.sleep(13)

elo.autoparse(scores)

browser.quit()