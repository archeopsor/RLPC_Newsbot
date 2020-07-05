from bs4 import BeautifulSoup
import requests

def get_mmr(url: str) -> (int, int):
    """
    Parameters
    ----------
    url : str
        Rocket League Tracker Network.

    Returns
    -------
    Tuple with 2 integers: 
        1) Doubles mmr (int)
        2) Standard mmr (int)
    """
    req = requests.get(url)
    soup = BeautifulSoup(req.content, 'html.parser')
    match = soup.find('div', class_='season-table')
    
    test = match.text
    test = test.split("\n")
    test = list(filter(lambda a: a not in ["", " "], test))
    test = list(filter(lambda a: "Streak" not in a, test))
    test = list(filter(lambda a: "Div" not in a, test))
    test = list(filter(lambda a: "~" not in a, test))
    
    doubles = test[21]
    standard = test[31]
    
    print("Doubles MMR:", doubles)
    print("Standard MMR:", standard)
    
    return(doubles, standard)