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

#Creates function variants in corresponding files
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

def randFullPolicy(controllers, conditions):
    FullPolicy=np.random.randint(3,size=(controllers,conditions))+1
    return FullPolicy

def randController(FullPolicy):
    controllers,conditions=FullPolicy.shape
    randcontroller=np.random.randint(controllers)
    FullPolicy[randcontroller]=np.random.randint(3,size=conditions)+1    
    return FullPolicy

def randCondition(FullPolicy):
    controllers,conditions=FullPolicy.shape
    randcontroller=np.random.randint(controllers)
    randcondition=np.random.randint(conditions)
    FullPolicy[randcontroller][randcondition]=np.random.randint(3)+1
    return FullPolicy

def initPopulation(pop,controllers, conditions):
    Population=np.random.randint(3,size=(pop,controllers,conditions))+1
    return Population
    
def permutePopulation(Population):
    pop,controllers,conditions=Population.shape
    frac=0.8
    
    for i in range(pop):
        oldPolicy=Population[i]
        
        rand=np.random.rand()
        if rand>frac:
            newPolicy=randController(oldPolicy)
        else:
            newPolicy=randCondition(oldPolicy)
            
        Population[i]=newPolicy
    return Population

def evalPopulation(Population, experiment):
    pop,controllers,conditions=Population.shape
    fitness=np.ones(pop)
    
    for i in range(pop):
        actions, instates, utilityscores, designcost=evaluate(Population[i],experiment)
        fitness[i]=sum(utilityscores)-designcost
    
    return fitness

def selectPopulation(Population1, fitness1, Population2, fitness2):
    newfitness=fitness1
    newpopulation=Population1
    
    totfitness=np.append(fitness1,fitness2)
    totpopulation=np.append(Population1, Population2)
    medfitness=np.median(totfitness)
    k=0
    
    for i in range(len(totfitness)):
        if totfitness[i]>medfitness:
            newfitness[k]=totfitness[i]
            newpopulation[k]=totpopulation[k]
            k+=1
    
    return newpopulation, newfitness
      
def EA(pop,generations, controllers, conditions, experiment):
    Population1=initPopulation(pop,controllers, conditions)
    Population2=initPopulation(pop,controllers, conditions)
    
    fitness1=evalPopulation(Population1, experiment)
    fitness2=evalPopulation(Population2, experiment)
    
    fithist=np.ones(generations)
    
    for i in range(generations):
        Population2=permutePopulation(Population1)
        fitness2=evalPopulation(Population2, experiment)
        
        Population1,fitness1=selectPopulation(Population1, fitness1, Population2, fitness2)
        
        maxfitness=max(fitness1)
        bestsolloc=np.argmax(fitness1)
        bestsol=Population1[bestsolloc]
        fithist[i]=maxfitness        
    return maxfitness, bestsol, fithist
    
#Initializes the Policy    
def initFullPolicy(controllers, conditions):
    FullPolicy=np.ones([controllers,conditions], int)
    return FullPolicy

#Initializes the Q-table
def initQTab(controllers, conditions, modes):
    #Qtable: controller (state), input condition (state), output mode (action)
    QTab=np.ones([controllers,conditions,modes])
    return QTab
  
#Learns value of the policy without tracking states entered
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

#Learns the value of the policy without propogating future states to previous
def avlearn(QTab, actions, instates, reward):
    controllers,conditions,modes=np.shape(QTab)
    alpha=0.01
    QVal=1.0
    
    for i in range(controllers):
        taken=actions[i]
        instate=instates[i]
        QVal=QTab[i,instate,taken]
        QTab[i,instate,taken]=QVal+alpha*(reward-QVal)

#Learns the value of the policy by rewarding each action that lead future states
# which lead to a reward      
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

#Selects a policy by iterating throug the Q-table
def selectPolicy(QTab, FullPolicy):
    tau=0.5
    
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

