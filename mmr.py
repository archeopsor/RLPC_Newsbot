from bs4 import BeautifulSoup
import requests
import Google_Sheets as sheet
import time
import urllib
import re

BASE_URL = 'https://rocketleague.tracker.network'
PROFILE_URL = BASE_URL + '/profile/{platform}/{username}'

def playlist(playlist, url=None, platform=None, username=None):
    if url == None:
        player = get_player(platform, username)
    else:
        player = get_player(url)
    
    duels = ['1', '1v1', '1s', 'duels', ]
    doubles = ['2', '2v2', '2s', 'doubles']
    solo_standard = ['solo', 'ss']
    standard = ['3', '3v3', '3s', 'standard']
    hoops = ['hoops', 'basketball']
    rumble = ['rumble', 'rng']
    dropshot= ['dropshot']
    snowday = ['snowday', 'hockey', 'snow day']    
    
    if any(playlist.casefold() in x for x in duels):
        playlist = 0
    elif any(playlist.casefold() in x for x in doubles):
        playlist = 1
    elif any(playlist.casefold() in x for x in solo_standard):
        playlist = 2
    elif any(playlist.casefold() in x for x in standard):
        playlist = 3
    elif any(playlist.casefold() in x for x in hoops):
        playlist = 4
    elif any(playlist.casefold() in x for x in rumble):
        playlist = 5
    elif any(playlist.casefold() in x for x in dropshot):
        playlist = 6
    elif any(playlist.casefold() in x for x in snowday):
        playlist = 7
    else:
        raise ValueError('Could not understand playlist')
    
    stats = player['games'][playlist]
    return stats

def get_player(url = None, platform = None, username = None):
    if url == None:
        url = PROFILE_URL.replace('{platform}', platform).replace('{username}', username)

    req = requests.get(url)
    soup = BeautifulSoup(req.content, 'html.parser')

    playlist = {'games': []}
    rows = get_rows(soup)

    for row in rows[1:]:
        rank_img_url = get_rank_img_url(row)
        game_type = get_game_type(row)

        div_down = get_div_down(row)
        div_up = get_div_up(row)

        rank = get_rank(row)
        rating = get_rating(row)
        top_percent = get_top_percent(row)
        games_played = get_games_played(row)

        playlist['games'].append({
            'rankImgUrl' : rank_img_url,
			'gameType' : game_type,
			'divDown' : div_down,
			'divUp' : div_up,
			'rank' : rank,
			'rating' : rating,
			'topPercent': top_percent,
			'gamesPlayed' : games_played
		})

    return playlist


def get_rank_img_url(row):
	data = row.find_all('td')[0]
	image = data.find('img')
	return BASE_URL + image['src']


def get_game_type(row):
	data = row.find_all('td')[1]
	split = data.getText().split('\n')
	return split[1]


def get_div_down(row):
	return get_div_movement(row, 2)


def get_div_up(row):
	return get_div_movement(row, 4)


def get_div_movement(row, index):
	data = row.find_all('td')[index]
	span = data.find('span')

	if span is None:
		return None
	else:
		return span.text


def get_rank(row):
	data = row.find_all('td')[1]
	split = data.getText().split('\n')
	return split[3] + " " + split[4]


def get_rating(row):
	data = row.find_all('td')[3]
	split = data.getText().split('\n')
	return split[1]


def get_top_percent(row):
	data = row.find_all('td')[3]
	split = data.getText().split('\n')
	return split[3]


def get_games_played(row):
	data = row.find_all('td')[5]
	split = data.getText().split('\n')
	return split[1]


def get_rows(soup, seasons_ago):
	season_table = soup.find_all(class_='season-table')[seasons_ago]
	playlist_table = season_table.find_all('table')[1]
	table_body = playlist_table.find('tbody')
	return table_body.find_all('tr')

def findmmrs():
    done = sheet.gsheet2df(sheet.get_google_sheet('1rmJVnfWvVe3tSnFrXpExv4XGbIN3syZO12dGBeoAf-w', 'Player Data!A1:B'))
    players = sheet.gsheet2df(sheet.get_google_sheet('1C10LolATTti0oDuW64pxDhYRLkdUxrXP0fHYBk3ZwmU', 'Players!A1:R'))
    players = players.loc[players['Tracker']!= ""]
    try: players = players.loc[~players['Username'].isin(done['Username'])]
    except: pass
    
    for i in players.index.values:
        peaks=[0]
        peaks.append(int(players.loc[i, 'Tracker MMR']))
        
        for url in players.loc[i, 'Tracker'].split(", "):
            link = url.strip()
            if 'mmr' not in link:
                text = link.split("/profile")
                link = text[0] + "/profile/mmr" + text[-1]
            
            try:
                peaks.append(getMmr(link))
            except:
                try:
                    peaks.append(max(seasonpeak(link)))
                except:
                    print(players.loc[i, 'Username']+' failed')
        
        peaks = [x for x in peaks if x != None]
        values = [[players.loc[i, 'Username']], [max(peaks)]]
        body = {'majorDimension': "COLUMNS", 'values': values}
        sheet.append_data('1rmJVnfWvVe3tSnFrXpExv4XGbIN3syZO12dGBeoAf-w', 'Player Data!A1:C', body)
        time.sleep(60)
        
        
