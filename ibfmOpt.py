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
import importlib
import ibfm


    
def initFullPolicy(controllers, conditions):
    FullPolicy=np.ones([controllers,conditions], int)
    return FullPolicy

def initQTab(controllers, conditions, modes):
    #Qtable: controller (state), input condition (state), output mode (action)
    QTab=np.ones([controllers,conditions,modes])
    return QTab

def avlearn(QTab, FullPolicy,reward):
    controllers,conditions,modes=np.shape(QTab)
    alpha=0.1
    taken=1
    QVal=1.0
    
    for i in range(controllers):
        for j in range(conditions):
            taken=FullPolicy[i,j]-1
            QVal=QTab[i,j,taken]
            QTab[i,j,taken]=QVal+alpha*(reward-QVal)
            
    return QTab

def selectPolicy(QTab, FullPolicy):
    tau=1
    
    controllers,conditions,modes=np.shape(QTab)
    prob=np.ones(modes)
    relval=np.ones(modes)

    for i in range(controllers):
        for j in range (conditions):
            for k in range(modes):
                relval[k]=np.exp(QTab[i,j,k]/tau)
            prob=relval/sum(relval)
            FullPolicy[i,j]=np.random.choice(modes,1,p=prob)+1

    return FullPolicy

def evaluate(FullPolicy):
    changeFunctions(FullPolicy)
    importlib.reload(ibfm)
    
    e1= ibfm.Experiment('monoprop')
    e1.run(1)
    scenscore,reward=score(e1)
    
    return reward

def changeFunctions(FullPolicy):
    #parameters of problem
    nummodes=3
    controllers=len(FullPolicy)
    functions=[]
    for controller in range(controllers):
        num=controller+1
        functions=functions+['ControlSig'+str(num)]
    conditions=['LowSignal', 'HighSignal','NominalSignal']
    filename='functions.ibfm'
    #initialization
    policy=FullPolicy[0]
    inmodestr,outmodestr=policy2strs(policy,nummodes)     
    num=0     
    numconditions=len(conditions)
    newline=''
    infunction=0
    #open the functions file to edit
    with fileinput.FileInput(filename, inplace=True) as thefile:
        for line in thefile:
            #check to find function
            if 'function' in line:
                for function in functions:
                    if function in line:
                        funnum=functions.index(function)
                        infunction=1
                        policy=FullPolicy[funnum]
                        inmodestr,outmodestr=policy2strs(policy,nummodes) 
                        statenum=0
                    
            elif 'function' in line:
                #print('other function')
                infunction=0
            elif 'mode' not in line and infunction==1 and statenum<=numconditions:
                newline='    condition ' + inmodestr[statenum] + ' to ' + outmodestr[statenum] + ' ' + conditions[statenum] + '\n'
                statenum=statenum+1
                #print(line)
                line=newline
            print(line, end='')
            

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
    functions=['exportT1']
    Flow="Thrust"
    
    statescores=np.zeros([numstates,len(functions)])
    scensco=np.zeros(numstates)
    
    for i in range (numstates):
        flowsraw=list(exp.results[i].keys())
        flows=[str(j) for j in flowsraw]
        states=list(exp.results[i].values())
        loc=flows.index(Flow)
        
        effort=int(states[loc][0])
        rate=int(states[loc][1])
        statescores[i]=scoreState(rate,effort)
        
    totalscore=sum(statescores)
    #score modes
    #for i in range(numstates):
    #    count=0
    #    for j in functions:
    #        #takes the state of the function at the final iteration
    #        res=exp.getResults()[i][j][1]
    #        funsco[i,count]=scorefunc[res]
    #        count=count+1
    #    scensco[i]=sum(funsco[i,:])
    #scorefunc={'Failed': -5,'Degraded': -2, 'Operational': 0}
        
    totsco=sum(scensco)
    
    return statescores, totalscore

def scoreState(rate, effort):
    func = [[-10,-10,-10,-10,-10],
            [-10, -5, -3, -1, -7],
            [-10, -3,  0, -3, -9],
            [-10, -1, -3, -5,-10],
            [-10, -7, -9,-10,-10]]
            
    score=func[effort][rate]
    return score


    
        

    