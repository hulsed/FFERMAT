# -*- coding: utf-8 -*-
"""
Created on Fri Feb 15 13:10:03 2019

@author: Daniel Hulse
"""

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

    
#prob_tot=1-np.exp(-l_occ_tot)