import pandas as pd
import Google_Sheets as sheet

spreadsheet_id = sheet.SPREADSHEET_ID

# Initial ELO for each team = 1000
def reset_elo(league=""):
    gsheet = sheet.get_google_sheet(spreadsheet_id, 'ELO!A1:H')
    global total_elo_data
    total_elo_data = sheet.gsheet2df(gsheet)
    
    global major_elo
    major_elo = total_elo_data[['Major Teams','Major ELO']]
    major_elo = major_elo.rename(columns={'Major Teams': 'teams','Major ELO': 'ELO'})
    global aaa_elo
    aaa_elo = total_elo_data[['AAA Teams','AAA ELO']]
    aaa_elo = aaa_elo.rename(columns={'AAA Teams': 'teams','AAA ELO': 'ELO'})
    global aa_elo
    aa_elo = total_elo_data[['AA Teams','AA ELO']]
    aa_elo = aa_elo.rename(columns={'AA Teams': 'teams','AA ELO': 'ELO'})
    global a_elo
    a_elo = total_elo_data[['A Teams','A ELO']]
    a_elo = a_elo.rename(columns={'A Teams': 'teams','A ELO': 'ELO'})
    
reset_elo()

#Save data to the spreadsheet
def save_data(league=""):
    if league.casefold() == "major":
        for row in major_elo.index:
            if major_elo.iloc[row,1] != total_elo_data.iloc[row,1]:
                sheet.update_cell(spreadsheet_id,f'ELO!B{row+2}',major_elo.iloc[row,1])
            else:
                pass
    elif league.casefold() == "aaa":
        for row in aaa_elo.index:
            if aaa_elo.iloc[row,1] != total_elo_data.iloc[row,3]:
                sheet.update_cell(spreadsheet_id,f'ELO!D{row+2}',aaa_elo.iloc[row,1])
            else:
                pass
    elif league.casefold() == "aa":
        for row in major_elo.index:
            if aa_elo.iloc[row,1] != total_elo_data.iloc[row,5]:
                sheet.update_cell(spreadsheet_id,f'ELO!F{row+2}',aa_elo.iloc[row,1])
            else:
                pass
    elif league.casefold() == "a":
        for row in major_elo.index:
            if a_elo.iloc[row,1] != total_elo_data.iloc[row,7]:
                sheet.update_cell(spreadsheet_id,f'ELO!H{row+2}',a_elo.iloc[row,1])
            else:
                pass
    else:
        save_data("major")
        save_data("aaa")
        save_data("aa")
        save_data("a")
    
def recall_data(league=""):
    if league.casefold() == "major":
        reset_elo("major")
        return(major_elo)
    elif league.casefold() == "aaa":
        reset_elo("aaa")
        return(aaa_elo)
    elif league.casefold() == "aa":
        reset_elo("aa")
        return(aa_elo)
    elif league.casefold() == "a":
        reset_elo("a")
        return(a_elo)
    else:
        reset_elo()
        return(total_elo_data)
        
recall_data()
        