def seasonpeak(url):
    mmrs = BeautifulSoup(requests.get(url).content, 'html.parser')
    text = mmrs.find_all(type="text/javascript")
    text = text[3].string.split('rating: ')
    doubles = list(map(int, text[3].split(']')[0][1:].split(',')))
    standard = list(map(int, text[5].split(']')[0][1:].split(',')))
    peaks = [max(doubles), max(standard)]
    return peaks

def getMmr(url):
    if 'mmr' not in url:
        text = url.split("/profile")
        url = text[0] + "/profile/mmr" + text[-1]
    
    headers = {"User-Agent": "Mozilla/5.0"}
    request = urllib.request.Request(url, headers=headers)
    resp = urllib.request.urlopen(request)
    peakMmrHtml = resp.read()

    patternString = r'data\[\'[0-9]{1,2}\'\]\s*=\s*{((?:.*?\r?\n?)*)}'
    pattern = re.compile(patternString, re.MULTILINE | re.DOTALL)

    soup = BeautifulSoup(peakMmrHtml, 'html.parser')
    text = soup.find_all(type="text/javascript", text=pattern)
    if len(text) != 1:
        return

    currentPeakMmrs = []

    for group in pattern.findall(text[0].string):
        p = re.compile(r'((Ranked Solo Standard 3v3)|(Ranked Doubles 2v2)|(Ranked Standard 3v3))+', re.MULTILINE | re.DOTALL)
        cleanGroup = group.strip()
        if len(p.findall(cleanGroup)) == 1:
            p = re.compile(r'rating:\s*\[((?:.*?\r?\n?)*)\]')
            ratingGroup = p.findall(cleanGroup)
            
            if len(ratingGroup) == 1:
                playlistPeakMmr = 0
                mmrArr = ratingGroup[0].replace('[', '').replace(']', '').replace('\'', '').split(',')
                for mmr in mmrArr:
                    try:
                        val = int(mmr)
                        if val >= playlistPeakMmr:
                            playlistPeakMmr = val
                    except ValueError:
                        pass

                currentPeakMmrs.append(playlistPeakMmr)

    #print('All playlists peaks:')
    #print(currentPeakMmrs)
    #print('Current season peak:')
    currentSeasonPeak = max(currentPeakMmrs)
    #print(currentSeasonPeak)

    # Pull from previous seasons
    url = url.replace('mmr/','')
    headers = {"User-Agent": "Mozilla/5.0"}
    request = urllib.request.Request(url, headers=headers)
    resp = urllib.request.urlopen(request)
    previousMmrHtml = resp.read()

    soup = BeautifulSoup(previousMmrHtml, 'html.parser')
    text = soup.find_all(True, attrs={'role': 'tablist', 'class': ['season-tabs']})
    if len(text) != 1:
        return

    backNumOfSeasons = 3

    previousPeakMmrs = []

    seasonNumbers = []
    seasonMap = {}
    seasonsToParse = []

    ulTag = text[0]
    liElems = ulTag.findChildren('li')

    for li in liElems:
        aElems = li.findChildren('a')
        onClick = aElems[0]['onclick']
        p = re.compile(r'\$\(\'#.*\'\).show\(\)')
        sns = p.findall(onClick)

        if len(sns) != 1:
            continue

        seasonTag = sns[0]
        seasonTag = seasonTag.replace('$(\'', '').replace('\').show()', '').replace('#', '')
        seasonNumber = int(seasonTag.split('-')[1])
        seasonNumbers.append(seasonNumber)
        seasonMap[seasonNumber] = seasonTag

    seasonNumbers.sort(reverse=True)

    count = backNumOfSeasons
    for seasonNum in seasonNumbers:
        if count == 0:
            break
        seasonsToParse.append(seasonMap[seasonNum])
        count = count - 1

    for season in seasonsToParse:
        seasonTable = soup.find(id=season)                    

        seasonPeakMmr = 0

        tableRows = seasonTable.findChildren('tr')
        for row in tableRows:
            p = re.compile(r'((Ranked Solo Standard 3v3)|(Ranked Doubles 2v2)|(Ranked Standard 3v3))+', re.MULTILINE | re.DOTALL)
            cleanRow = row.text.strip()
            if len(p.findall(cleanRow)) == 1:
                cells = row.find_all('td')
                count = 0
                for cell in cells:
                    contents = cell.contents
                    
                    if count <= 3:
                        mmr = contents[0].replace(',', '')

                        try:
                            val = int(mmr)
                            if val >= seasonPeakMmr:
                                seasonPeakMmr = val
                        except ValueError:
                            pass

                    count = count + 1

        previousPeakMmrs.append(seasonPeakMmr)

    #print('Peaks from other seasons:')
    #print(previousPeakMmrs)

    #print('Highest peak from last ' + str(backNumOfSeasons) + ' seasons:')
    previousSeasonMax = max(previousPeakMmrs)
    #print(previousSeasonMax)

    #print('Player MMR:')
    playerMmr = previousSeasonMax if previousSeasonMax > currentSeasonPeak else currentSeasonPeak
    #print(playerMmr)
    
    if playerMmr == None:
        raise Exception("No MMRs found")
    else:
        return playerMmr