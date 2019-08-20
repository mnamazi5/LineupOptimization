import pandas as pd
import numpy as np
from ortools.linear_solver import pywraplp
from urllib.request import urlopen
from bs4 import BeautifulSoup
import math
import time
import re

#import data
df = pd.read_csv('FanDuel-NBA-2019-02-23-32998-players-list.csv')

#Strip Nickname of spaces to be used as variables for optimization
df['Nickname'] = df['Nickname'].apply(lambda x: x.replace(" ",""))

# Giving players
df['modelFPPG'] = df['FPPG']

#Strip First and Last name for use in URL
df["First Name"] = df['First Name'].str.replace('[^\w\s]','')
df["Last Name"] = df['Last Name'].str.replace('[^\w\s]','')

def getURL(player):
    #Input: Row of df (or Player)
    #Output: The most common structure for player URL
    
    if len(player['Last Name']) > 5:
        extension = player['Last Name'][0].lower() + '/' + player['Last Name'][0:5].lower() + player['First Name'][0:2].lower() +'01'
    else:
        extension = player['Last Name'][0].lower() + '/' + player['Last Name'].lower() + player['First Name'][0:2].lower() +'01'
    
    return "https://www.basketball-reference.com/players/{}/gamelog/2019".format(extension)


def getStats(player):
    
    #Input: Dataframe row(or player)
    #Output: Return and fills the modelFPPG (or mean+1_std of 10-day data)
    
    
    # A time stop to not overload basketball-reference with requests
    time.sleep(2)
    
    #Using beautifulSoup to find HTML page of respective player 
    
    url = getURL(player)
    html = urlopen(url)
    soup = BeautifulSoup(html,'lxml')
    
    #If player shares URL with older player we switch number of extension accordingly
    
    for j in range(1,5):
        if soup.findAll('tr') != []:
            break
        else:    
            url = url.replace('0' + str(j),'0'+str(j + 1),1)
            html = urlopen(url)
            soup = BeautifulSoup(html,'lxml')
        
    #The following two 'if' statements account for two specific URL inconsistencies 
    
    if soup.findAll('th') == []:
        m = re.search(player['First Name'][0:2].lower(), url)
    
        s1 = url[:m.end()]
        s2 = url[m.end():]
        s3 = s2.replace(player['First Name'][0:2].lower(),player['First Name'][2].lower() + player['First Name'][1].lower(),1)
    
        url = s1+s3
        url = url.replace('05','01',1)
    
        html = urlopen(url)
        soup = BeautifulSoup(html,'lxml')
      
    if soup.findAll('tr') == []:
        url = url.replace(player['First Name'][0:2].lower(),player['Last Name'][0:2].lower(),1)
        url = url.replace('05','01',1)
        html = urlopen(url)
        soup = BeautifulSoup(html,'lxml')
    
    
    #Following loop finds where in the HTML text we can find stats table
    i = 0
    for tr in soup.findAll('tr'):
        i = i + 1
        if 'th' in tr.prettify():
            break
    
    #Finds the headers of stats table
    headers = [th.getText() for th in soup.findAll('tr')[i-1].findAll('th')]
    headers = headers[1:]
    
    #extracts dats per row and fills into stats dataframe
    rows = soup.findAll('tr')[32:]
    player_stats = [[td.getText() for td in rows[i].findAll('td')]
                    for i in range(len(rows))]
    
    stats = pd.DataFrame(player_stats, columns = headers)
    stats = stats.apply(pd.to_numeric,errors='ignore')
    
    #Removes games not played and keeps most recent 10
    stats = stats.dropna(axis = 0)
    stats = stats.tail(10)
    
    #If player has not played 10 games we simply use expected value
    if stats.shape[0] < 10:
        modelFPPG = player['FPPG']
    else:    
        stats['FPPG'] = stats['PTS'] + 1.2*stats['TRB'] + 1.5*stats['AST'] + 3*stats['BLK'] + 3*stats['STL'] - stats['TOV']
        modelFPPG = stats['FPPG'].mean()+ math.sqrt(stats['FPPG'].var())
   
    return modelFPPG
    
    
#Finding modelFPPG of top 200 players
df.loc[0:200,'modelFPPG'] = df.loc[0:200,:].apply(func = getStats,axis = 1)


#Initiate Solver and constraints
solver = pywraplp.Solver('Lineup Optimizer',
                            pywraplp.Solver.CBC_MIXED_INTEGER_PROGRAMMING)
objective = solver.Objective()

constraintSalary = solver.Constraint(-solver.infinity(), 60000)
constraintPG = solver.Constraint(2,2)
constraintSG = solver.Constraint(2,2)
constraintSF = solver.Constraint(2,2)
constraintPF = solver.Constraint(2,2)
constraintC = solver.Constraint(1,1)


def initiateVariables(player):
    #Input: row of df(or player)
    #Ouput: adds each players as variable in Linear Programming Problem
        
    #Globals allows us to iniate a dynamic variable name into oru program
    globals()[player['Nickname']] = solver.IntVar(0,1,player['Nickname'])
        
    #Set player coeff as modelFPPG (what we want to maximize)
    objective.SetCoefficient(globals()[player['Nickname']],player['modelFPPG'])
        
    #Adding each player's respective value for respective constraint
    constraintSalary.SetCoefficient(globals()[player['Nickname']],player['Salary'])
        
    if player['Position'] == 'PG':
        constraintPG.SetCoefficient(globals()[player['Nickname']],1)
        
    elif player['Position'] == 'SG':
        constraintSG.SetCoefficient(globals()[player['Nickname']],1)
        
    elif player['Position'] == 'SF':
        constraintSF.SetCoefficient(globals()[player['Nickname']],1)
        
    elif player['Position'] == 'PF':
        constraintPF.SetCoefficient(globals()[player['Nickname']],1)
        
    elif player['Position'] == 'C':
        constraintC.SetCoefficient(globals()[player['Nickname']],1)


df.apply(func = initiateVariables, axis = 1)

#Setting as maximiaztion problem
objective.SetMaximization()


print('Number of variables =', solver.NumVariables())
print('Number of constraints =', solver.NumConstraints())

# Solve the system.
status = solver.Solve()
# Check that the problem has an optimal solution.
if status != pywraplp.Solver.OPTIMAL:
    print("The problem does not have an optimal solution!")
    exit(1)


def printPlayers(player):
    #Input: player dataframe
    #Output: players found in the optimal solution
    
    if globals()[player['Nickname']].solution_value() > 0.5:
      
        print(player['First Name'],player['Last Name'],round(player['FPPG'],2))
    else:
        pass
df = df.apply(func = printPlayers, axis = 1)


print('Optimal objective value = %f' % solver.Objective().Value())