# Adding games via copy/paste from the sheet
def add_games_auto(league):
    data=input("Copy/paste data from spreadsheet: ")
    game_data = []
    game_data = data.split("	")
    team1 = ""
    team2 = ""
    winner = ""
    score = ""
    # Update elo
    for game in range(0,int(((len(game_data))-1)/7)):
        team1 = game_data[game*7]
        team1 = team1.lstrip()
        team1 = team1.title()
        team2 = game_data[game*7+2]
        team2 = team2.title()
        winner = game_data[game*7+3]
        score = game_data[game*7+4]
        Qa = 0
        Qb = 0
        if league.casefold() == "major":
            Qa = 10**(major_elo.loc[major_elo['teams']==team1,'ELO'][0]/400)
            Qb = 10**(major_elo.loc[major_elo['teams']==team2,'ELO'][0]/400)
        elif league.casefold() == "aaa":
            Qa = 10**(aaa_elo.loc[aaa_elo['teams']==team1,'ELO'][0]/400)
            Qb = 10**(aaa_elo.loc[aaa_elo['teams']==team2,'ELO'][0]/400)
        elif league.casefold() == "aa":
            Qa = 10**(aa_elo.loc[aa_elo['teams']==team1,'ELO'][0]/400)
            Qb = 10**(aa_elo.loc[aa_elo['teams']==team2,'ELO'][0]/400)
        elif league.casefold() == "a":
            Qa = 10**(a_elo.loc[a_elo['teams']==team1,'ELO'][0]/400)
            Qb = 10**(a_elo.loc[a_elo['teams']==team2,'ELO'][0]/400)
        Ea = Qa/(Qa+Qb)
        Eb = Qb/(Qa+Qb)
        Sa = 0
        Sb = 0
        if score != "FF":
            if winner == team1:
                scparts = score.split()
                Sa = int(scparts[0])/(int(scparts[0])+int(scparts[2]))
                Sb = int(scparts[2])/(int(scparts[0])+int(scparts[2]))
            elif winner == team2:
                scparts = score.split()
                Sb = int(scparts[0])/(int(scparts[0])+int(scparts[2]))
                Sa = int(scparts[2])/(int(scparts[0])+int(scparts[2]))
            elif winner == "Double FF":
                Sa = Ea
                Sb = Eb
            else:
                Sa = Ea
                Sb = Eb
        elif score == "FF":
            Sa = Ea
            Sb = Eb
        else:
            Sa = Ea
            Sb = Eb
        if league == "major":
            major_elo.loc[major_elo['teams']==team1,'ELO'] = round(major_elo.loc[major_elo['teams']==team1,'ELO'][0] + 100*(Sa - Ea))
            major_elo.loc[major_elo['teams']==team2,'ELO'] = round(major_elo.loc[major_elo['teams']==team2,'ELO'][0] + 100*(Sb - Eb))
        if league == "aaa":
            aaa_elo.loc[aaa_elo['teams']==team1,'ELO'] = round(aaa_elo.loc[aaa_elo['teams']==team1,'ELO'][0] + 100*(Sa - Ea))
            aaa_elo.loc[aaa_elo['teams']==team2,'ELO'] = round(aaa_elo.loc[aaa_elo['teams']==team2,'ELO'][0] + 100*(Sb - Eb))
        if league == "aa":
            aa_elo.loc[aa_elo['teams']==team1,'ELO'] = round(aa_elo.loc[aa_elo['teams']==team1,'ELO'][0] + 100*(Sa - Ea))
            aa_elo.loc[aa_elo['teams']==team2,'ELO'] = round(aa_elo.loc[aa_elo['teams']==team2,'ELO'][0] + 100*(Sb - Eb))
        if league == "a":
            a_elo.loc[a_elo['teams']==team1,'ELO'] = round(a_elo.loc[a_elo['teams']==team1,'ELO'][0] + 100*(Sa - Ea))
            a_elo.loc[a_elo['teams']==team2,'ELO'] = round(a_elo.loc[a_elo['teams']==team2,'ELO'][0] + 100*(Sb - Eb))
    save_data()
        
def add_games_manual(league,team1,team2,winner,score):
    score = list(score)
    score = f"{score[0]} - {score[-1]}"
    team1 = team1.title()
    team2 = team2.title()
    Qa = 0
    Qb = 0
    if league.casefold() == "major":
        Qa = 10**(int(major_elo.loc[major_elo['teams']==team1,'ELO'])/400)
        Qb = 10**(int(major_elo.loc[major_elo['teams']==team2,'ELO'])/400)
    elif league.casefold() == "aaa":
        Qa = 10**(int(aaa_elo.loc[aaa_elo['teams']==team1,'ELO'])/400)
        Qb = 10**(int(aaa_elo.loc[aaa_elo['teams']==team2,'ELO'])/400)
    elif league.casefold() == "aa":
        Qa = 10**(int(aa_elo.loc[aa_elo['teams']==team1,'ELO'])/400)
        Qb = 10**(int(aa_elo.loc[aa_elo['teams']==team2,'ELO'])/400)
    elif league.casefold() == "a":
        Qa = 10**(int(a_elo.loc[a_elo['teams']==team1,'ELO'])/400)
        Qb = 10**(int(a_elo.loc[a_elo['teams']==team2,'ELO'])/400)
    Ea = Qa/(Qa+Qb)
    Eb = Qb/(Qa+Qb)
    Sa = 0
    Sb = 0
    scparts = score.split()
    score1 = int(scparts[0])
    score2 = int(scparts[2])
    if score.casefold() != "ff":
        if winner == team1 and score1 > score2:
            Sa = score1/(score1+score2)
            Sb = score2/(score1+score2)
        elif winner == team1 and score2 > score1:
            Sb = score1/(score1+score2)
            Sa = score2/(score1+score2)
        elif winner == team2 and score1 > score2:
            Sa = score1/(score1+score2)
            Sb = score2/(score1+score2)
        elif winner == team2 and score2 > score1:
            Sb = score1/(score1+score2)
            Sa = score2/(score1+score2)
        elif winner.casefold() == "double ff":
            Sa = Ea
            Sb = Eb
        else:
            Sa = Ea
            Sb = Eb
    elif score.casefold() == "ff":
        Sa = Ea
        Sb = Eb
    else:
        Sa = Ea
        Sb = Eb
    if league.casefold() == "major":
        major_elo.loc[major_elo['teams']==team1,'ELO'] = round(int(major_elo.loc[major_elo['teams']==team1,'ELO']) + 100*(Sa - Ea))
        major_elo.loc[major_elo['teams']==team2,'ELO'] = round(int(major_elo.loc[major_elo['teams']==team2,'ELO']) + 100*(Sb - Eb))
    if league.casefold() == "aaa":
        aaa_elo.loc[aaa_elo['teams']==team1,'ELO'] = round(int(aaa_elo.loc[aaa_elo['teams']==team1,'ELO']) + 100*(Sa - Ea))
        aaa_elo.loc[aaa_elo['teams']==team2,'ELO'] = round(int(aaa_elo.loc[aaa_elo['teams']==team2,'ELO']) + 100*(Sb - Eb))
    if league.casefold() == "aa":
        aa_elo.loc[aa_elo['teams']==team1,'ELO'] = round(int(aa_elo.loc[aa_elo['teams']==team1,'ELO']) + 100*(Sa - Ea))
        aa_elo.loc[aa_elo['teams']==team2,'ELO'] = round(int(aa_elo.loc[aa_elo['teams']==team2,'ELO']) + 100*(Sb - Eb))
    if league.casefold() == "a":
        a_elo.loc[a_elo['teams']==team1,'ELO'] = round(int(a_elo.loc[a_elo['teams']==team1,'ELO']) + 100*(Sa - Ea))
        a_elo.loc[a_elo['teams']==team2,'ELO'] = round(int(a_elo.loc[a_elo['teams']==team2,'ELO']) + 100*(Sb - Eb))
        
    save_data()

