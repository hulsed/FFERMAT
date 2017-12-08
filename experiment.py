# -*- coding: utf-8 -*-
"""
Created on Sun Nov 19 18:50:24 2017

@author: hulsed
"""
import ibfmOpt as io
import numpy as np
from matplotlib import pyplot as plt

controllers=4
conditions=3
modes=3
iterations=100
runs=10
    
FullPolicy=io.initFullPolicy(controllers,conditions)
QTab=io.initQTab(controllers, conditions, modes)
rewardhist=np.ones([runs,iterations])

for i in range(runs):
    QTab=io.initQTab(controllers, conditions, modes)
    for j in range(iterations):
        FullPolicy=io.selectPolicy(QTab, FullPolicy)
    
        actions, instates, scores, probs=io.evaluate(FullPolicy)
        totreward=sum(scores)/10
        rewardhist[i,j]=sum(scores)
        
        for k in range(len(scores)):
            action=actions[k]
            instate=instates[k]
            reward=scores[k]
            #note: not sure why individual rewards don't work, but they don't
            #Qtab=io.avlearn(QTab,action,instate,sum(scores))
            #note: probability of the nominal state is prod(1-p_e), for e independent events
        
        QTab=io.avlearnnotracking(QTab, FullPolicy,totreward)
        
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