#Takes the policy, changes the model, runs it, tracks the actions, and gives 
#a utility score for each scenario
def evaluate(FullPolicy,experiment):
    graph=reviseModel(FullPolicy, experiment)
    #importlib.reload(ibfm)
    newexp= ibfm.Experiment(graph)
    newexp.run(1)
    
    scenarios=len(newexp.results)
    actions=[]
    instates=[]
    scores=[]
    probs=[]
    
    nominalstate=newexp.model.nominal_state
    nominalscore=scoreNomstate(nominalstate)
    
    for scenario in range(scenarios):
        actions+=[trackActions(newexp,scenario)]
        instates+=[trackFlows(newexp,scenario)]
        scores+=[scoreScenario(newexp,scenario, nominalstate)]
        
        prob1=list(newexp.scenarios[scenario].values())[0].prob
        nloc=prob1.find('n')
        prob= float(prob1[:nloc]+'-'+prob1[nloc+1:])
        probs=probs+[prob]
        
    probabilities=np.array(probs)
    
    #probability of the nominal state is prod(1-p_e), for e independent events
    nominalprob=np.prod(1-probabilities)
    
    actions+=[trackNomActions(nominalstate)]
    instates+=[trackNomFlows(nominalstate)]
    scores+=[nominalscore]
    probabilities=np.append(probabilities, nominalprob)
    
    designcost=PolicyCost(FullPolicy)
    
    utilityscores=scores*probabilities
    
    return actions, instates, utilityscores, designcost

#Revises the model based on the policy, creating a new graph to be used in ibfm        
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

#Track the actions taken for the nominal state
def trackNomActions(nominal_state):
    #functions of concern--the controlling functions
    functions=['controlG2rate','controlG3press','controlP1effort','controlP1rate']
    mode2actions={'EqualControl': 0, 'IncreaseControl': 1, 'DecreaseControl': 2}
    
    actions=[]
    #find actions taken
    for function in functions:
        mode=str(nominal_state[function])
        actions+=[mode2actions[mode]] 
    return actions

#Track the actions taken (given which scenario it is in a list) for the experiment
def trackActions(exp, scenario):
    #functions of concern--the controlling functions
    functions=['controlG2rate','controlG3press','controlP1effort','controlP1rate']
    mode2actions={'EqualControl': 0, 'IncreaseControl': 1, 'DecreaseControl': 2}
    numstates=len(exp.getResults())
    
    actions=[]
    #find actions taken
    for function in functions:
        mode=str(exp.results[scenario][function])
        actions+=[mode2actions[mode]] 
    return actions

#Track flows going into the functions for the nominal state, as per trackFlows()
def trackNomFlows(nominal_state):
    #flows of concern--inputs to the controllers    
    condition2state={'Negative':0,'Zero': 0,'Low': 0,'High': 1,'Highest': 1,'Nominal': 2}
    
    flowtypesraw=list(nominal_state.keys())
    flowtypes=[str(j) for j in flowtypesraw]
    flowstates=list(nominal_state.values())
    
    flownum=len(flowtypes)
    instates=[]
    
    #find states entered
    for i in range(flownum):
        if flowtypes[i]=='Signal':
            if i%2==0:
                incondition=str(flowstates[i][0])
                instate=condition2state[incondition]
                instates+=[instate]
                
    return instates

#Track flows going into the functions for each scenario 
#(given which scenario it is in a list) for the experiment
#This is used for seeing how an action in one controller changes the state
#for the next controller. However, it may only work if the controllers are 
#oriented in a chain
#NOTE: May ONLY work if only signals are to controllers
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
                instates+=[instate]
                
    return instates

#creates a cost for the design provided it enables certain parts of the policy
def PolicyCost(FullPolicy):
    controllercost=1.0
    increaseratecost=0.5
    increasenomratecost=1.0
    
    ratecontrollers=[0,3]
    controllers=len(FullPolicy)
    
    cost=0.0
    
    for controller in range(controllers):
        #penalty for having a controller at all
        if all(FullPolicy[controller][i]==1 for i in range(len(FullPolicy[controller]))):
            cost+=0.0
        else:
            cost+=controllercost
        #penalties for rate variables
        if controller in ratecontrollers:
            #penalty for increasing rate in nominal state
            if FullPolicy[controller][2]==2:
                cost+=increasenomratecost
            #penalty for increasing rate otherwise
            if any([FullPolicy[controller][0]==2,FullPolicy[controller][1]==2]):
                cost+=increaseratecost    
    return cost

