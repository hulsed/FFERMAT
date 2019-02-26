# -*- coding: utf-8 -*-
"""
Created on Fri Feb 15 13:10:03 2019

@author: Daniel Hulse
"""

import numpy as np

wear_rate=50.0
rand_rate=25.0

hours=26000


wear_ratehrs=wear_rate/1e6
rand_ratehrs=rand_rate/1e6

hrsperday=3
    
weardayprob=1-np.exp(-wear_ratehrs*hrsperday)
    
eff=0.9
prop=0.5
    
newweardayprob=weardayprob*(1-prop)+prop*(1-eff)*weardayprob
    
weardayrate=-np.log(1-newweardayprob)

wearmonthprob=1-np.exp(-weardayrate*30)


eff2=0.9
prop2=0.8

newwearmonthprob=wearmonthprob*(1-prop2)+prop2*(1-eff2)*wearmonthprob

newwearmonthrate=-np.log(1-newwearmonthprob)

wear5yrprob=1-np.exp(-newwearmonthrate*60)

eff3=0.6
prop3=0.9

newwear5yrprob=wear5yrprob*(1-prop3)+prop3*(1-eff3)*wear5yrprob

newwear5yrrate=1-np.exp(-newwear5yrprob)


lifecyclerate=newwear5yrrate*hours/(3*30*60)

lifecyclerand_rate=rand_ratehrs*hours


total_exp=lifecyclerate+lifecyclerand_rate

total_prob=1-np.exp(-total_exp)

import controlsurfacemodel

[forwardgraph,backgraph,fullgraph]=controlsurfacemodel.initialize()

fxn=forwardgraph.nodes(data='funcobj')['Distribute_EE']

def calcmaint(fxn, mdl):
    
    newrate=0.0
    totcost=0.0
    lifehrs=mdl.lifehours*1.0
    
    faults=fxn.faultmodes
    maint=fxn.maint
    
    faultrates={}
    
    for fault in faults:
        
        ratetype=fxn.faultmodes[fault]['rate']
        newrate=mdl.rates[ratetype]['av']
        faultrates['unmit_rate']=newrate
        
        for strattype in maint:
            strat=maint[strattype]
                    
            sched=mdl.maintenancesched[strat['sched']]['av']
            
            eff=strat['eff'][fault]
            
            oldprob=1-np.exp(-sched*newrate)
            newprob=oldprob*eff
            newrate=-np.log(1-newprob)/sched
        
        faultrates['mit_rate']=newrate
        faultrates['mit_prob']=1-np.exp(-lifehrs*newrate)
        faultrates['life_exp']=lifehrs*newrate    
    
    for strattype in maint:
        strat=maint[strattype]
        
        cost=mdl.maintenancecosts[strat['type']]['av']
        sched=mdl.maintenancesched[strat['sched']]['av']
        lifecost=cost*lifehrs/sched
        totcost+=lifecost
    
    maintcost=totcost
    
    return faultrates, maintcost
    
    
    