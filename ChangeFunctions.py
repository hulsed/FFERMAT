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
            
        

    