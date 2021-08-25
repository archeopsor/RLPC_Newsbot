from settings import prefix

fantasy_help_text = f"""
Welcome to RLPC Fantasy! This is a just-for-fun fantasy league in which people can build a team of RLPC players and compete against other fantasy teams.
**To get started, type {prefix}new to create a new fantasy account.**

**__RULES/STRUCTURE__**
 - Each fantasy team has 5 players
 - You can pick up players at any time EXCEPT for Tuesdays and Thursdays (Gamedays)
     - You may also be prevented from picking players on Wednesday or Friday morning if points haven't been calculated yet
 - Points are calculated after every gameday (Wednesday/Friday)
 - Each team can do 2 transfers (replacing one player with another player) every week. Filling an empty slot doesn't add to this counter, but dropping a player does.
 - Each player is given a specific "salary" based on their mmr and team. The total salary value of a fantasy team must be below 700 at all times.

**__FANTASY COMMANDS__**

**{prefix}fantasy** - Shows this message
**{prefix}new** - Creates a fantasy team linked to your discord account.
    *Example: {prefix}new*
**{prefix}team** - Shows the current fantasy team of any fantasy player. Not specifying a player will show your own team
    *Example: {prefix}team arco*
**{prefix}info** - Gives important information about a player, such as their salary and a variety of stats.
    *Example: {prefix}info arco*
**{prefix}pick** - Adds a player to your fantasy team, in one of 5 player slots. Please specify which player you want.
    *Example: {prefix}pick arco*
**{prefix}drop** - Drops the specified player, replacing them with 'Not Picked'.
    *Example: {prefix}drop arco*
**{prefix}lb** - Displays the current leaderboard of points
**{prefix}search**- Searches for 5 random players fiting specified parameters
    *Example: {prefix}search name: arco min: 100 max: 160 league: AA team: all strictness: 0.8*
    *Note: Searching for a team of "signed" or "playing" will exclude Free Agents*
**{prefix}players** - Shows a leaderboard of players based on the fantasy points they have earned since the start of the season.
    *Example: {prefix}players major*
        """