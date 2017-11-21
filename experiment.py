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
iterations=75
runs=20
    
FullPolicy=io.initFullPolicy(controllers,conditions)
QTab=io.initQTab(controllers, conditions, modes)
rewardhist=np.ones([runs,iterations])

for i in range(runs):
    QTab=io.initQTab(controllers, conditions, modes)
    for j in range(iterations):
        FullPolicy=io.selectPolicy(QTab, FullPolicy)
    
        reward,statescore=io.evaluate(FullPolicy)
        rewardhist[i,j]=reward
    
        QTab=io.avlearn(QTab,FullPolicy,reward)
        
avereward=np.ones(iterations)
stdreward=np.ones(iterations)
    
for k in range(iterations):
    avereward[k]=np.mean(rewardhist[:,k])
    stdreward[k]=np.std(rewardhist[:,k])

x=range(iterations)

plt.errorbar(x,avereward,stdreward, linestyle='None',marker='+')