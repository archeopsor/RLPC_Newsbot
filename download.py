from selenium import webdriver
import time
import geckodriver_autoinstaller

# To prevent download dialog
profile = webdriver.FirefoxProfile()
profile.set_preference('browser.download.folderList', 2) # custom location
profile.set_preference('browser.download.manager.showWhenStarting', False)
profile.set_preference('browser.download.dir', '/tmp')
profile.set_preference('browser.helperApps.neverAsk.saveToDisk', 'application/octet-stream, application/zip')

browser = webdriver.Firefox(profile, executable_path=r'C:\Users\Owner\RLPC News\geckodriver.exe')
browser.get("https://rlpcgamelogs.com/")

browser.find_element_by_xpath("/html/body/app-root/div/app-main/div/div[1]/div[4]").click()
browser.find_element_by_xpath("/html/body/app-root/div/app-main/div/div[2]/div[1]").click()
browser.find_element_by_xpath("/html/body/app-root/div/app-main/div/app-logs-status/div/div[2]/p-dropdown/div/label").click()

date = 1
while True:
    try: # This should only work for the first gameday
        browser.find_element_by_xpath("/html/body/app-root/div/app-main/div/app-logs-status/div/div[2]/p-dropdown[1]/div/div[4]/div/ul/li").click()
        break
    except: # Do this on every other gameday to find the most recent row in the date table
        try:
            browser.find_element_by_xpath(f"/html/body/app-root/div/app-main/div/app-logs-status/div/div[2]/p-dropdown[1]/div/div[4]/div/ul/li[{date}]")
            date += 1
        except:
            browser.find_element_by_xpath(f"/html/body/app-root/div/app-main/div/app-logs-status/div/div[2]/p-dropdown[1]/div/div[4]/div/ul/li[{date-1}]").click()
            break

for i in range(4): # Does the below for each of Major, AAA, AA, and A
    league = i + 1
    browser.find_element_by_xpath("/html/body/app-root/div/app-main/div/app-logs-status/div/div[2]/p-dropdown[2]/div/label").click()
    browser.find_element_by_xpath(f"/html/body/app-root/div/app-main/div/app-logs-status/div/div[2]/p-dropdown[2]/div/div[4]/div/ul/li[{league}]").click()
    num = 2
    while True: # Goes through the table and keeps downloading replays until it doesn't work, then stop
        try:
            browser.find_element_by_xpath(f"/html/body/app-root/div/app-main/div/app-logs-status/div/div[3]/table/tbody/tr[{num}]/td[7]/div").click()
            num += 1
        except:
            break
    time.sleep(10)
        
browser.quit()

import os
import psutil
process = psutil.Process(os.getpid())
print(process.memory_info().rss)  # in bytes 