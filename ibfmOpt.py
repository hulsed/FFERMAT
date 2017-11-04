# -*- coding: utf-8 -*-
"""
Created on Thu Nov  2 11:34:44 2017

@author: hulsed
"""
import os
import sys
import fileinput
import numpy as np
import scipy as sp

def changeController():
    #actions
    actionmodes=['2','3','3','2','3','1','2','3','1']
    #states
    modes=3
    conditions=['LowSignal', 'HighSignal','NominalSignal']
    condlist, modelist=enumerateStates(conditions, modes)
    
    changeFunctions(condlist, modelist, actionmodes)
    
    return 0

def changeFunctions(condlist, modelist, actionmodes):
    filename='functions.ibfm'
    function='ControlElectrical'
    infunction=0
    statenum=0
    
    newline=''
    
    with fileinput.FileInput(filename, inplace=True, backup='.bak') as thefile:
        for line in thefile:
            if 'function' in line and function in line:
                #print('function found')
                infunction=1
            elif 'function' in line:
                #print('other function')
                infunction=0
            elif 'mode' not in line and infunction==1:
                newline='    condition ' + modelist[statenum] + ' to ' + actionmodes[statenum] + ' ' + condlist[statenum] + '\n'
                statenum=statenum+1
                #print(line)
                line=newline
            print(line, end='')
    return 0

def enumerateStates(conditions, modes):
    conds=len(conditions)
    condlist=[]
    modelist=[]
    
    for j in range(conds):
        for k in range(modes):
            condlist=condlist+[conditions[j]]
            modelist=modelist+[str(k+1)]
            
    return condlist, modelist

def score(exp):
    numstates=len(exp.getResults())
    functions=['exportEE1']
    scorefunc={'Failed': 5,'Degraded': 2, 'Operational': 0}
    funsco=np.zeros([numstates,len(functions)])
    scensco=np.zeros(numstates)
    
    count=0
    #score modes
    for i in range(numstates):
        count=0
        for j in functions:
            #takes the state of the function at the final iteration
            res=exp.getResults()[i][j][1]
            funsco[i,count]=scorefunc[res]
            count=count+1
        scensco[i]=sum(funsco[i,:])
        
    totsco=sum(scensco)
    
    return scensco, totsco
    
        

    