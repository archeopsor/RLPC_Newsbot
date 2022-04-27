import requests
from tools.sheet import Sheet
from settings import sheet_p4

try:
    from passwords import BALLCHASING_TOKEN
except:
    from dotenv import load_dotenv
    import os
    load_dotenv(f'{os.getcwd()}\.env')
    BALLCHASING_TOKEN = os.getenv("BALLCHASING_TOKEN")


def get_players() -> list[dict]:
    """Gets all the players from the sheet and their associated ids for finding ballchasing replays

    Returns:
        list[dict]: List of {username: str, ids: list[str]} dicts each representing a unique player
    """
    sheet = Sheet(sheet_p4, refresh_cooldown=300)
    players = sheet.to_df('Players!A1:AH')
    players = players.loc[(players['Not Playing']=="FALSE") & (players['Departed']=="FALSE") & (~players['Team'].isin(['Waitlist', 'Below MMR', 'Ineligible', 'Future Star', 'Banned']) & (players['Username'] != ''))]
    players.set_index('Username', inplace=True)

    processed_players: list[dict] = []

    for player in players.index:
        trackers = players.loc[player, 'Tracker']
        ids = get_ids_from_trackers(trackers)
        processed_players.append({
            "username": player,
            "ids": ids,
        })

    return processed_players


def get_ids_from_trackers(trackers: str) -> list[str]:
    """Takes in string containing trackers (from rlpc sheet), returns list of platform:id strings.

    Args:
        trackers (str): Trackers from sheet. Format: 'tracker1, tracker2, ... trackern'

    Returns:
        list[str]: _description_
    """
    trackersList = trackers.split(',')
    ids: list[str] = []

    for tracker in trackersList:
        platform: str = tracker.split('/')[5]
        id: str = tracker.split('/')[6].replace('%20', ' ')

        if platform == 'xbl':
            # Don't have xbox ids, so just need to use their name
            ids.append(id)
        elif platform == 'psn':
            # All playstation players have 'ps4' tag
            ids.append('ps4:' + id)
        else:
            # Normal {platform}:{id} format for steam and epic ids
            ids.append(platform + ':' + id)

    return ids


def get_replays(player_id: str) -> dict:
    """Gets all the replays from ballchasing that were uploaded by arco and contain this player, which should all be RLPC replays.

    Args:
        playerId (str): id as found in get_ids_from_trackers()

    Returns:
        dict: list of all the replays and their various metadata (id is the important one for each replay)
    """
    params = {
        "player-name": player_id,
        "uploader": "76561198157223906", # Could also maybe just use 'me'
        "playlist": "private",
    }

    headers = {
        'Content-Type': 'application/json',
        'Authorization': BALLCHASING_TOKEN,
    }

    r = requests.get("https://ballchasing.com/api/replays", params=params, headers=headers)

    return r.json()


def get_replay_stats(replay_id: str) -> dict:
    pass


if __name__ == '__main__':
    print(get_replays(get_players()[0]['ids']))
