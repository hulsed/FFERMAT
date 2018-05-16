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

failcosts=np.array([failcost2, failcost3, failcost4, failcost5])-failcost1
designcosts=np.array([designcost2, designcost3, designcost4, designcost5])-designcost1
designutils=np.array([utility2, utility3, utility4, utility5])-designcost1-failcost1

#noheatsource is 45
width=0.25
variants=np.array([1,2,3,4])
fig, ax = plt.subplots()
p1 = plt.bar(variants, designcosts, width, color='white', edgecolor='blue', hatch='//')
p2 = plt.bar(variants+width ,failcosts, width, color='white', edgecolor='green', hatch='o')
p3 = plt.bar(variants+2*width, designutils, width, color='white', edgecolor='red', hatch='x')

ax.set_title('Differential Design Variant Cost')
ax.set_xticks(variants+width)
ax.set_xticklabels(('Variant 1', 'Variant 2', 'Variant 3', 'Variant 4'))
ax.legend((p1[0], p2[0], p3[0]),(r'$\Delta$' ' Design Cost',r'$\Delta$' ' Failure Cost',r'$\Delta$' ' Total Cost'))
ax.grid(axis='y', which='major')
ax.grid(axis='y', which='minor')
plt.minorticks_on()