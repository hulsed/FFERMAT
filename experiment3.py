# -*- coding: utf-8 -*-
"""
Created on Thu Apr 12 14:48:33 2018

@author: hulsed
"""

import ibfmOpt as io
import numpy as np
from matplotlib import pyplot as plt
import ibfm
import importlib

importlib.reload(ibfm)
importlib.reload(io)

e1=ibfm.Experiment('eps_simple')
e1.run(1)

functions, fxnscores, fxnprobs, failutility, fxncost = io.scorefxns(e1)

factor=1000000


fxnreds, newfailutility=io.optRedundancy(functions, fxnscores, fxnprobs, fxncost,factor)

print(fxnreds)

#print failure utility

factor*sum(list(failutility.values()))

#print design costs
print(sum(np.array(list(fxncost.values()))*np.array(list(fxnreds.values()))))

print(sum(list(newfailutility.values())))