#Get the expected score and winner of a matchup
def exp_score(league,team1,team2,bestof=100):
    team1 = team1.title()
    team2 = team2.title()
    if league.casefold() == "major":
        team1elo = major_elo.loc[major_elo['teams']==team1,'ELO'][0]
        team2elo = major_elo.loc[major_elo['teams']==team2,'ELO'][0]
    elif league.casefold() == "aaa":
        team1elo = aaa_elo.loc[aaa_elo['teams']==team1,'ELO'][0]
        team2elo = aaa_elo.loc[aaa_elo['teams']==team2,'ELO'][0]
    elif league.casefold() == "aa" or league.casefold() == "indy":
        team1elo = aa_elo.loc[aa_elo['teams']==team1,'ELO'][0]
        team2elo = aa_elo.loc[aa_elo['teams']==team2,'ELO'][0]
    elif league.casefold() == "a" or league.casefold() == "mav":
        team1elo = a_elo.loc[a_elo['teams']==team1,'ELO'][0]
        team2elo = a_elo.loc[a_elo['teams']==team2,'ELO'][0]
    Q1 = 10**(team1elo/400)
    Q2 = 10**(team2elo/400)
    exp_score_1 = Q1/(Q1+Q2)
    exp_score_2 = Q2/(Q1+Q2)
    if exp_score_1 > exp_score_2:
        return(f'''Winner: {team1}
Score: {str(int(round(exp_score_1*bestof)))} - {str(int(round(exp_score_2*bestof)))}''')
    elif exp_score_2 > exp_score_1:
        return(f'''Winner: {team2}
Score: {str(int(round(exp_score_2*bestof)))} - {str(int(round(exp_score_1*bestof)))}''')
    else:
        return(f'''Winner: Pure toss up)
Score: Pure toss up''')
        
def rank_teams(league):
    if league.casefold() == "major":
        major_elo['ELO'] = major_elo['ELO'].map(lambda a: int(a))
        lb = major_elo.sort_values(by=['ELO'], ascending=False)
        lb = lb.reset_index(drop=True)
        return(lb)
    if league.casefold() == "aaa":
        aaa_elo['ELO'] = aaa_elo['ELO'].map(lambda a: int(a))
        lb = aaa_elo.sort_values(by=['ELO'], ascending=False)
        lb = lb.reset_index(drop=True)
        return(lb)
    if league.casefold() == "aa" or league.casefold() == "indy":
        aa_elo['ELO'] = aa_elo['ELO'].map(lambda a: int(a))
        lb = aa_elo.sort_values(by=['ELO'], ascending=False)
        lb = lb.reset_index(drop=True)
        return(lb)
    if league.casefold() == "a" or league.casefold() == "mav":
        a_elo['ELO'] = a_elo['ELO'].map(lambda a: int(a))
        lb = a_elo.sort_values(by=['ELO'], ascending=False)
        lb = lb.reset_index(drop=True)
        return(lb)