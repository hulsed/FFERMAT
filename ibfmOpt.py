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
    QTab=np.ones([controllers,conditions,modes])*-25
    return QTab

def avlearnnotracking(QTab, FullPolicy,reward):
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

def avlearn(QTab, actions, instates, reward):
    controllers,conditions,modes=np.shape(QTab)
    alpha=0.01
    QVal=1.0
    
    for i in range(controllers):
        taken=actions[i]
        instate=instates[i]
        QVal=QTab[i,instate,taken]
        QTab[i,instate,taken]=QVal+alpha*(reward-QVal)
        
def Qlearn(QTab, actions, instates, reward):
    controllers,conditions,modes=np.shape(QTab)
    alpha=0.01
    QVal=1.0
    
    #preceding controllers get max next q value
    for i in range(controllers-1):
        taken=actions[i]
        instate=instates[i]
        QVal=QTab[i,instate,taken]
        maxnextQ=max(QTab[i+1,instates[i+1],:])
        QTab[i,instate,taken]=QVal+alpha*(maxnextQ-QVal)
    
    #final controller gets reward
    finaltaken=actions[controllers-1]
    finalstate=instates[controllers-1]
    QVal=QTab[controllers-1,finalstate,finaltaken]
    QTab[controllers-1,finalstate,finaltaken]=QVal+alpha*(reward-QVal)
        
#def avlearn(QTab, FullPolicy,reward):
#    controllers,conditions,modes=np.shape(QTab)
#    alpha=0.1
#    taken=1
#    QVal=1.0
#    
#    for i in range(controllers):
#        for j in range(conditions):
#            taken=FullPolicy[i,j]-1
#            QVal=QTab[i,j,taken]
#            QTab[i,j,taken]=QVal+alpha*(reward-QVal)
#            
#    return QTab

def selectPolicy(QTab, FullPolicy):
    tau=1.0
    
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
    
    scenarios=len(e1.results)
    actions=[]
    instates=[]
    scores=[]
    for scenario in range(scenarios):
        actions=actions+[trackActions(e1,scenario)]
        instates=instates+[trackFlows(e1,scenario)]
        scores=scores+[scoreEndstate(e1,scenario)]
    
    return actions, instates, scores

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

def trackActions(exp, scenario):
    #functions of concern--the controlling functions
    functions=['controlG2rate','controlG3press','controlP1effort','controlP1rate']
    mode2actions={'EqualControl': 0, 'IncreaseControl': 1, 'DecreaseControl': 2}
    numstates=len(exp.getResults())
    
    actions=[]
    #find actions taken
    for function in functions:
        mode=str(exp.results[scenario][function])
        actions=actions+[mode2actions[mode]] 
    return actions
    
#NOTE: Will ONLY work if only signals are to controllers
def trackFlows(exp, scenario):
    #flows of concern--inputs to the controllers    
    condition2state={'Negative':0,'Zero': 0,'Low': 0,'High': 1,'Highest': 1,'Nominal': 2}
    
    flowtypesraw=list(exp.results[scenario].keys())
    flowtypes=[str(j) for j in flowtypesraw]
    flowstates=list(exp.results[scenario].values())
    
    flownum=len(flowtypes)
    instates=[]
    
    #find states entered
    for i in range(flownum):
        if flowtypes[i]=='Signal':
            if i%2==0:
                incondition=str(flowstates[i][0])
                instate=condition2state[incondition]
                instates=instates+[instate]
                
    return instates

def scoreEndstate(exp, scenario):
    functions=['exportT1']
    Flow="Thrust"
    
    flowsraw=list(exp.results[scenario].keys())
    flows=[str(j) for j in flowsraw]
    states=list(exp.results[scenario].values())
    loc=flows.index(Flow)
        
    effort=int(states[loc][0])
    rate=int(states[loc][1])
    statescore=scoreFlowstate(rate,effort)
    
    return statescore

def scoreFlowstate(rate, effort):
    func = [[-10,-10,-10,-10,-10],
            [-10, -5, -3, -1, -7],
            [-10, -3,  0, -3, -9],
            [-10, -1, -3, -5,-10],
            [-10, -7, -9,-10,-10]]
            
    score=func[effort][rate]
    return score

def scorefxns(exp):
    
    exp.run(1)
    scenarios=len(exp.results)
    
    functions=[]
    scores=[]
    
    #initialize dictionary
    fxns=exp.model.graph.nodes()
    fxnscores={}
    for fxn in fxns:
        fxnscores[fxn]=[]
    
    for scenario in range(scenarios):
        function=list(exp.scenarios[scenario].keys())[0]
        functions=functions+[function]
        score=scoreEndstate(exp,scenario)
        scores=scores+[score]
        
        fxnscores[function]=[score]+fxnscores[function]
        
    
    return functions, scores, fxnscores
        

    
        

    