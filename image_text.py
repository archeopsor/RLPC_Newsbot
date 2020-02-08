from PIL import Image, ImageDraw, ImageFont

def player_card(username, rep, mmr, seasons, league, team):
    
    rep = str(rep)
    mmr = str(mmr)
    seasons = str(seasons)
    
    card = Image.open("./Image_templates/Filled_template.png")
    draw = ImageDraw.Draw(card)
    
    # Put username in the title box
    title_font = ImageFont.truetype("arial.ttf",20)
    w, h = draw.textsize(username)
    draw.text((((280-w)/2)+20,((300-h)/2)-110), username, font=title_font, fill="black")
    
    # Put reputation in the rep box
    rep_font = ImageFont.truetype("arial.ttf", 25)
    w, h, = draw.textsize(rep)
    draw.text(((84-w)/2,(75-h)/2), rep, font=rep_font, fill="black")
    
    # Put MMR in the mmr box
    mmr_font = ImageFont.truetype("arial.ttf", 15)
    w, h = draw.textsize(mmr)
    draw.text(((155-w)/2,145), mmr, font=mmr_font, fill="black")
    
    # Put seasons played in the seasons box
    seasons_font = mmr_font
    w, h = draw.textsize(seasons)
    draw.text((((450-w)/2)+150,145), seasons, font=seasons_font, fill="black")
    
    # Put league in the league box
    league_font = mmr_font
    w, h = draw.textsize(league)
    draw.text(((155-w)/2,145), league, font=league_font, fill="black")
    
    # Put team in the team box
    team_font = mmr_font
    w, h = draw.textsize(team)
    draw.text(((155-w)/2,145), team, font=team_font, fill="black")
    
    card.show()