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
    #modes and conditions to use
    nummodes=3
    conditions=['LowSignal', 'HighSignal','NominalSignal']
    
    #actions (should be input to function)
    policy=[1,2,3]
    
    changeFunctions(policy,nummodes, conditions)
    
    return 0

    

def changeFunctions(policy,nummodes, conditions):
    filename='functions.ibfm'
    function='ControlElectrical'
    #convert policy to input and output modes
    inmodestr,outmodestr=policy2strs(policy,nummodes)    
    
    numconditions=len(conditions)
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
            elif 'mode' not in line and infunction==1 and statenum>=numconditions:
                newline='    condition ' + inmodestr[statenum] + ' to ' + outmodestr[statenum] + ' ' + conditions[statenum] + '\n'
                statenum=statenum+1
                #print(line)
                line=newline
            print(line, end='')
    print(statenum)
    return 0

def policy2strs(policy,nummodes):
    states=len(policy)
    options=list(range(1,nummodes+1))
    inmodes=np.zeros([nummodes-1])
    inmodestr=['' for x in range(states)]
    
    for i in range(states):
        toremove=policy[i]
        inmodes=list(filter(lambda x: x!=toremove,options))
        inmodestr[i]=' '.join(str(x) for x in inmodes)
        
    outmodestr=np.char.mod('%d',policy)   
    
    return inmodestr,outmodestr


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
    
        

    