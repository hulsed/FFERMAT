# -*- coding: utf-8 -*-
"""
Created on Sun Nov 19 18:50:24 2017

@author: hulsed
"""
import ibfmOpt as io
import numpy as np
from matplotlib import pyplot as plt
import ibfm

controllers=4
conditions=3
modes=3
iterations=25
runs=1
    
FullPolicy=io.initFullPolicy(controllers,conditions)
QTab=io.initQTab(controllers, conditions, modes)
rewardhist=np.ones([runs,iterations])
io.createVariants()

initexperiment=ibfm.Experiment('monoprop')

actionkey=io.initActions()

for i in range(runs):
    QTab=io.initQTab(controllers, conditions, modes)
    for j in range(iterations):
        FullPolicy=io.selectPolicy(QTab, FullPolicy)
    
        actions, instates, utilityscores =io.evaluate(FullPolicy,initexperiment)
        utility=sum(utilityscores)
        
        
        rewardhist[i,j]=utility
        
        for k in range(len(utilityscores)):
            action=actions[k]
            instate=instates[k]
            reward=utilityscores[k]
            #note: not sure why individual rewards don't work, but they don't
            Qtab=io.Qlearn(QTab,action,instate,sum(utilityscores))
        
        #QTab=io.avlearnnotracking(QTab, FullPolicy,utility)
        print(utility)
avereward=np.ones(iterations)
stdreward=np.ones(iterations)
maxreward=np.ones(iterations)
minreward=np.ones(iterations)
    
for k in range(iterations):
    avereward[k]=np.mean(rewardhist[:,k])
    stdreward[k]=np.std(rewardhist[:,k])
    maxreward[k]=np.max(rewardhist[:,k])
    minreward[k]=np.min(rewardhist[:,k])

x=range(iterations)

plt.errorbar(x,avereward,stdreward, linestyle='None',marker='+')
plt.title('Convergence of Learner Over Time')
plt.xlabel('Iterations')
plt.ylabel('Score of End-States')
plt.grid()