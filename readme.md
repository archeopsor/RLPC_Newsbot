# RLPC Newsbot
Discord bot for [RLPC](https://discord.gg/BUDpvq7egk) and the [RLPC News](https://discord.gg/2SU3zVVAtz) server, with a variety of purposes for enhancing the league experience. 

## Fantasy

Runs a fantasy league where participants can pick teams of five RLPC Players under a salary cap. Players are awarded points based on their performance in each series. All stats from these replays are stored in a mongodb collection.

---
## Stats

Allows discord users to get anyone's stats from the RLPC Spreadsheet or from the fantasy database. Additionally supports getting power rankings and specific stats from a given gameday.

---
## Elo

An internal elo system is used to rank teams in each league and create a Monte-Carlo forecast that's run every wednesday and friday.

---
## Reddit

Can retreive reddit posts from the [RLPC Subreddit ](https://www.reddit.com/r/RLPC)

---
## Misc

Schedules and Rosters can be retreived from the [RLPC Spreadsheet](https://docs.google.com/spreadsheets/d/17tPXpZACXlqrCS3gYo59C5gbZyp3oguVdjwsgWQJkcA)

***
### Sample passwords.py file structure
```
BOT_TOKEN = ''                      # Discord token
CREDS = {                           # Google service account credentials
  "type": "",
  "project_id": "",
  "private_key_id": "",
  "private_key": "",
  "client_email": "",
  "client_id": "",
  "auth_uri": "",
  "token_uri": "",
  "auth_provider_x509_cert_url": "",
  "client_x509_cert_url": ""
    }
REDDIT = {                          # Reddit account credentials
    'client_id': '', 
    'client_secret': '', 
    'username': "", 
    'password': "", 
    'user_agent': ""
    }
MONGO_URL = ""
```
Aside from a discord bot token, a google service account is needed, as well as a reddit account and mongodb connection link.