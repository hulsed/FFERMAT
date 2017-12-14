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
import networkx as nx


def createVariants():
    
    file=open('ctlfxnvariants.ibfm', mode='w')
    variants=[3,3,3]
    options=list(range(1,variants[0]+1))
    
    for i in range(variants[0]):
        for j in range(variants[1]):
            for k in range(variants[2]):
                file.write('function ControlSig'+str(i+1)+str(j+1)+str(k+1)+'\n')
                file.write('\t'+'mode 1 Operational EqualControl \n')
                file.write('\t'+'mode 2 Operational IncreaseControl \n')
                file.write('\t'+'mode 3 Operational DecreaseControl \n')
                
                toremove=i+1
                inmodes=list(filter(lambda x: x!=toremove,options))
                inmodestr=' '.join(str(x) for x in inmodes)
                
                file.write('\t'+'condition '+inmodestr+' to '+str(toremove)+' LowSignal'+'\n')
                
                toremove=j+1
                inmodes=list(filter(lambda x: x!=toremove,options))
                inmodestr=' '.join(str(x) for x in inmodes)
                
                file.write('\t'+'condition '+inmodestr+' to '+str(toremove)+' HighSignal'+'\n')
                
                toremove=k+1
                inmodes=list(filter(lambda x: x!=toremove,options))
                inmodestr=' '.join(str(x) for x in inmodes)
                
                file.write('\t'+'condition '+inmodestr+' to '+str(toremove)+' NominalSignal'+'\n')
                
    file.close()
    return 0

           
def reviseModel(FullPolicy, exp):
    graph=exp.model.graph.copy()
    nodes=graph.nodes()
    edges=graph.edges()
    
    functions=['controlG2rate','controlG3press','controlP1effort','controlP1rate']
    
    newgraph=nx.DiGraph()
    
    for node in nodes:
        name=str(node)
        fxn=graph.node[node]['function']
        
        newgraph.add_node(name, function=fxn)
        if name in functions:
            loc=functions.index(name)
            policy=FullPolicy[loc]
            
            ctlfxn='ControlSig'+str(policy[0])+str(policy[1])+str(policy[2])
            newgraph.node[name]={'function': ctlfxn}
            
    
    for edge in edges:
        
        prev=str(edge[0])
        new=str(edge[1])
        
        flowtype=str(list(graph.edge[edge[0]][edge[1]][0].values())[0])

        newgraph.add_edge(prev,new,flow=flowtype)
        #newgraph.edge[prev]={new: {'flow': flowtype}}
        
    return newgraph  
    
    
    
def initFullPolicy(controllers, conditions):
    FullPolicy=np.ones([controllers,conditions], int)
    return FullPolicy

def initQTab(controllers, conditions, modes):
    #Qtable: controller (state), input condition (state), output mode (action)
    QTab=np.ones([controllers,conditions,modes])*-25
    return QTab

def initActions():
    FullPolicy=[[1,2,3],[1,2,3],[1,2,3],[1,2,3]]
    changeFxnfile(FullPolicy)
    e1= ibfm.Experiment('monoprop')
    actionkey=e1.model.graph.nodes()[6].modes
    
    return actionkey    
    

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

def evaluate(FullPolicy,actionkey):
    changeFunctions(FullPolicy)
    #importlib.reload(ibfm)
    e1= ibfm.Experiment('monoprop')
    e2=changeModes(FullPolicy, actionkey, e1)
    
    e2.run(1)
    
    scenarios=len(e2.results)
    actions=[]
    instates=[]
    scores=[]
    probs=[]
    for scenario in range(scenarios):
        actions=actions+[trackActions(e2,scenario)]
        instates=instates+[trackFlows(e2,scenario)]
        scores=scores+[scoreEndstate(e2,scenario)]
        
        prob=float(list(e1.scenarios[scenario].values())[0].prob)
        probs=probs+[prob]
    
    return actions, instates, scores, probs, e2

def changeModes(FullPolicy, actionkey, exp):
    
    functions=['controlG2rate','controlG3press','controlP1effort','controlP1rate']
    
    newmodes=[]
    funnum=0
    for function in exp.model.graph.nodes():
        newmodes=[]
        name=str(function)
        if name in functions:
            loc=functions.index(name)
            policy=FullPolicy[loc]
            for action in policy:
                newmode=actionkey[action-1]
                newmodes=newmodes+[newmode]
            exp.model.graph.nodes()[funnum].modes=newmodes
        funnum=funnum+1
    return exp

def changeFunctions(FullPolicy):
    #parameters of problem
    nummodes=3
    controllers=len(FullPolicy)
    functions=[]
    
    for controller in range(controllers):
        num=controller+1
        functions=functions+['ControlSig'+str(num)]
    conditions=['LowSignal', 'HighSignal','NominalSignal']
    modes=['EqualControl','IncreaseControl','DecreaseControl']
    template=[('EqualControl','Operational'),('EqualControl','Operational'),('EqualControl','Operational')]
    
    #changes dictionary values (not model definition, unfortunately)
    for controller in range(controllers):
        
        ibfm.functions[functions[controller]]=[(modes[FullPolicy[controller][0]-1],'Operational'),
         (modes[FullPolicy[controller][1]-1],'Operational'),
         (modes[FullPolicy[controller][2]-1],'Operational')]
    
    return 0

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
    probs=[]
    
    #initialize dictionary
    fxns=exp.model.graph.nodes()
    fxnscores={}
    fxnprobs={}
    for fxn in fxns:
        fxnscores[fxn]=[]
        fxnprobs[fxn]=[]
    
    for scenario in range(scenarios):
        function=list(exp.scenarios[scenario].keys())[0]
        functions=functions+[function]
        
        prob=float(list(exp.scenarios[scenario].values())[0].prob)
        probs=probs+[prob]
        
        score=scoreEndstate(exp,scenario)
        scores=scores+[score]
        
        fxnscores[function]=[score]+fxnscores[function]
        fxnprobs[function]=[prob]+fxnprobs[function]
        
    
    return functions, scores, probs, fxnscores, fxnprobs


### Deprecated functions
#writes full policy to function file
def changeFxnfile(FullPolicy):
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
#converts a single policy to a string
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
    
        

    