import pandas as pd
import numpy as np
from bs4 import BeautifulSoup
import time
import re

def completeURL(playerExtension):
    
    #Input: Extracted player URL
    #Output: URL to current season stats
    
    return 'https://www.basketball-reference.com{}/gamelog/2019'.format(playerExtension)
    
def createURLTable(letter):
    
    #Input: Letter 
    #Output: returns table of players and their URL for respective letter
    url = 'https://www.basketball-reference.com/players/{}'.format(letter)
    html = urlopen(url)
    soup = BeautifulSoup(html,'html.parser')
    rows = soup.findAll('strong')[2:-15]
    
    players_extension = [[a['href'] for a in rows[i].findAll('a',href = True)]
                    for i in range(len(rows))]
    players = [[a.get_text() for a in rows[i].findAll('a',href = True)]
                    for i in range(len(rows))]
    playerTable = pd.DataFrame(data = [players,players_extension],index = ['Name','Extension'])

    playerTable = playerTable.T

    playerTable['Name'] = playerTable['Name'].str[0]
    
    playerTable['Extension'] = playerTable['Extension'].str[0]
    playerTable['Extension'] = playerTable['Extension'].map(lambda x: x.strip('.html'))
    playerTable['Extension'] = playerTable['Extension'].apply(func = completeURL )
    
    return playerTable 
    
database = pd.DataFrame(columns = ['Name','Extension'])

alphabet = ['a','b','c','d','e','f','g','h','i','j','k','l','m','n','o','p','q','r','s','t','u','v','w','x','y','z']
for letter in alphabet:
    try:
        table = createURLTable(letter)
        database = database.append(table)
    except:
        pass
  
database.index = database.Name
database['Name']= database['Name'].str.replace('[^\w\s]','')
database['Nickname'] = database['Name'].apply(lambda x: x.replace(" ",""))
database = database.drop(labels = 'Name',axis=1)

database.to_csv('NBArefDatabase.csv')
