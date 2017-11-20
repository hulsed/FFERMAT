# -*- coding: utf-8 -*-
"""
Created on Sun Nov 19 18:50:24 2017

@author: hulsed
"""
import ibfmOpt as io

controllers=4
conditions=3
modes=3
    
FullPolicy=io.initFullPolicy(controllers,conditions)
QTab=io.initQTab(controllers, conditions, modes)
rewardhist=[1.,1.,1.,1.,1.,1.,1.,1.,1.,1.]

for j in range(10):
    FullPolicy=io.selectPolicy(QTab, FullPolicy)

    reward=io.evaluate(FullPolicy)
    rewardhist[j]=reward

    QTab=io.avlearn(QTab,FullPolicy,reward)