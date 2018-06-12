# -*- coding: utf-8 -*-
"""
Created on Fri Jan 12 12:25:17 2018

@author: hulsed
"""

import ibfmOpt as io
import numpy as np
from matplotlib import pyplot as plt
import ibfm

controllers=4
conditions=3
modes=3
iterations=10
runs=1
pop=30
generations=30
    

io.createVariants()
initexperiment=ibfm.Experiment('monoprop')

maxfitness, bestsol, fithist=io.EA(pop,generations, controllers, conditions, initexperiment)

plothist=fithist-fithist[0]

plt.plot(plothist)
plt.title('Cost Improvement over Baseline from Optimization')
plt.xlabel('Generations (of population 30)')
plt.ylabel('Cost Score Inprovement')