#Score a scenario (given which scenario it is in a list)
def scoreScenario(exp, scenario, Nominalstate):
    time2coeff={'beginning':0.0,'early':0.1,'midway':0.3,'late':0.6,'end':0.9}
    
    nomscore=scoreNomstate(Nominalstate)
    endscore=scoreEndstate(exp, scenario)
    
    
    
    time=list(exp.scenarios[scenario].values())[0].when
    cnom=time2coeff[time]
    cend=1.0-cnom
    
    scenscore=cnom*nomscore+cend*endscore
    
    return scenscore

#Score the nominal state
def scoreNomstate(Nominalstate):
    functions=['exportT1']
    Flow="Thrust"
    
    flowsraw=list(Nominalstate.keys())
    flows=[str(j) for j in flowsraw]
    states=list(Nominalstate.values())
    loc=flows.index(Flow)
    
    effort=int(states[loc][0])
    rate=int(states[loc][1])
    statescore=scoreFlowstate(rate,effort)
    
    return statescore

#Score an endstate for the experiment
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

#Score function for a given flow state.
def scoreFlowstate(rate, effort):
    qualfunc = [[-10.,-10.,-10.,-10.,-10.],
            [-10., -5., -3., -2.0, -10.],
            [-10., -3.,  0., -3., -10.],
            [-10., -2.0, -3., -5.,-10.],
            [-10., -10., -10.,-10.,-10.]]
    
    longbonus=[0.0,1.0,0.0,-1.0,0.0]
    score=qualfunc[effort][rate]+longbonus[rate]
    return score


#Individually scores functions based on their failure impact
def scorefxns(exp):
    
    exp.run(1)
    scenarios=len(exp.results)
    
    functions=[]
    scores=[]
    probs=[]
    
    #initialize dictionary
    functions=exp.model.graph.nodes()
    fxnscores={}
    fxnprobs={}
    failutility={}
    fxncost={}
    
    for fxn in functions:
        fxnscores[fxn]=[]
        fxnprobs[fxn]=[]
        failutility[fxn]=0.0
        try:
            fxncost[fxn]=float(fxn._cost[0])
        except ValueError:
            fxncost[fxn]=0.0
    #map each scenario to its originating function
    for scenario in range(scenarios):
        function=list(exp.scenarios[scenario].keys())[0]
        
        prob=0.01*float(list(exp.scenarios[scenario].values())[0].prob)
        probs+=[prob]
        #remove: simply to make current problem interesting
        score=100*scoreEndstate(exp,scenario)
        scores+=[score]
        
        fxnscores[function]+=[score]
        fxnprobs[function]+=[prob]
        failutility[function]=failutility[function] + score*prob
    #map each function to the utility of making it redundant
    
    
    return functions, fxnscores, fxnprobs, failutility, fxncost

def optRedundancy(functions, fxnscores, fxnprobs, fxncost):
    
    
    fxnreds={}
    
    for function in functions:
        fxnreds[function]=0
    
    ufunc=0.0
    
    for function in functions:
        probs=np.array(fxnprobs[function])
        scores=np.array(fxnscores[function])
        cost=fxncost[function]
        
        ufunc=sum(scores*probs)-cost
        converged=0
        n=0
        print(ufunc)
        while not(converged):
            n+=1
            newufunc=sum(scores*probs**(n+1))-cost*(n+1)
            print(newufunc)
            
            if newufunc >= ufunc:
                ufunc=newufunc
            else:
                converged=1
                
            if n>150:
                break
        
        fxnreds[function]=n
        
    return fxnreds 
                
    

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
#changes modes in graph (but does nothing)
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
                newmodes+=[newmode]
            exp.model.graph.nodes()[funnum].modes=newmodes
        funnum=funnum+1
    return exp
#changes function dictionary (which also does nothing)
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

#Initializes actions to take
def initActions():
    FullPolicy=[[1,2,3],[1,2,3],[1,2,3],[1,2,3]]
    changeFxnfile(FullPolicy)
    e1= ibfm.Experiment('monoprop')
    actionkey=e1.model.graph.nodes()[6].modes
    
    return actionkey 
        

    