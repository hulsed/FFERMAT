# -*- coding: utf-8 -*-
"""
Created on Mon Apr 23 13:50:37 2018

@author: hulsed
"""

import ibfmOpt as io
import numpy as np
from matplotlib import pyplot as plt
import ibfm
import importlib

importlib.reload(ibfm)
importlib.reload(io)

e1=ibfm.Experiment('monoprop')
e1.run(1)

failcost1, designcost1, utility1, scores1 = io.evaluate2(e1)

e2=ibfm.Experiment('monoprop2')
e2.run(1)

failcost2, designcost2, utility2, scores2 = io.evaluate2(e2)

e3=ibfm.Experiment('monoprop3')
e3.run(1)

failcost3, designcost3, utility3, scores3 = io.evaluate2(e3)

e4=ibfm.Experiment('monoprop4')
e4.run(1)

failcost4, designcost4, utility4, scores4 = io.evaluate2(e4)

e5=ibfm.Experiment('monoprop5')
e5.run(1)

failcost5, designcost5, utility5, scores5 = io.evaluate2(e5)

failcosts=[failcost1, failcost2, failcost3, failcost4, failcost5]
designcosts=[designcost1, designcost2, designcost3, designcost4, designcost5]
designutils=[utility1, utility2, utility3, utility4, utility5]

#noheatsource is 45
plt.bar([0,1,2,3,4],designutils)
plt.bar([0,1,2,3,4],failcosts)
plt.bar([0,1,2,3,4],designcosts)